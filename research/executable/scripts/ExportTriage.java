// Read-only summary script for the saved Dishonored Ghidra project.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import java.io.File;
import java.io.PrintWriter;

public class ExportTriage extends GhidraScript {
    @Override
    public void run() throws Exception {
        int functions = 0;
        File csv = new File("E:/Dishonored REVERS/research/executable/functions.csv");
        try (PrintWriter writer = new PrintWriter(csv, "UTF-8")) {
            writer.println("address,name,signature,size,body_start,body_end");
        FunctionIterator iterator = currentProgram.getFunctionManager().getFunctions(true);
        while (iterator.hasNext()) {
            Function function = iterator.next();
            functions++;
                writer.printf("\"%s\",\"%s\",\"%s\",%d,\"%s\",\"%s\"%n",
                    function.getEntryPoint(),
                    function.getName().replace("\"", "\"\""),
                    function.getSignature().getPrototypeString().replace("\"", "\"\""),
                    function.getBody().getNumAddresses(),
                    function.getBody().getMinAddress(),
                    function.getBody().getMaxAddress());
            }
        }
        println("PROGRAM=" + currentProgram.getName());
        println("LANGUAGE=" + currentProgram.getLanguageID());
        println("IMAGE_BASE=" + currentProgram.getImageBase());
        println("FUNCTION_COUNT=" + functions);
        println("SYMBOL_COUNT=" + currentProgram.getSymbolTable().getNumSymbols());
        println("MEMORY_BLOCK_COUNT=" + currentProgram.getMemory().getBlocks().length);
    }
}
