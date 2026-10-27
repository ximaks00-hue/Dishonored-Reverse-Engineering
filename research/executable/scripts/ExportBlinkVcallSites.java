import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Pattern;

/**
 * Read-only scan for indirect CALL instructions that reference a requested
 * x86 vtable-slot displacement (or load it immediately before the call).
 * This exports candidates only; it does not infer the receiver's class.
 *
 * Usage: -postScript ExportBlinkVcallSites.java <slot-hex> <output.csv>
 */
public class ExportBlinkVcallSites extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 2) {
            throw new IllegalArgumentException("Pass slot hex and output CSV path");
        }
        String slot = args[0].replace("0x", "").replace("0X", "").trim();
        if (slot.isEmpty() || !slot.matches("[0-9a-fA-F]+")) {
            throw new IllegalArgumentException("Slot must be a hexadecimal displacement");
        }
        Pattern literal = Pattern.compile("(?i)\\b0x0*" + Pattern.quote(slot) + "\\b");
        File out = new File(args[1]);
        File parent = out.getParentFile();
        if (parent != null && !parent.exists()) {
            parent.mkdirs();
        }

        int rows = 0;
        try (BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(
                new FileOutputStream(out), StandardCharsets.UTF_8))) {
            writer.write("slot,function_addr,function_name,call_addr,call_text,match_addr,match_text,prev1,prev2\n");
            FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
            while (functions.hasNext() && !monitor.isCancelled()) {
                Function function = functions.next();
                List<Instruction> previous = new ArrayList<>();
                InstructionIterator instructions = currentProgram.getListing()
                        .getInstructions(function.getBody(), true);
                while (instructions.hasNext() && !monitor.isCancelled()) {
                    Instruction instruction = instructions.next();
                    if ("CALL".equalsIgnoreCase(instruction.getMnemonicString())) {
                        Instruction match = hasSlot(instruction, literal) ? instruction : null;
                        if (match == null) {
                            for (int i = previous.size() - 1; i >= 0; i--) {
                                Instruction candidate = previous.get(i);
                                if (hasSlot(candidate, literal)) {
                                    match = candidate;
                                    break;
                                }
                            }
                        }
                        if (match != null) {
                            Address entry = function.getEntryPoint();
                            writer.write(csv(slot.toUpperCase()) + "," + csv(entry.toString()) + ","
                                    + csv(function.getName()) + "," + csv(instruction.getAddress().toString()) + ","
                                    + csv(instruction.toString()) + "," + csv(match.getAddress().toString()) + ","
                                    + csv(match.toString()) + ","
                                    + csv(previous.size() >= 1 ? previous.get(previous.size() - 1).toString() : "") + ","
                                    + csv(previous.size() >= 2 ? previous.get(previous.size() - 2).toString() : "")
                                    + "\n");
                            rows++;
                        }
                    }
                    previous.add(instruction);
                    if (previous.size() > 3) {
                        previous.remove(0);
                    }
                }
            }
        }
        println("ExportBlinkVcallSites wrote " + rows + " candidate calls for slot 0x"
                + slot.toUpperCase() + " to " + out.getAbsolutePath());
    }

    private static boolean hasSlot(Instruction instruction, Pattern literal) {
        return literal.matcher(instruction.toString()).find();
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
