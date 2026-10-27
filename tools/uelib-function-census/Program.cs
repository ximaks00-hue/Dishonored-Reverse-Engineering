using System.Diagnostics;
using System.Security.Cryptography;
using System.Text.Json;
using UELib;
using UELib.Core;

#pragma warning disable CS0612, CS0618

var originalOut = Console.Out;
var argsList = args.ToList();
string? Value(string option)
{
    var i = argsList.IndexOf(option);
    return i >= 0 && i + 1 < argsList.Count ? argsList[i + 1] : null;
}

var decompressorArg = Value("--decompressor");
var outputRootArg = Value("--output-root");
var jsonOutputArg = Value("--json-output");
var emitDecompiledJsonl = argsList.Contains("--emit-decompiled-jsonl", StringComparer.Ordinal);
var packages = new List<string>();
for (var i = 0; i < argsList.Count; i++)
{
    if (argsList[i] is "--decompressor" or "--output-root" or "--json-output") { i++; continue; }
    if (argsList[i] == "--emit-decompiled-jsonl") continue;
    if (argsList[i].StartsWith("--", StringComparison.Ordinal))
        throw new ArgumentException($"Unknown option: {argsList[i]}");
    packages.Add(argsList[i]);
}

if (decompressorArg is null || outputRootArg is null || packages.Count == 0)
{
    originalOut.WriteLine("Usage: dotnet run --project tools/uelib-function-census -- --decompressor <decompress.exe> --output-root <ignored-output-dir> [--json-output <path>] [--emit-decompiled-jsonl] <package.upk> [package.upk ...]");
    return 2;
}

var decompressor = Path.GetFullPath(decompressorArg);
var outputRoot = Path.GetFullPath(outputRootArg);
if (!File.Exists(decompressor)) throw new FileNotFoundException("Decompressor not found", decompressor);
Directory.CreateDirectory(outputRoot);
var runDirectory = Path.Combine(outputRoot, DateTime.UtcNow.ToString("yyyyMMdd-HHmmss-fff") + "-" + Guid.NewGuid().ToString("N")[..8]);
Directory.CreateDirectory(runDirectory);

