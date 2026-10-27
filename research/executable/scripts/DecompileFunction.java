import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;

public class DecompileFunction extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            throw new IllegalArgumentException("Pass one function entry address in hex");
        }
        String raw = args[0].replaceFirst("^(0x|0X)", "");
        Address address = toAddr(Long.parseUnsignedLong(raw, 16));
        Function function = currentProgram.getFunctionManager().getFunctionAt(address);
        if (function == null) {
            throw new IllegalArgumentException("No function at " + address);
        }
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        DecompileResults results = decompiler.decompileFunction(function, 60, monitor);
        if (!results.decompileCompleted()) {
            throw new RuntimeException("Decompilation failed: " + results.getErrorMessage());
        }
        println("ADDRESS=" + function.getEntryPoint());
        println("NAME=" + function.getName());
        println("SIGNATURE=" + function.getSignature().getPrototypeString());
        println(results.getDecompiledFunction().getC());
        decompiler.dispose();
    }
}
