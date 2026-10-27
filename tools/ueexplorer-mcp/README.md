# UE Explorer MCP

Read-only MCP server for Dishonored UE3 packages. It uses Eliot.UELib, the Unreal package and UnrealScript library available as the official package. The MCP process uses .NET 8 so it runs independently of UE Explorer's .NET Framework 4.8 Windows UI.

## Tools

- `inspect_package`: package version, engine/cooker metadata and table counts.
- `search_objects`: case-insensitive search in UModel's package object listing.
- `decompile_object`: decompile a uniquely named parsed object.

All tools are read-only. Package paths must resolve inside `DISHONORED_GAME_ROOT`. The default is this repository's `Dishonored RHCP` directory.

## Build and run

From the repository root in PowerShell:

```powershell
$env:NUGET_PACKAGES = (Join-Path (Get-Location) '.nuget\packages')
dotnet restore tools\ueexplorer-mcp\ueexplorer-mcp.csproj
dotnet build tools\ueexplorer-mcp\ueexplorer-mcp.csproj --configuration Release
dotnet run --project tools\ueexplorer-mcp\ueexplorer-mcp.csproj --configuration Release
```

Object search uses UModel because Dishonored's cooked UPK files are compressed;
UELib can read their headers but stops before loading the object tables. Script
decompilation therefore reports this limitation for those compressed packages.
Set `UMODEL_PATH` if UModel is installed somewhere else.

The server speaks MCP over stdio. Register it in Codex's MCP configuration:

```toml
[mcp_servers.ue_explorer]
command = "dotnet"
args = ["E:\\Dishonored Reverse Engineering\\tools\\ueexplorer-mcp\\bin\\Release\\net8.0\\ueexplorer-mcp.dll"]
enabled = true
startup_timeout_sec = 30

[mcp_servers.ue_explorer.env]
DISHONORED_GAME_ROOT = "E:\\Dishonored Reverse Engineering\\Dishonored RHCP"
NUGET_PACKAGES = "E:\\Dishonored Reverse Engineering\\.nuget\\packages"
UMODEL_PATH = "E:\\Dishonored Reverse Engineering\\third_party\\ueviewer-gildor\\umodel.exe"
```

Restart Codex after adding the server. Example package path: `DishonoredGame\CookedPCConsole\DishonoredGame.upk`.

## Scope

This provides direct package and script access through UELib. It does not automate the desktop window or its file dialog. Package writing, game modification, process control, and unrestricted filesystem access are not exposed.

Library: https://github.com/EliotVU/Unreal-Library
