// EXP-0015: read-only candidate search for x86 Dishonored vtables.
// @category Dishonored
// Requires one argument: new absolute output CSV path.
// Candidate matches are NOT class attributions.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;
import java.io.File;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;

public class Exp0015VtableCandidateExport extends GhidraScript {
    private static final int[] CTRL = {0,4,8,0x4F8,0x4FC,0x500,0x504,0x508,0x50C,0x510,0x514,0x518,0x55C,0x560,0x564};
    private static final int[] WHEEL = {0,4,8,0x1EC,0x1F0,0x1F4};
    private Memory m;
    private ReferenceManager r;
    private long imageBase;

    private boolean codePointer(long va, int off) {
        try {
            long dest = m.getInt(toAddr(va + off), false) & 0xffffffffL;
            MemoryBlock block = m.getBlock(toAddr(dest));
            return block != null && block.isExecute();
        } catch (Exception e) {
            return false;
        }
    }
    private boolean matches(long va, int[] offsets) {
        for (int offset : offsets) if (!codePointer(va, offset)) return false;
        return true;
    }
    private String evidence(long va) {
        StringBuilder sb = new StringBuilder();
        ReferenceIterator iter = r.getReferencesTo(toAddr(va));
        while (iter.hasNext()) {
            Reference ref = iter.next();
            MemoryBlock src = m.getBlock(ref.getFromAddress());
            if (src == null || !src.isExecute()) continue;
            if (sb.length() > 0) sb.append(';');
            if (sb.length() < 512) sb.append(ref.getFromAddress().toString());
        }
        return sb.toString();
    }
    private void emit(PrintWriter out, String kind, long va, String xrefs, int[] offsets) throws Exception {
        for (int offset : offsets) {
            long ptr = m.getInt(toAddr(va + offset), false) & 0xffffffffL;
            Function fn = currentProgram.getFunctionManager().getFunctionContaining(toAddr(ptr));
            String name = fn == null ? "UNKNOWN" : fn.getName().replace(',', '_');
            out.printf("%s,0x%08X,0x%08X,%s,0x%03X,0x%08X,0x%08X,%s%n",
                kind, va, va - imageBase, xrefs, offset, ptr, ptr - imageBase, name);
        }
    }
    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            println("Provide exactly one NEW absolute output CSV filename");
            return;
        }
        if (currentProgram.getDefaultPointerSize() != 4) throw new IllegalStateException("x86 only");
        imageBase = currentProgram.getImageBase().getOffset();
        if (imageBase != 0x400000) throw new IllegalStateException("Unexpected image base");
        File dest = new File(args[0]);
        if (dest.exists()) throw new IllegalStateException("Refusing overwrite of " + dest);
        m = currentProgram.getMemory();
        r = currentProgram.getReferenceManager();
        int tables = 0;
        try (PrintWriter out = new PrintWriter(dest, StandardCharsets.UTF_8.name())) {
            out.println("candidate_kind,table_va,table_rva,code_xref_sources,byte_offset,target_va,target_rva,ghidra_function");
            outer: for (MemoryBlock block : m.getBlocks()) {
                if (block.isExecute() || !block.isInitialized() || !block.isLoaded()) continue;
                long first = (block.getStart().getOffset() + 3L) & ~3L;
                long last = block.getEnd().getOffset() - 0x567L;
                for (long va = first; va <= last; va += 4) {
                    if ((va & 0x3FFF) == 0) monitor.checkCancelled();
                    if (!codePointer(va, 0) || !codePointer(va, 4) || !codePointer(va, 8)) continue;
                    boolean a = matches(va, CTRL), b = matches(va, WHEEL);
                    if (!a && !b) continue;
                    String x = evidence(va);
                    if (x.isEmpty()) continue;
                    if (a) emit(out, "controller-shaped", va, x, CTRL);
                    if (b) emit(out, "wheel-shaped", va, x, WHEEL);
                    if (++tables >= 3000) {
                        println("Output capped at 3000 candidate bases; incomplete scan");
                        break outer;
                    }
                }
            }
        }
        println("Exported " + tables + " tentative candidate table bases. No ownership assigned.");
    }
}
