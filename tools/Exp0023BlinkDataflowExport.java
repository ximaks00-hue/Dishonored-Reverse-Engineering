// EXP-0023: read-only x86 Blink dataflow observation exporter.
// @category Dishonored
// Args: <new-absolute-output.tsv>. Do NOT run on an unverified build.
// High p-code reports are optimized representations, NOT proof of pawn movement.
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.listing.Function;
import ghidra.program.model.pcode.HighFunction;
import ghidra.program.model.pcode.PcodeOp;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import java.io.File;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.Iterator;

public class Exp0023BlinkDataflowExport extends GhidraScript {
  private static final String SHA =
      "66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E";
  private static final long[] TARGETS = {
      0x00BFC5D0L, 0x00BFC160L, 0x00BFBC90L, 0x00BF9AB0L,
      0x00AB4680L, 0x00BCD800L, 0x00414DC0L
  };
  private String clean(Object x) {
    return (x == null ? "" : x.toString()).replace('\t',' ').replace('\r',' ').replace('\n',' ');
  }
  private String hex(long v) { return String.format("0x%08X",v); }
  private void line(PrintWriter out,String fn,String kind,String at,String opcode,String detail) {
    out.println(fn+"\t"+kind+"\t"+at+"\t"+opcode+"\t"+clean(detail));
  }
  private boolean include(int o) {
    return o==PcodeOp.CALL || o==PcodeOp.CALLIND || o==PcodeOp.STORE ||
       o==PcodeOp.LOAD || o==PcodeOp.RETURN || o==PcodeOp.PTRADD ||
       o==PcodeOp.PTRSUB || o==PcodeOp.INT_ADD || o==PcodeOp.INT_MULT ||
       o==PcodeOp.CBRANCH;
  }
  @Override
  protected void run() throws Exception {
    String[] args=getScriptArgs();
    if(args.length!=1) throw new IllegalArgumentException("Need one NEW output TSV path");
    File output=new File(args[0]);
    if(output.exists()) throw new IllegalStateException("Refusing overwrite");
    if(currentProgram.getDefaultPointerSize()!=4 ||
       currentProgram.getImageBase().getOffset()!=0x400000L)
      throw new IllegalStateException("Unexpected architecture or image base");
    String programSha=currentProgram.getExecutableSHA256();
    if(programSha==null || !SHA.equalsIgnoreCase(programSha))
      throw new IllegalStateException("Ghidra imported executable SHA mismatch: "+programSha);
    DecompInterface d=new DecompInterface();
    if(!d.openProgram(currentProgram)) throw new IllegalStateException("Decompiler open failed");
    try(PrintWriter out=new PrintWriter(Files.newBufferedWriter(output.toPath(),StandardCharsets.UTF_8))) {
      out.println("# SHA256="+programSha+"\tImageBase="+hex(0x400000L));
      out.println("function_va\tevidence_kind\tsite_va\topcode\toperand_or_reference");
      for(long va:TARGETS) {
        monitor.checkCancelled();
        String name=hex(va);
        Function fn=currentProgram.getFunctionManager().getFunctionAt(toAddr(va));
        if(fn==null){
          line(out,name,"NOT_A_FUNCTION_ENTRY",name,"","Inspect entry/mid-function manually");
          continue;
        }
        line(out,name,"FUNCTION",name,"",fn.getName()+"; thunk="+fn.isThunk()+
            "; calling_convention="+fn.getCallingConventionName());
        ReferenceIterator refs=currentProgram.getReferenceManager().getReferencesTo(fn.getEntryPoint());
        while(refs.hasNext()){
          Reference r=refs.next();
          line(out,name,"XREF",r.getFromAddress().toString(),
              r.getReferenceType().toString(),"source="+r.getFromAddress().toString());
        }
        DecompileResults result=d.decompileFunction(fn,60,monitor);
        if(result==null||!result.decompileCompleted()||result.getHighFunction()==null){
          line(out,name,"DECOMPILATION_FAILED",name,"",
               result==null?"null result":result.getErrorMessage());
          continue;
        }
        HighFunction high=result.getHighFunction();
        Iterator<?> ops=high.getPcodeOps();
        int observed=0;
        while(ops.hasNext()){
          monitor.checkCancelled();
          PcodeOp op=(PcodeOp)ops.next();
          if(!include(op.getOpcode())) continue;
          String site=op.getSeqnum().getTarget().toString();
          StringBuilder argsView=new StringBuilder();
          for(int i=0;i<op.getNumInputs();i++){
            if(i>0)argsView.append("; ");
            argsView.append("in").append(i).append("=").append(clean(op.getInput(i)));
          }
          if(op.getOutput()!=null)argsView.append("; out=").append(clean(op.getOutput()));
          line(out,name,"HIGH_PCODE",site,op.getMnemonic(),argsView.toString());
          if(++observed>=3500){
            line(out,name,"TRUNCATED",name,"","Event cap 3500; do not infer absence");
            break;
          }
        }
        line(out,name,"COMPLETE_FUNCTION",name,"","events="+observed);
      }
    } finally {
      d.dispose();
    }
    println("EXP-0023 completed: only structural p-code observations exported.");
  }
}
