import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.listing.FunctionManager;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.TreeMap;

/** Read-only function inventory and external-function audit. */
public class ExportFunctionCountAudit extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) throw new IllegalArgumentException("Pass output CSV path");
        File out = new File(args[0]);
        File parent = out.getParentFile();
        if (parent != null && !parent.exists()) parent.mkdirs();

        FunctionManager manager = currentProgram.getFunctionManager();
        Map<String, Boolean> functions = new TreeMap<>();
        FunctionIterator all = manager.getFunctions(true);
        while (all.hasNext() && !monitor.isCancelled()) {
            Function function = all.next();
            functions.put(function.getEntryPoint().toString(), function.isExternal());
        }
        FunctionIterator external = manager.getExternalFunctions();
        while (external.hasNext() && !monitor.isCancelled()) {
            Function function = external.next();
            functions.put(function.getEntryPoint().toString(), true);
        }

        long internal = 0;
        long externalCount = 0;
        try (BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(
                new FileOutputStream(out), StandardCharsets.UTF_8))) {
            writer.write("address,external,name\n");
            for (Map.Entry<String, Boolean> entry : functions.entrySet()) {
                Address address = toAddr(entry.getKey());
                Function function = manager.getFunctionAt(address);
                boolean isExternal = entry.getValue() || (function != null && function.isExternal());
                if (isExternal) externalCount++;
                else internal++;
                writer.write(entry.getKey() + "," + isExternal + ","
                        + (function == null ? "" : csv(function.getName())) + "\n");
            }
        }
        println("FunctionCountAudit API getFunctionCount=" + manager.getFunctionCount()
                + " uniqueExported=" + functions.size()
                + " internal=" + internal + " external=" + externalCount
                + " output=" + out.getAbsolutePath());
    }

    private static String csv(String value) {
        if (value == null) return "";
        String escaped = value.replace("\"", "\"\"");
        return escaped.indexOf(',') >= 0 || escaped.indexOf('"') >= 0
                ? "\"" + escaped + "\"" : escaped;
    }
}
