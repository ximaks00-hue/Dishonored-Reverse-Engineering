import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.symbol.RefType;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolTable;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;

/**
 * Read-only provenance dump for Blink candidate producer/consumer identity (EXP-0042).
 *
 * Usage:
 *   -postScript ExportCandidateOwnerEvidence.java <output.csv>
 */
public class ExportCandidateOwnerEvidence extends GhidraScript {
    private static final String[] FUNCS = {
            "0x00BFAE60", "0x00BFAFD0", "0x00BF8C00", "0x00BFC990",
            "0x00BFE3C0", "0x00BF8DD0", "0x00BE7580", "0x00CF34E0",
            "0x00BF9A10", "0x00BF8A20"
    };

    private static final String[] SLOT_DWARDS = {
            "0x01168458", // FUN_00BFAE60 data entry (EXP-0039)
            "0x01168408", // FUN_00BFE3C0
            "0x011685EC", // FUN_00BF8DD0
            "0x01168698", // Blink vtable start
            "0x01168844", // Blink +0x1AC -> FUN_00BFC990 (0x1AC=428=0x1AC)
            "0x01167F60"  // ActivePower base candidate
    };

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
        SymbolTable symbols = currentProgram.getSymbolTable();

        try (BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(
                new FileOutputStream(out), StandardCharsets.UTF_8))) {
            writer.write("kind,subject,from_addr,from_func,to_addr,to_func,ref_type,detail\n");

            for (String raw : FUNCS) {
                Address addr = toAddr(Long.parseUnsignedLong(raw.substring(2), 16));
                Function fn = getFunctionAt(addr);
                String fname = fn != null ? fn.getName() : raw;

                // Incoming xrefs to function entry.
                ReferenceIterator incoming = refs.getReferencesTo(addr);
                int n = 0;
                while (incoming.hasNext() && n < 80) {
                    Reference ref = incoming.next();
                    Address from = ref.getFromAddress();
                    Function caller = getFunctionContaining(from);
                    writer.write(csv("xref_to_func") + "," + csv(fname) + ","
                            + csv(from.toString()) + ","
                            + csv(caller == null ? "" : caller.getName()) + ","
                            + csv(addr.toString()) + "," + csv(fname) + ","
                            + csv(String.valueOf(ref.getReferenceType())) + ","
                            + csv("") + "\n");
                    n++;
                }

                // Outgoing call-like refs from body (sample).
                if (fn != null) {
                    Instruction instr = getInstructionAt(fn.getEntryPoint());
                    int outs = 0;
                    while (instr != null && outs < 60 && !monitor.isCancelled()) {
                        if (!fn.getBody().contains(instr.getAddress())) {
                            break;
                        }
                        Reference[] fromRefs = instr.getReferencesFrom();
                        if (fromRefs != null) {
                            for (Reference ref : fromRefs) {
                                RefType type = ref.getReferenceType();
                                if (type == null || !(type.isCall() || type.isJump())) {
                                    continue;
                                }
                                Address to = ref.getToAddress();
                                Function target = getFunctionAt(to);
                                if (target == null) {
                                    target = getFunctionContaining(to);
                                }
                                writer.write(csv("call_from_func") + "," + csv(fname) + ","
                                        + csv(instr.getAddress().toString()) + ","
                                        + csv(fname) + ","
                                        + csv(to.toString()) + ","
                                        + csv(target == null ? "" : target.getName()) + ","
                                        + csv(String.valueOf(type)) + ","
                                        + csv("") + "\n");
                                outs++;
                            }
                        }
                        instr = instr.getNext();
                    }
                }
            }

            for (String raw : SLOT_DWARDS) {
                Address addr = toAddr(Long.parseUnsignedLong(raw.substring(2), 16));
                Symbol sym = symbols.getPrimarySymbol(addr);
                int value = 0;
                try {
                    value = getInt(addr);
                } catch (Exception ignored) {
                }
                Address target = toAddr(Integer.toUnsignedLong(value));
                Function tfn = getFunctionAt(target);
                ReferenceIterator incoming = refs.getReferencesTo(addr);
                int n = 0;
                StringBuilder sources = new StringBuilder();
                while (incoming.hasNext() && n < 40) {
                    Reference ref = incoming.next();
                    Address from = ref.getFromAddress();
                    Function caller = getFunctionContaining(from);
                    if (sources.length() > 0) {
                        sources.append(';');
                    }
                    sources.append(from).append('@')
                            .append(caller == null ? "?" : caller.getName());
                    writer.write(csv("xref_to_slot") + "," + csv(raw) + ","
                            + csv(from.toString()) + ","
                            + csv(caller == null ? "" : caller.getName()) + ","
                            + csv(addr.toString()) + ","
                            + csv(tfn == null ? "" : tfn.getName()) + ","
                            + csv(String.valueOf(ref.getReferenceType())) + ","
                            + csv(sym == null ? "" : sym.getName()) + "\n");
                    n++;
                }
                if (n == 0) {
                    writer.write(csv("xref_to_slot") + "," + csv(raw) + ",,,,,"
                            + csv(addr.toString()) + ","
                            + csv(tfn == null ? "" : tfn.getName()) + ",NONE,"
                            + csv((sym == null ? "" : sym.getName())
                                    + ";dword=" + String.format("0x%08X", value)
                                    + ";sources=" + sources) + "\n");
                }
            }
        }
        println("ExportCandidateOwnerEvidence wrote " + out.getAbsolutePath());
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
