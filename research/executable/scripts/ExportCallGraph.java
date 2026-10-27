import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.symbol.RefType;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;

/**
 * Read-only export of direct call edges and data xrefs for the Dishonored offline callgraph.
 *
 * Usage (analyzeHeadless, -readOnly):
 *   -postScript ExportCallGraph.java <output.csv>
 *
 * CSV columns:
 *   kind,from_addr,from_name,to_addr,to_name,site_addr
 */
public class ExportCallGraph extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            throw new IllegalArgumentException("Pass one output CSV path");
        }
        File out = new File(args[0]);
        File parent = out.getParentFile();
        if (parent != null && !parent.exists()) {
            parent.mkdirs();
        }

        ReferenceManager refs = currentProgram.getReferenceManager();
        int edgeCount = 0;
        try (BufferedWriter writer = new BufferedWriter(
                new OutputStreamWriter(new FileOutputStream(out), StandardCharsets.UTF_8))) {
            writer.write("kind,from_addr,from_name,to_addr,to_name,site_addr\n");

            FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
            while (functions.hasNext() && !monitor.isCancelled()) {
                Function function = functions.next();
                Address entry = function.getEntryPoint();
                String fromAddr = entry.toString();
                String fromName = csv(function.getName());

                Instruction instr = getInstructionAt(entry);
                while (instr != null && !monitor.isCancelled()) {
                    Address site = instr.getAddress();
                    Reference[] flows = instr.getReferencesFrom();
                    if (flows != null) {
                        for (Reference ref : flows) {
                            RefType type = ref.getReferenceType();
                            if (type == null || !type.isCall()) {
                                continue;
                            }
                            Address to = ref.getToAddress();
                            Function target = getFunctionAt(to);
                            if (target == null) {
                                target = getFunctionContaining(to);
                            }
                            String toAddr = to.toString();
                            String toName = target != null ? csv(target.getName()) : "";
                            writer.write("call," + fromAddr + "," + fromName + "," + toAddr + ","
                                    + toName + "," + site.toString() + "\n");
                            edgeCount++;
                        }
                    }
                    instr = instr.getNext();
                    if (instr != null && !function.getBody().contains(instr.getAddress())) {
                        break;
                    }
                }

                // Data xrefs *to* this function entry (imports, vtables, etc.).
                ReferenceIterator incoming = refs.getReferencesTo(entry);
                while (incoming.hasNext() && !monitor.isCancelled()) {
                    Reference ref = incoming.next();
                    RefType type = ref.getReferenceType();
                    if (type != null && type.isCall()) {
                        continue; // already captured as call from caller body
                    }
                    Address fromSite = ref.getFromAddress();
                    Function caller = getFunctionContaining(fromSite);
                    String callerAddr = caller != null ? caller.getEntryPoint().toString()
                            : fromSite.toString();
                    String callerName = caller != null ? csv(caller.getName()) : "";
                    writer.write("data," + callerAddr + "," + callerName + "," + fromAddr + ","
                            + fromName + "," + fromSite.toString() + "\n");
                    edgeCount++;
                }
            }
        }
        println("ExportCallGraph wrote " + edgeCount + " edges to " + out.getAbsolutePath());
    }

    private static String csv(String value) {
        if (value == null) {
            return "";
        }
        String escaped = value.replace("\"", "\"\"");
        if (escaped.indexOf(',') >= 0 || escaped.indexOf('"') >= 0 || escaped.indexOf('\n') >= 0) {
            return "\"" + escaped + "\"";
        }
        return escaped;
    }
}
