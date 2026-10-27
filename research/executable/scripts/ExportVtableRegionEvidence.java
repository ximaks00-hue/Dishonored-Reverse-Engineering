import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolTable;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;

/**
 * Read-only export of labels, DWORD targets, and xrefs for a candidate vtable region.
 *
 * Usage: -postScript ExportVtableRegionEvidence.java <start-VA> <end-VA> <output.csv>
 */
public class ExportVtableRegionEvidence extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 3) {
            throw new IllegalArgumentException("Pass start VA, end VA, and output CSV path");
        }
        Address start = toAddr(args[0]);
        Address end = toAddr(args[1]);
        File out = new File(args[2]);
        File parent = out.getParentFile();
        if (parent != null && !parent.exists()) parent.mkdirs();

        Listing listing = currentProgram.getListing();
        SymbolTable symbols = currentProgram.getSymbolTable();
        try (BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(
                new FileOutputStream(out), StandardCharsets.UTF_8))) {
            writer.write("address,dword,symbol,target_function,reference_count,reference_sources\n");
            for (Address at = start; at.compareTo(end) <= 0; at = at.add(4)) {
                if (monitor.isCancelled()) break;
                int value;
                try {
                    value = getInt(at);
                } catch (Exception e) {
                    continue;
                }
                Address target = toAddr(Integer.toUnsignedLong(value));
                Symbol sym = symbols.getPrimarySymbol(at);
                Function function = listing.getFunctionAt(target);
                ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(at);
                StringBuilder sources = new StringBuilder();
                int count = 0;
                while (refs.hasNext()) {
                    Reference ref = refs.next();
                    if (count++ < 20) {
                        if (sources.length() > 0) sources.append(';');
                        sources.append(ref.getFromAddress());
                    }
                }
                writer.write(csv(at.toString()) + "," + String.format("0x%08X", value) + ","
                        + csv(sym == null ? "" : sym.getName()) + ","
                        + csv(function == null ? "" : function.getName()) + "," + count + ","
                        + csv(sources.toString()) + "\n");
            }
        }
        println("ExportVtableRegionEvidence wrote region " + start + ".." + end
                + " to " + out.getAbsolutePath());
    }

    private static String csv(String value) {
        if (value == null) return "";
        String escaped = value.replace("\"", "\"\"");
        if (escaped.indexOf(',') >= 0 || escaped.indexOf('"') >= 0 || escaped.indexOf('\n') >= 0) {
            return "\"" + escaped + "\"";
        }
        return escaped;
    }
}
