import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;

/**
 * Decompile + print a few instructions around a call target.
 * Args: <function-va> [call-site-va]
 */
public class DecompileFunctionVerbose extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 1) {
            throw new IllegalArgumentException("Pass function VA and optional call-site VA");
        }
        Address address = toAddr(Long.parseUnsignedLong(args[0].replaceFirst("^(0x|0X)", ""), 16));
        Function function = getFunctionAt(address);
        if (function == null) {
            function = getFunctionContaining(address);
        }
        if (function == null) {
            throw new IllegalArgumentException("No function at " + address);
        }
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        DecompileResults results = decompiler.decompileFunction(function, 90, monitor);
        println("ADDRESS=" + function.getEntryPoint());
        println("NAME=" + function.getName());
        if (results.decompileCompleted()) {
            println(results.getDecompiledFunction().getC());
        } else {
            println("DECOMPILE_FAILED=" + results.getErrorMessage());
        }
        if (args.length >= 2) {
            Address site = toAddr(Long.parseUnsignedLong(args[1].replaceFirst("^(0x|0X)", ""), 16));
            println("SITE=" + site);
            Instruction instr = getInstructionAt(site);
            for (int i = 0; i < 12 && instr != null; i++) {
                println("INSN=" + instr.getAddress() + " " + instr);
                instr = instr.getPrevious();
            }
        }
        decompiler.dispose();
    }
}