var results = new List<object>();
for (var index = 0; index < packages.Count; index++)
{
    var source = Path.GetFullPath(packages[index]);
    if (!File.Exists(source))
    {
        results.Add(new { source, error = "source_not_found" });
        continue;
    }

    var sourceInfo = new FileInfo(source);
    var sourceHash = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(source)));
    var destination = Path.Combine(runDirectory, $"{index:D3}-{Path.GetFileNameWithoutExtension(source)}");
    Directory.CreateDirectory(destination);
    var outputPackage = Path.Combine(destination, Path.GetFileName(source));

    var start = new ProcessStartInfo(decompressor)
    {
        RedirectStandardOutput = true,
        RedirectStandardError = true,
        UseShellExecute = false,
        CreateNoWindow = true
    };
    start.ArgumentList.Add("-game=dis");
    start.ArgumentList.Add($"-path={Path.GetDirectoryName(source)}");
    start.ArgumentList.Add($"-out={destination}");
    start.ArgumentList.Add(Path.GetFileName(source));
    using var process = Process.Start(start) ?? throw new InvalidOperationException("Could not start package decompressor.");
    var stdoutTask = process.StandardOutput.ReadToEndAsync();
    var stderrTask = process.StandardError.ReadToEndAsync();
    await process.WaitForExitAsync();
    var decompressorOutput = (await stdoutTask) + (await stderrTask);
    if (process.ExitCode != 0 || !File.Exists(outputPackage))
    {
        results.Add(new { source, sourceBytes = sourceInfo.Length, sourceSha256 = sourceHash, decompressorExitCode = process.ExitCode, decompressorOutput, error = "decompression_failed" });
        continue;
    }

    try
    {
        var diagnostics = new StringWriter();
        Console.SetOut(diagnostics);
        using var package = UnrealLoader.LoadPackage(outputPackage, FileAccess.Read);
        package.InitializePackage();

        var functions = package.Objects.OfType<UFunction>().ToArray();
        var exportedFunctions = functions.Where(f => f.ExportTable is not null).ToArray();
        var importedFunctions = functions.Count(f => f.ImportTable is not null);
        var objectTypes = package.Objects
            .GroupBy(obj => obj.GetType().Name)
            .OrderBy(group => group.Key, StringComparer.Ordinal)
            .ToDictionary(group => group.Key, group => group.Count(), StringComparer.Ordinal);
        var exportClassTypes = package.Exports
            .GroupBy(export => export.ClassName ?? "<null>")
            .OrderBy(group => group.Key, StringComparer.Ordinal)
            .ToDictionary(group => group.Key, group => group.Count(), StringComparer.Ordinal);
        var objectTypeCounts = new
        {
            classes = package.Objects.Count(obj => string.Equals(obj.GetType().Name, "UClass", StringComparison.Ordinal)),
            metaClasses = package.Objects.Count(obj => string.Equals(obj.GetType().Name, "UMetaClass", StringComparison.Ordinal)),
            scriptStructs = package.Objects.OfType<UScriptStruct>().Count(),
            otherStructs = package.Objects.OfType<UStruct>().Count(obj => obj is not UClass and not UFunction and not UScriptStruct),
            functions = exportedFunctions.Length,
            enums = package.Objects.OfType<UEnum>().Count(),
            properties = package.Objects.OfType<UProperty>().Count(),
            classDefaultObjects = package.Objects.Count(obj => obj.ExportTable is not null && obj.ExportTable.ClassName == "ClassDefaultObject"),
            unknownObjects = package.Objects.Count(obj => string.Equals(obj.GetType().Name, "UnknownObject", StringComparison.Ordinal))
        };
        var exportFailures = new List<object>();
        foreach (var export in package.Exports)
        {
            try
            {
                _ = export.Object;
            }
            catch (Exception exception)
            {
                exportFailures.Add(new { export.ObjectName, export.ClassName, error = exception.GetType().Name, detail = exception.Message });
            }
        }
        if (functions.Length > 0)
        {
            var rawFlags = functions[0].FunctionFlags.GetType().GetField("_RawValue", System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic)
                ?? throw new InvalidOperationException("UELib function flag raw value field was not found.");
            var decompiledText = new Dictionary<UFunction, string>();
            bool IsNative(UFunction function) => (((ulong)rawFlags.GetValue(function.FunctionFlags)!) & 0x400) != 0;
            bool HasBodyLines(UFunction function)
            {
                var sourceText = decompiledText[function];
                var bodyStart = sourceText.IndexOf("\n{", StringComparison.Ordinal);
                if (bodyStart < 0) return false;
                return sourceText[(bodyStart + 2)..].Split('\n').Any(line =>
                {
                    var trimmed = line.Trim();
                    return trimmed.Length > 0 && trimmed != "}" && !trimmed.StartsWith("//", StringComparison.Ordinal);
                });
            }

            var nonNative = exportedFunctions.Where(f => !IsNative(f)).ToArray();
            var jsonlPath = emitDecompiledJsonl ? outputPackage + ".functions.jsonl" : null;
            using (var jsonl = jsonlPath is null ? null : new StreamWriter(jsonlPath))
            {
                foreach (var function in exportedFunctions)
                {
                    if (!emitDecompiledJsonl && IsNative(function)) continue;
                    var decompiled = function.Decompile();
                    decompiledText.Add(function, decompiled);
                    jsonl?.WriteLine(JsonSerializer.Serialize(new
                    {
                        package = source,
                        sourceSha256 = sourceHash,
                        objectPath = function.GetReferencePath(),
                        objectName = function.Name.ToString(),
                        nativeFlag = IsNative(function),
                        nativeToken = function.NativeToken,
                        operatorPrecedence = function.OperPrecedence,
                        scriptSize = function.ScriptSize,
                        decompiled
                    }));
                }
            }
            var withBodyLines = nonNative.Count(HasBodyLines);
            Console.SetOut(originalOut);
            results.Add(new
            {
                source,
                sourceBytes = sourceInfo.Length,
                sourceSha256 = sourceHash,
                decompressedPath = outputPackage,
                decompressedBytes = new FileInfo(outputPackage).Length,
                decompressorExitCode = process.ExitCode,
                packageName = package.PackageName,
                version = package.Version,
                licenseeVersion = package.LicenseeVersion,
                isScript = package.IsScript(),
                exportCount = package.Exports.Count,
                importCount = package.Imports.Count,
                exportTableFunctionClassNames = package.Exports.Count(e => string.Equals(e.ClassName, "Function", StringComparison.Ordinal)),
                initializedObjects = package.Objects.Count,
                objectTypeCounts,
                objectTypes,
                exportClassTypes,
                exportObjectFailures = exportFailures.Count,
                exportFailureSamples = exportFailures.Take(50),
                exportedUFunctions = exportedFunctions.Length,
                importedUFunctions = importedFunctions,
                nativeFlagExports = exportedFunctions.Count(IsNative),
                nonNativeFlagExports = nonNative.Length,
                nonNativeWithBodyLines = withBodyLines,
                nonNativeWithoutBodyLines = nonNative.Length - withBodyLines,
                decompiledJsonlPath = jsonlPath,
                diagnostics = diagnostics.ToString().Split(['\r', '\n'], StringSplitOptions.RemoveEmptyEntries),
                decompressorOutput
            });
        }
        else
        {
            Console.SetOut(originalOut);
            results.Add(new
            {
                source,
                sourceBytes = sourceInfo.Length,
                sourceSha256 = sourceHash,
                decompressedPath = outputPackage,
                decompressedBytes = new FileInfo(outputPackage).Length,
                decompressorExitCode = process.ExitCode,
                packageName = package.PackageName,
                version = package.Version,
                licenseeVersion = package.LicenseeVersion,
                isScript = package.IsScript(),
                exportCount = package.Exports.Count,
                importCount = package.Imports.Count,
                exportTableFunctionClassNames = package.Exports.Count(e => string.Equals(e.ClassName, "Function", StringComparison.Ordinal)),
                initializedObjects = package.Objects.Count,
                objectTypeCounts,
                objectTypes,
                exportClassTypes,
                exportObjectFailures = exportFailures.Count,
                exportFailureSamples = exportFailures.Take(50),
                exportedUFunctions = 0,
                importedUFunctions = 0,
                nativeFlagExports = 0,
                nonNativeFlagExports = 0,
                nonNativeWithBodyLines = 0,
                nonNativeWithoutBodyLines = 0,
                decompiledJsonlPath = (string?)null,
                diagnostics = diagnostics.ToString().Split(['\r', '\n'], StringSplitOptions.RemoveEmptyEntries),
                decompressorOutput
            });
        }
    }
    catch (Exception exception)
    {
        Console.SetOut(originalOut);
        results.Add(new { source, sourceBytes = sourceInfo.Length, sourceSha256 = sourceHash, decompressedPath = outputPackage, error = exception.GetType().Name, detail = exception.Message });
    }
}

var resultJson = JsonSerializer.Serialize(new { runDirectory, results }, new JsonSerializerOptions { WriteIndented = true });
if (jsonOutputArg is not null)
{
    var jsonOutput = Path.GetFullPath(jsonOutputArg);
    Directory.CreateDirectory(Path.GetDirectoryName(jsonOutput)!);
    await File.WriteAllTextAsync(jsonOutput, resultJson);
    originalOut.WriteLine($"Wrote {results.Count} package results to {jsonOutput}");
}
else
{
    originalOut.WriteLine(resultJson);
}
return 0;
