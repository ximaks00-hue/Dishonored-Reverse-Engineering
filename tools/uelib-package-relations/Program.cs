using System.Diagnostics;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.RegularExpressions;
using UELib;
using UELib.Core;

#pragma warning disable CS0612, CS0618

static string? Value(string[] args, string name)
{
    var i = Array.IndexOf(args, name);
    return i >= 0 && i + 1 < args.Length ? args[i + 1] : null;
}

var gameRootArg = Value(args, "--game-root");
var manifestArg = Value(args, "--manifest");
var decompressorArg = Value(args, "--decompressor");
var outputArg = Value(args, "--output-dir");
var onlyArg = Value(args, "--only");
var initializeObjects = args.Contains("--initialize", StringComparer.Ordinal);
var loadOnDemandObjects = args.Contains("--load-on-demand", StringComparer.Ordinal);
if (gameRootArg is null || manifestArg is null || decompressorArg is null || outputArg is null)
{
    Console.Error.WriteLine("Usage: --game-root <dir> --manifest <files.csv> --decompressor <decompress.exe> --output-dir <ignored-dir> [--only <relative-upk-path>] [--initialize] [--load-on-demand]");
    return 2;
}

var gameRoot = Path.GetFullPath(gameRootArg);
var manifestPath = Path.GetFullPath(manifestArg);
var decompressor = Path.GetFullPath(decompressorArg);
var outputDir = Path.GetFullPath(outputArg);
Directory.CreateDirectory(outputDir);

var manifestRows = new List<(string RelativePath, long Length, string Sha256)>();
using (var reader = new StreamReader(manifestPath))
{
    _ = reader.ReadLine();
    while (reader.ReadLine() is { } line)
    {
        var columns = line.Split(',');
        if (columns.Length < 3 || !columns[0].EndsWith(".upk", StringComparison.OrdinalIgnoreCase)) continue;
        if (onlyArg is not null && !columns[0].Replace('\\', '/').Equals(onlyArg.Replace('\\', '/'), StringComparison.OrdinalIgnoreCase)) continue;
        manifestRows.Add((columns[0].Replace('/', Path.DirectorySeparatorChar), long.Parse(columns[1]), columns[2]));
    }
}

var objectsPath = Path.Combine(outputDir, "package-objects.jsonl");
var edgesPath = Path.Combine(outputDir, "package-edges.jsonl");
var errorsPath = Path.Combine(outputDir, "package-errors.jsonl");
var summaryPath = Path.Combine(outputDir, "package-summary.jsonl");
var initializedObjectsPath = Path.Combine(outputDir, "initialized-objects.jsonl");
var initializedEdgesPath = Path.Combine(outputDir, "initialized-edges.jsonl");
var defaultPropertiesPath = Path.Combine(outputDir, "default-properties.jsonl");
var defaultPropertyReferencesPath = Path.Combine(outputDir, "default-property-reference-mentions.jsonl");
var initializationPath = Path.Combine(outputDir, "initialization-summary.jsonl");
var processed = 0;
var failed = 0;
var objectRows = 0;
var edgeRows = 0;

using var objectsWriter = new StreamWriter(objectsPath, append: false);
using var edgesWriter = new StreamWriter(edgesPath, append: false);
using var errorsWriter = new StreamWriter(errorsPath, append: false);
using var summaryWriter = new StreamWriter(summaryPath, append: false);
using var initializedObjectsWriter = initializeObjects ? new StreamWriter(initializedObjectsPath, append: false) : null;
using var initializedEdgesWriter = initializeObjects ? new StreamWriter(initializedEdgesPath, append: false) : null;
using var defaultPropertiesWriter = initializeObjects ? new StreamWriter(defaultPropertiesPath, append: false) : null;
using var defaultPropertyReferencesWriter = initializeObjects ? new StreamWriter(defaultPropertyReferencesPath, append: false) : null;
using var initializationWriter = initializeObjects ? new StreamWriter(initializationPath, append: false) : null;

