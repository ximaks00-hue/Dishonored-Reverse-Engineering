import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;

/** Args: output-path address...; read-only batch decompilation of indexed addresses. */
public class DecompileAddressBatch extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 2) {
            throw new IllegalArgumentException("Pass output path and one or more function addresses");
        }
        File out = new File(args[0]);
        File parent = out.getParentFile();
        if (parent != null && !parent.exists()) {
            parent.mkdirs();
        }

        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        try (BufferedWriter writer = new BufferedWriter(
                new OutputStreamWriter(new FileOutputStream(out), StandardCharsets.UTF_8))) {
            for (int i = 1; i < args.length && !monitor.isCancelled(); i++) {
                String raw = args[i].replaceFirst("^(0x|0X)", "");
                Address address = toAddr(Long.parseUnsignedLong(raw, 16));
                Function function = currentProgram.getFunctionManager().getFunctionAt(address);
                writer.write("@@@ " + address + " " + (function == null ? "<missing>" : function.getName()) + " @@@\n");
                if (function == null) {
                    writer.write("NO_FUNCTION\n");
                    continue;
                }
                DecompileResults results = decompiler.decompileFunction(function, 120, monitor);
                if (!results.decompileCompleted()) {
                    writer.write("DECOMPILE_FAILED=" + results.getErrorMessage() + "\n");
                    continue;
                }
                writer.write(results.getDecompiledFunction().getC());
                writer.write("\n");
                println("DECOMPILED=" + address + " NAME=" + function.getName());
            }
        } finally {
            decompiler.dispose();
        }
        println("OUTPUT=" + out.getAbsolutePath());
    }
}
