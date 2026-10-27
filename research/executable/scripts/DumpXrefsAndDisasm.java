import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;

/** Args: address [instruction-count] */
public class DumpXrefsAndDisasm extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 1) {
            throw new IllegalArgumentException("Pass address");
        }
        Address addr = toAddr(Long.parseUnsignedLong(args[0].replaceFirst("^(0x|0X)", ""), 16));
        int count = args.length >= 2 ? Integer.parseInt(args[1]) : 40;
        Function fn = getFunctionContaining(addr);
        println("ADDR=" + addr);
        println("FUNC=" + (fn == null ? "none" : fn.getName() + "@" + fn.getEntryPoint()
                + ".." + fn.getBody().getMaxAddress()));
        ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(addr);
        int n = 0;
        while (refs.hasNext() && n++ < 50) {
            Reference ref = refs.next();
            Function caller = getFunctionContaining(ref.getFromAddress());
            println("XREF=" + ref.getFromAddress() + " "
                    + (caller == null ? "?" : caller.getName()) + " "
                    + ref.getReferenceType());
        }
        Instruction instr = getInstructionAt(fn != null ? fn.getEntryPoint() : addr);
        int i = 0;
        while (instr != null && i++ < count) {
            println("INSN=" + instr.getAddress() + " " + instr);
            instr = instr.getNext();
        }
    }
}