foreach (var row in manifestRows)
{
    var source = Path.GetFullPath(Path.Combine(gameRoot, row.RelativePath));
    var sourceFull = Path.GetFullPath(source);
    if (!sourceFull.StartsWith(gameRoot.TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase))
        throw new InvalidOperationException($"Manifest path escaped game root: {row.RelativePath}");
    var packageDirectory = Path.GetDirectoryName(source)!;
    var workDir = Path.Combine(Path.GetTempPath(), "dishonored-uelib-relations", Guid.NewGuid().ToString("N"));
    Directory.CreateDirectory(workDir);
    var decompressed = Path.Combine(workDir, Path.GetFileName(source));
    using var sourceStream = File.OpenRead(source);
    var actualHash = Convert.ToHexString(SHA256.HashData(sourceStream));
    var sizeMatch = new FileInfo(source).Length == row.Length;
    var hashMatch = actualHash.Equals(row.Sha256, StringComparison.OrdinalIgnoreCase);
    if (!sizeMatch || !hashMatch)
    {
        failed++;
        errorsWriter.WriteLine(JsonSerializer.Serialize(new { package = row.RelativePath, error = "source_manifest_mismatch", sizeMatch, hashMatch, expectedSha256 = row.Sha256, actualSha256 = actualHash }));
        Directory.Delete(workDir, recursive: true);
        continue;
    }

    var procStart = new ProcessStartInfo(decompressor)
    {
        RedirectStandardOutput = true,
        RedirectStandardError = true,
        UseShellExecute = false,
        CreateNoWindow = true,
    };
    procStart.ArgumentList.Add("-game=dis");
    procStart.ArgumentList.Add($"-path={packageDirectory}");
    procStart.ArgumentList.Add($"-out={workDir}");
    procStart.ArgumentList.Add(Path.GetFileName(source));

    try
    {
        using var process = Process.Start(procStart) ?? throw new InvalidOperationException("Could not start package decompressor");
        var stdoutTask = process.StandardOutput.ReadToEndAsync();
        var stderrTask = process.StandardError.ReadToEndAsync();
        await process.WaitForExitAsync();
        var decompressorOutput = (await stdoutTask) + (await stderrTask);
        if (process.ExitCode != 0 || !File.Exists(decompressed))
        {
            failed++;
            errorsWriter.WriteLine(JsonSerializer.Serialize(new { package = row.RelativePath, error = "decompression_failed", exitCode = process.ExitCode, output = decompressorOutput }));
            continue;
        }

        var previousConsole = Console.Out;
        UnrealPackage package;
        try
        {
            Console.SetOut(TextWriter.Null);
            package = UnrealLoader.LoadPackage(decompressed, FileAccess.Read);
        }
        finally
        {
            Console.SetOut(previousConsole);
        }
        using var packageScope = package;
        var importItems = package.Imports.ToArray();
        var exportItems = package.Exports.ToArray();
        var tableObjects = new Dictionary<int, object>();
        for (var i = 0; i < importItems.Length; i++) tableObjects[-(i + 1)] = importItems[i];
        for (var i = 0; i < exportItems.Length; i++) tableObjects[i + 1] = exportItems[i];

        string? ObjectName(int index) => tableObjects.TryGetValue(index, out var item)
            ? item switch
            {
                UObjectTableItem tableItem => tableItem.ObjectName.ToString(),
                _ => null,
            }
            : null;
        string Resolve(int index) => index == 0 ? "null" : ObjectName(index) is { } name
            ? $"{(index < 0 ? "import" : "export")}:{Math.Abs(index)}:{name}"
            : $"unresolved:{index}";

        for (var importPosition = 0; importPosition < importItems.Length; importPosition++)
        {
            var index = -(importPosition + 1);
            var item = importItems[importPosition];
            var name = item.ObjectName.ToString();
            var outerIndex = item.OuterIndex.Index;
            objectsWriter.WriteLine(JsonSerializer.Serialize(new
            {
                package = row.RelativePath.Replace('\\', '/'), sourceSha256 = row.Sha256,
                table = "import", tableIndex = index, objectName = name,
                className = item.ClassName.ToString(), classPackageName = item.ClassPackageName.ToString(),
                packageName = item.PackageName.ToString(), outerIndex, outerTarget = Resolve(outerIndex),
            }));
            objectRows++;
            if (outerIndex != 0)
            {
                edgesWriter.WriteLine(JsonSerializer.Serialize(new { package = row.RelativePath.Replace('\\', '/'), fromTable = "import", fromIndex = index, fromName = name, relation = "outer", targetIndex = outerIndex, target = Resolve(outerIndex), claim = "serialized_table_index" }));
                edgeRows++;
            }
        }

        for (var exportPosition = 0; exportPosition < exportItems.Length; exportPosition++)
        {
            var index = exportPosition + 1;
            var item = exportItems[exportPosition];
            var name = item.ObjectName.ToString();
            var outerIndex = item.OuterIndex.Index;
            var classIndex = item.ClassIndex.Index;
            var superIndex = item.SuperIndex.Index;
            var templateIndex = item.TemplateIndex.Index;
            var archetypeIndex = item.ArchetypeIndex.Index;
            objectsWriter.WriteLine(JsonSerializer.Serialize(new
            {
                package = row.RelativePath.Replace('\\', '/'), sourceSha256 = row.Sha256,
                table = "export", tableIndex = index, objectName = name,
                className = item.ClassName, outerIndex, outerTarget = Resolve(outerIndex),
                classIndex, classTarget = Resolve(classIndex), superIndex, superTarget = Resolve(superIndex),
                templateIndex, templateTarget = Resolve(templateIndex), archetypeIndex, archetypeTarget = Resolve(archetypeIndex),
                serialSize = item.SerialSize, serialOffset = item.SerialOffset,
            }));
            objectRows++;
            foreach (var (relation, targetIndex) in new[]
            {
                ("outer", outerIndex), ("class", classIndex), ("super", superIndex), ("template", templateIndex), ("archetype", archetypeIndex),
            })
            {
                if (targetIndex == 0) continue;
                edgesWriter.WriteLine(JsonSerializer.Serialize(new { package = row.RelativePath.Replace('\\', '/'), fromTable = "export", fromIndex = index, fromName = name, relation, targetIndex, target = Resolve(targetIndex), claim = "serialized_table_index" }));
                edgeRows++;
            }
        }

        var initializedCount = 0;
        var initializedEdgeCount = 0;
        var defaultPropertyCount = 0;
        var defaultPropertyReferenceCount = 0;
        string? initializeError = null;
        if (initializeObjects)
        {
            var previousInitializeConsole = Console.Out;
            var previousInitializeError = Console.Error;
            try
            {
                Console.SetOut(TextWriter.Null);
                Console.SetError(TextWriter.Null);
                package.InitializePackage();
            }
            catch (Exception exception)
            {
                initializeError = $"{exception.GetType().Name}: {exception.Message}";
            }
            finally
            {
                Console.SetOut(previousInitializeConsole);
                Console.SetError(previousInitializeError);
            }

            if (initializeError is null)
            {
                string? SafePath(UObject? obj)
                {
                    if (obj is null) return null;
                    try { return obj.GetReferencePath(); }
                    catch { return null; }
                }

                string? TypedReference(UProperty property) => property switch
                {
                    UClassProperty classProperty => SafePath(classProperty.MetaClass),
                    UObjectProperty objectProperty => SafePath(objectProperty.Object),
                    UStructProperty structProperty => SafePath(structProperty.Struct),
                    UArrayProperty arrayProperty => SafePath(arrayProperty.InnerProperty),
                    UByteProperty byteProperty => SafePath(byteProperty.Enum),
                    _ => null,
                };

                foreach (var obj in package.Objects)
                {
                    var packageIndex = obj.PackageIndex.Index;
                    var shouldDeserializeOnDemand = obj.ShouldDeserializeOnDemand;
                    var onDemandLoadAttempted = loadOnDemandObjects && shouldDeserializeOnDemand && packageIndex > 0;
                    string? onDemandLoadError = null;
                    string? onDemandDiagnosticSample = null;
                    var onDemandDiagnosticLineCount = 0;
                    if (onDemandLoadAttempted)
                    {
                        using var diagnosticWriter = new StringWriter();
                        var previousLoadConsole = Console.Out;
                        var previousLoadError = Console.Error;
                        try
                        {
                            Console.SetOut(diagnosticWriter);
                            Console.SetError(diagnosticWriter);
                            obj.Load();
                        }
                        catch (Exception exception)
                        {
                            onDemandLoadError = $"{exception.GetType().Name}: {exception.Message}";
                        }
                        finally
                        {
                            Console.SetOut(previousLoadConsole);
                            Console.SetError(previousLoadError);
                        }
                        var diagnosticLines = diagnosticWriter.ToString().Split(
                            new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);
                        onDemandDiagnosticLineCount = diagnosticLines.Length;
                        if (diagnosticLines.Length > 0)
                            onDemandDiagnosticSample = string.Join(" | ", diagnosticLines.Take(4));
                    }
                    var referencePath = SafePath(obj);
                    var defaultProperties = obj.Properties;
                    var propertyCount = defaultProperties?.Count ?? 0;
                    var super = obj is UStruct structObject ? SafePath(structObject.Super) : null;
                    var nextField = obj is UField fieldObject ? SafePath(fieldObject.NextField) : null;
                    var propertyTypeReference = obj is UProperty typeProperty ? TypedReference(typeProperty) : null;
                    initializedObjectsWriter!.WriteLine(JsonSerializer.Serialize(new
                    {
                        package = row.RelativePath.Replace('\\', '/'), sourceSha256 = row.Sha256,
                        packageIndex, table = packageIndex < 0 ? "import" : packageIndex > 0 ? "export" : "none",
                        objectType = obj.GetType().Name, objectName = obj.Name.ToString(),
                        objectPath = referencePath, classPath = SafePath(obj.Class), outerPath = SafePath(obj.Outer),
                        archetypePath = SafePath(obj.Archetype), defaultObjectPath = SafePath(obj.Default),
                        superPath = super, nextFieldPath = nextField,
                        propertyTypeReferencePath = propertyTypeReference,
                        shouldDeserializeOnDemand,
                        onDemandLoadAttempted,
                        onDemandLoadError,
                        onDemandDiagnosticLineCount,
                        onDemandDiagnosticSample,
                        exportClassName = obj.ExportTable?.ClassName, importClassName = obj.ImportTable?.ClassName.ToString(),
                        defaultPropertyCount = propertyCount,
                        exceptionType = obj.ThrownException?.GetType().Name,
                        exceptionMessage = obj.ThrownException?.Message,
                        deserializationState = obj.DeserializationState.ToString(),
                    }));
                    initializedCount++;

                    foreach (var (relation, targetPath) in new[]
                    {
                        ("class", SafePath(obj.Class)), ("outer", SafePath(obj.Outer)),
                        ("archetype", SafePath(obj.Archetype)), ("default_object", SafePath(obj.Default)),
                        ("super", super), ("next_field", nextField), ("property_type", propertyTypeReference),
                    })
                    {
                        if (targetPath is null) continue;
                        initializedEdgesWriter!.WriteLine(JsonSerializer.Serialize(new
                        {
                            package = row.RelativePath.Replace('\\', '/'), sourceSha256 = row.Sha256,
                            fromPackageIndex = packageIndex, fromObjectPath = referencePath,
                            relation, targetObjectPath = targetPath,
                            claim = "UELib initialized object relation",
                        }));
                        initializedEdgeCount++;
                    }

                    for (var propertyIndex = 0; propertyIndex < propertyCount; propertyIndex++)
                    {
                        var property = defaultProperties![propertyIndex];
                        if (property is null) continue;
                        string? value = null;
                        string? valueError = null;
                        var valueDiagnosticLineCount = 0;
                        string? valueDiagnosticSample = null;
                        try
                        {
                            if (onDemandLoadAttempted)
                            {
                                using var valueDiagnosticWriter = new StringWriter();
                                var previousValueConsole = Console.Out;
                                var previousValueError = Console.Error;
                                try
                                {
                                    Console.SetOut(valueDiagnosticWriter);
                                    Console.SetError(valueDiagnosticWriter);
                                    value = property.Value;
                                }
                                finally
                                {
                                    Console.SetOut(previousValueConsole);
                                    Console.SetError(previousValueError);
                                }
                                var valueDiagnosticLines = valueDiagnosticWriter.ToString().Split(
                                    new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);
                                valueDiagnosticLineCount = valueDiagnosticLines.Length;
                                if (valueDiagnosticLines.Length > 0)
                                    valueDiagnosticSample = string.Join(" | ", valueDiagnosticLines.Take(4));
                            }
                            else value = property.Value;
                        }
                        catch (Exception exception) { valueError = $"{exception.GetType().Name}: {exception.Message}"; }
                        defaultPropertiesWriter!.WriteLine(JsonSerializer.Serialize(new
                        {
                            package = row.RelativePath.Replace('\\', '/'), sourceSha256 = row.Sha256,
                            ownerPackageIndex = packageIndex, ownerObjectPath = referencePath,
                            propertyIndex, propertyName = property.Name?.ToString(), propertyType = property.Type.ToString(),
                            propertySize = property.Size, arrayIndex = property.ArrayIndex,
                            boolValue = property.BoolValue, structName = property.StructName?.ToString(),
                            enumName = property.EnumName?.ToString(), innerTypeName = property.InnerTypeName?.ToString(),
                            value, valueError, valueDiagnosticLineCount, valueDiagnosticSample,
                        }));
                        defaultPropertyCount++;
                        foreach (Match match in Regex.Matches(value ?? "", @"// Reference:\s*(?<class>[^'\r\n]+)'(?<path>[^'\r\n]+)'"))
                        {
                            defaultPropertyReferencesWriter!.WriteLine(JsonSerializer.Serialize(new
                            {
                                package = row.RelativePath.Replace('\\', '/'), sourceSha256 = row.Sha256,
                                ownerPackageIndex = packageIndex, ownerObjectPath = referencePath,
                                propertyName = property.Name?.ToString(), propertyType = property.Type.ToString(),
                                referenceClassLabel = match.Groups["class"].Value.Trim(),
                                referenceObjectPath = match.Groups["path"].Value.Trim(),
                                claim = "reference mention parsed from UELib formatted default-property value",
                            }));
                            defaultPropertyReferenceCount++;
                        }
                    }

                    // UnknownObject deliberately retains its object buffer after Load().
                    // Once its decoded fields are emitted above, release that package-local
                    // payload so an all-install on-demand pass does not pin every buffer.
                    if (onDemandLoadAttempted) obj.Buffer?.Dispose();
                }
            }

            initializationWriter!.WriteLine(JsonSerializer.Serialize(new
            {
                package = row.RelativePath.Replace('\\', '/'), sourceSha256 = row.Sha256,
                initializedObjects = initializedCount, initializedEdges = initializedEdgeCount,
                defaultProperties = defaultPropertyCount,
                defaultPropertyReferenceMentions = defaultPropertyReferenceCount,
                initializationError = initializeError,
                objectTypes = initializeError is null
                    ? package.Objects.GroupBy(obj => obj.GetType().Name).ToDictionary(group => group.Key, group => group.Count())
                    : null,
                objectStates = initializeError is null
                    ? package.Objects.GroupBy(obj => obj.DeserializationState.ToString()).ToDictionary(group => group.Key, group => group.Count())
                    : null,
            }));
        }

        summaryWriter.WriteLine(JsonSerializer.Serialize(new
        {
            package = row.RelativePath.Replace('\\', '/'), sourceBytes = row.Length, sourceSha256 = row.Sha256,
            packageVersion = package.Version, licenseeVersion = package.LicenseeVersion,
            exportCount = exportItems.Length, importCount = importItems.Length,
            objectRows = exportItems.Length + importItems.Length,
            initializedObjects = initializedCount, initializedEdges = initializedEdgeCount,
            defaultProperties = defaultPropertyCount,
            defaultPropertyReferenceMentions = defaultPropertyReferenceCount,
            initializationError = initializeError,
            links = new { importOuters = importItems.Count(x => !x.OuterIndex.IsNull), exportOuters = exportItems.Count(x => !x.OuterIndex.IsNull), exportClasses = exportItems.Count(x => !x.ClassIndex.IsNull), exportSupers = exportItems.Count(x => !x.SuperIndex.IsNull), exportTemplates = exportItems.Count(x => !x.TemplateIndex.IsNull), exportArchetypes = exportItems.Count(x => !x.ArchetypeIndex.IsNull) },
            relationSource = "UELib package import/export table indices; no object initialization required",
        }));
        processed++;
    }
    catch (Exception exception)
    {
        failed++;
        errorsWriter.WriteLine(JsonSerializer.Serialize(new { package = row.RelativePath.Replace('\\', '/'), sourceSha256 = row.Sha256, error = exception.GetType().Name, detail = exception.Message }));
    }
    finally
    {
        try { Directory.Delete(workDir, recursive: true); }
        catch { }
        if (loadOnDemandObjects)
        {
            // A single package may retain many UELib object graphs. Do a collection after
            // the package scope is disposed to bound memory during a 904-package pass.
            GC.Collect();
        }
    }

    if ((processed + failed) % 50 == 0)
    {
        await objectsWriter.FlushAsync();
        await edgesWriter.FlushAsync();
        await errorsWriter.FlushAsync();
        await summaryWriter.FlushAsync();
        if (initializeObjects)
        {
            await initializedObjectsWriter!.FlushAsync();
            await initializedEdgesWriter!.FlushAsync();
            await defaultPropertiesWriter!.FlushAsync();
            await defaultPropertyReferencesWriter!.FlushAsync();
            await initializationWriter!.FlushAsync();
        }
        Console.WriteLine($"packages={processed + failed}/{manifestRows.Count} processed={processed} failed={failed} objects={objectRows} edges={edgeRows}");
    }
}

await objectsWriter.FlushAsync();
await edgesWriter.FlushAsync();
await errorsWriter.FlushAsync();
await summaryWriter.FlushAsync();
if (initializeObjects)
{
    await initializedObjectsWriter!.FlushAsync();
    await initializedEdgesWriter!.FlushAsync();
    await defaultPropertiesWriter!.FlushAsync();
    await defaultPropertyReferencesWriter!.FlushAsync();
    await initializationWriter!.FlushAsync();
}
Console.WriteLine(JsonSerializer.Serialize(new { packagesInScope = manifestRows.Count, processed, failed, objectRows, edgeRows, initializeObjects, outputDir }));
return 0;
