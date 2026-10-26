// EXP-0018 read-only Ghidra script; run only after verifying EXE SHA.
// @category Dishonored
// Args: <input_vtable_base_addresses.txt> <new_output.tsv>
// Input one 0x-prefixed table VA per line; # comments allowed.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import java.io.File;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.LinkedHashSet;

public class Exp0018CandidateEvidenceExport extends GhidraScript {
  private static final int[] OFFSETS={0,4,8,0x1EC,0x1F0,0x1F4,0x4F8,0x4FC,0x500,
      0x504,0x508,0x50C,0x510,0x514,0x518,0x55C,0x560,0x564};
  private String hex(long n){return String.format("0x%08X",n);}
  private String safe(String s){return s==null?"":s.replace('\t',' ').replace('\n',' ');}
  private String dword(Memory m,long va){
    try{return hex(m.getInt(toAddr(va),false)&0xffffffffL);}
    catch(Exception e){return "UNREADABLE";}
  }
  @Override protected void run() throws Exception {
    String[] args=getScriptArgs();
    if(args.length!=2)throw new IllegalArgumentException("Need input.txt and new output.tsv");
    if(currentProgram.getDefaultPointerSize()!=4||currentProgram.getImageBase().getOffset()!=0x400000L)
      throw new IllegalStateException("Requires 32-bit program at base 0x400000");
    File in=new File(args[0]),out=new File(args[1]);
    if(!in.isFile()||out.exists()||in.getCanonicalFile().equals(out.getCanonicalFile()))
      throw new IllegalArgumentException("Missing input or output already exists");
    LinkedHashSet<Long> bases=new LinkedHashSet<>();
    for(String line:Files.readAllLines(in.toPath(),StandardCharsets.UTF_8)){
      String val=line.split("#",2)[0].trim();
      if(val.isEmpty())continue;
      if(!val.matches("(?i)0x[0-9a-f]{1,8}"))throw new IllegalArgumentException(val);
      long base=Long.parseUnsignedLong(val.substring(2),16);
      if((base&3)!=0||base<0x400000)throw new IllegalArgumentException(val);
      bases.add(base);
    }
    Memory m=currentProgram.getMemory();
    String sha=currentProgram.getExecutableSHA256();
    try(PrintWriter w=new PrintWriter(Files.newBufferedWriter(out.toPath(),StandardCharsets.UTF_8))){
      w.println("# ProgramSHA256="+(sha==null?"UNKNOWN":sha)
        +"\tGhidraFunctionCount="+currentProgram.getFunctionManager().getFunctionCount()
        +"\tImageBase=0x00400000");
      w.println("table_va\ttable_rva\trole\tslot_offset\tslot_va\ttarget_va\ttarget_rva\ttarget_exec\tfunction_entry\tcontaining_function\tis_thunk\tcode_ref_count\tcode_ref_examples\tpreceding_dword");
      for(long base:bases){
        monitor.checkCancelled();
        int count=0;StringBuilder froms=new StringBuilder();
        ReferenceIterator it=currentProgram.getReferenceManager().getReferencesTo(toAddr(base));
        while(it.hasNext()){
          Reference ref=it.next();
          MemoryBlock b=m.getBlock(ref.getFromAddress());
          if(b!=null&&b.isExecute()){
            count++;
            if(froms.length()<160){
              if(froms.length()>0)froms.append(';');
              froms.append(ref.getFromAddress().toString());
            }
          }
        }
        String before=dword(m,base-4);
        for(int offset:OFFSETS){
          long slot=base+offset;
          String value=dword(m,slot);
          long target=value.startsWith("0x")?Long.parseUnsignedLong(value.substring(2),16):-1;
          MemoryBlock tb=target>=0?m.getBlock(toAddr(target)):null;
          boolean exec=tb!=null&&tb.isExecute();
          Function exact=exec?currentProgram.getFunctionManager().getFunctionAt(toAddr(target)):null;
          Function containing=exec?currentProgram.getFunctionManager().getFunctionContaining(toAddr(target)):null;
          String role=offset==0x1F0?"POWERWHEEL_TARGET":(offset==0x560?"CONTROLLER_TARGET":"CONTEXT");
          w.printf("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%d\t%s\t%s%n",
            hex(base),hex(base-0x400000L),role,hex(offset),hex(slot),value,
            target<0?"UNREADABLE":hex(target-0x400000L),exec,
            safe(exact==null?"":exact.getName()),
            safe(containing==null?"":containing.getName()),
            containing!=null&&containing.isThunk(),count,safe(froms.toString()),before);
        }
      }
    }
    println("EXP-0018 exported "+bases.size()+" candidate bases; no class owner inferred.");
  }
}
