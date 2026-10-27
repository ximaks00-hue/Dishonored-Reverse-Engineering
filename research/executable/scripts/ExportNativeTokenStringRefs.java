// Read-only search for native-exec registration-name strings and their xrefs.
// Args: input CSV (native_token,package,object_name), output CSV.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public class ExportNativeTokenStringRefs extends GhidraScript {
    private static class Record {
        String token;
        String packageName;
        String objectName;
        String searchString;
    }

    private static String csv(String value) {
        return "\"" + value.replace("\"", "\"\"") + "\"";
    }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 2) {
            throw new IllegalArgumentException("Pass input CSV and output CSV paths");
        }
        List<Record> records = new ArrayList<>();
        try (BufferedReader reader = new BufferedReader(new FileReader(args[0], StandardCharsets.UTF_8))) {
            String line;
            boolean header = true;
            while ((line = reader.readLine()) != null) {
                if (header) { header = false; continue; }
                String[] parts = line.split(",", -1);
                if (parts.length != 4) throw new IllegalArgumentException("Malformed input row: " + line);
                Record record = new Record();
                record.token = parts[0];
                record.packageName = parts[1];
                record.objectName = parts[2];
                record.searchString = parts[3];
                records.add(record);
            }
        }

        int stringsFound = 0;
        Set<String> recordsWithXrefs = new HashSet<>();
        try (PrintWriter writer = new PrintWriter(new File(args[1]), StandardCharsets.UTF_8)) {
            writer.println("native_token,package,object_name,search_string,string_va,xref_from_va,xref_function_va,xref_function_name,reference_type");
            for (Record record : records) {
                monitor.checkCancelled();
                String search = record.searchString;
                byte[] needle = search.getBytes(StandardCharsets.US_ASCII);
                Address cursor = currentProgram.getMinAddress();
                boolean foundForRecord = false;
                while (cursor != null) {
                    Address found = currentProgram.getMemory().findBytes(
                            cursor, currentProgram.getMaxAddress(), needle, null, true, monitor);
                    if (found == null) break;
                    foundForRecord = true;
                    stringsFound++;
                    ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(found);
                    boolean hadRef = false;
                    while (refs.hasNext()) {
                        Reference ref = refs.next();
                        hadRef = true;
                        Address from = ref.getFromAddress();
                        Function function = getFunctionContaining(from);
                        writer.printf("%s,%s,%s,%s,%s,%s,%s,%s,%s%n",
                                record.token, csv(record.packageName), csv(record.objectName),
                                csv(search), found, from,
                                function == null ? "" : function.getEntryPoint(),
                                csv(function == null ? "" : function.getName()),
                                csv(ref.getReferenceType().toString()));
                    }
                    if (hadRef) recordsWithXrefs.add(record.token + "|" + record.packageName + "|" + record.objectName);
                    cursor = found.add(1);
                }
                if (!foundForRecord) {
                    writer.printf("%s,%s,%s,%s,,,,,%n", record.token,
                            csv(record.packageName), csv(record.objectName), csv(search));
                }
            }
        }
        println("INPUT_RECORDS=" + records.size());
        println("STRING_OCCURRENCES=" + stringsFound);
        println("RECORDS_WITH_XREFS=" + recordsWithXrefs.size());
        println("OUTPUT=" + new File(args[1]).getAbsolutePath());
        println("PROGRAM=" + currentProgram.getName());
    }
}
