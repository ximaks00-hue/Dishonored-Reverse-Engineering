using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using ModelContextProtocol.Server;
using System.ComponentModel;
using System.Diagnostics;
using UELib;
using UELib.Core;
#pragma warning disable CS0612, CS0618

var builder = Host.CreateApplicationBuilder(args);
// UELib writes package diagnostics via Console.WriteLine; keep stdout reserved for MCP frames.
Console.SetOut(TextWriter.Null);
builder.Logging.ClearProviders();
builder.Logging.AddConsole(options => options.LogToStandardErrorThreshold = LogLevel.Trace);
builder.Services
    .AddMcpServer(options => options.ServerInfo = new() { Name = "ue-explorer", Version = "1.0.0" })
    .WithStdioServerTransport()
    .WithToolsFromAssembly();
await builder.Build().RunAsync();

[McpServerToolType]
public sealed class UEExplorerTools
{
    private static readonly string GameRoot = Path.GetFullPath(
        Environment.GetEnvironmentVariable("DISHONORED_GAME_ROOT")
        ?? Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "..", "Dishonored RHCP"));
    private static readonly string UModelPath = Environment.GetEnvironmentVariable("UMODEL_PATH")
        ?? @"E:\Dishonored REVERS\third_party\ueviewer-gildor\umodel.exe";

    [McpServerTool(ReadOnly = true), Description("Read package summary and counts using Eliot.UELib (the Unreal package library used by UE Explorer).")]
    public static object InspectPackage([Description("Absolute path or path relative to the configured Dishonored game root.")] string packagePath)
    {
        var path = ResolvePackage(packagePath);
        using var package = UnrealLoader.LoadPackage(path, FileAccess.Read);
        var summary = package.Summary;
        return new
        {
            path,
            package = package.PackageName,
            version = package.Version,
            licenseeVersion = package.LicenseeVersion,
            engineVersion = summary.EngineVersion,
            cookerVersion = summary.CookerVersion,
            isCooked = package.IsCooked(),
            isScript = package.IsScript(),
            names = summary.NameCount,
            exports = summary.ExportCount,
            imports = summary.ImportCount,
            compressedChunks = summary.CompressedChunks?.Count ?? 0,
            compressionFlags = summary.CompressionFlags
        };
    }

    [McpServerTool(ReadOnly = true), Description("Search package names, exports, and parsed objects by case-insensitive substring.")]
    public static object SearchObjects(
        [Description("Package path, absolute or relative to the configured game root.")] string packagePath,
        [Description("Substring to find in object names or class names.")] string query,
        [Description("Maximum number of matches (1-500; default 100).")] int limit = 100)
    {
        var path = ResolvePackage(packagePath);
        limit = Math.Clamp(limit, 1, 500);
        var output = RunUModel("-list", path);
        var needle = query ?? "";
        var matches = output.Split(['\r', '\n'], StringSplitOptions.RemoveEmptyEntries)
            .Where(line => line.Contains(needle, StringComparison.OrdinalIgnoreCase))
            .Take(limit)
            .ToArray();
        return new { path, query = needle, count = matches.Length, results = matches };
    }

    [McpServerTool(ReadOnly = true), Description("Decompile a class, struct, or function by its object name using UELib.")]
    public static object DecompileObject(
        [Description("Package path, absolute or relative to the configured game root.")] string packagePath,
        [Description("Exact object name (case-insensitive).")] string objectName)
    {
        var path = ResolvePackage(packagePath);
using var package = UnrealLoader.LoadPackage(path, FileAccess.Read);
        if (package.Summary.CompressionFlags != 0 && package.Summary.CompressedChunks?.Count > 0)
            return new { error = "This package is compressed. UELib can read its summary, but cannot load the compressed object tables or decompile objects from it." };
        package.InitializePackage();
        var matches = package.Objects
            .Where(o => string.Equals(o.Name.ToString(), objectName, StringComparison.OrdinalIgnoreCase))
            .Take(2)
            .ToArray();
        if (matches.Length == 0) return new { error = "Object not found.", objectName };
        if (matches.Length > 1) return new { error = "Object name is ambiguous; use SearchObjects and a more specific package.", objectName };
        return new { name = matches[0].GetReferencePath(), className = matches[0].GetClassName(), decompiled = matches[0].Decompile() };
    }

    private static string RunUModel(string mode, string packagePath)
    {
        if (!File.Exists(UModelPath)) throw new FileNotFoundException("UModel was not found. Set UMODEL_PATH to umodel.exe.", UModelPath);
        var start = new ProcessStartInfo(UModelPath)
        {
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };
        start.ArgumentList.Add(mode);
        start.ArgumentList.Add($"-path={Path.GetDirectoryName(packagePath)}");
        start.ArgumentList.Add(Path.GetFileName(packagePath));
        using var process = Process.Start(start) ?? throw new InvalidOperationException("Could not start UModel.");
        var stdout = process.StandardOutput.ReadToEnd();
        var stderr = process.StandardError.ReadToEnd();
        process.WaitForExit(120_000);
        if (!process.HasExited) { process.Kill(true); throw new TimeoutException("UModel timed out while reading the package."); }
        if (process.ExitCode != 0) throw new InvalidOperationException($"UModel exited with code {process.ExitCode}: {stderr}");
        return stdout;
    }

    private static string ResolvePackage(string requested)
    {
        var path = Path.GetFullPath(Path.IsPathRooted(requested) ? requested : Path.Combine(GameRoot, requested));
        var root = Path.GetFullPath(GameRoot).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        if (!path.StartsWith(root, StringComparison.OrdinalIgnoreCase))
            throw new ArgumentException("Package must be inside DISHONORED_GAME_ROOT.");
        if (!File.Exists(path)) throw new FileNotFoundException("Package not found.", path);
        return path;
    }
}




