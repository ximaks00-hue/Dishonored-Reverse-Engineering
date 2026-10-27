// EXP-0018: distinguish Ghidra nonexternal/external counts, read-only.
// @category Dishonored
// One script argument: new output TSV filename.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.FunctionIterator;
import java.io.File;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
public class Exp0018FunctionCountAudit extends GhidraScript {
  @Override protected void run() throws Exception {
    String[] args=getScriptArgs();
    if(args.length!=1)throw new IllegalArgumentException("Need new output TSV filename");
    File output=new File(args[0]);
    if(output.exists())throw new IllegalStateException("Refusing overwrite");
    FunctionManager fm=currentProgram.getFunctionManager();
    int all=fm.getFunctionCount(),internal=0,external=0,noStubs=0;
    FunctionIterator it=fm.getFunctions(true);
    while(it.hasNext()){monitor.checkCancelled();it.next();internal++;}
    it=fm.getExternalFunctions();
    while(it.hasNext()){monitor.checkCancelled();it.next();external++;}
    it=fm.getFunctionsNoStubs(true);
    while(it.hasNext()){monitor.checkCancelled();it.next();noStubs++;}
    String sha=currentProgram.getExecutableSHA256();
    try(PrintWriter out=new PrintWriter(Files.newBufferedWriter(output.toPath(),StandardCharsets.UTF_8))){
      out.println("metric\tvalue");
      out.println("image_base\t"+currentProgram.getImageBase());
      out.println("executable_sha256\t"+(sha==null?"UNKNOWN":sha));
      out.println("functions_including_external\t"+all);
      out.println("functions_non_external_iterator\t"+internal);
      out.println("functions_external_iterator\t"+external);
      out.println("functions_non_external_no_stubs\t"+noStubs);
      out.println("internal_plus_external_consistent\t"+(all==internal+external));
      out.println("external_matches_reported_gap_488\t"+(external==488));
    }
    println("Ghidra functions: total="+all+", internal="+internal+", external="+external+", real="+noStubs);
  }
}
