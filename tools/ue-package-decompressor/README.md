# Gildor UE3 package decompressor

`decompress.exe` is built from the official [UEViewer](https://github.com/gildor2/UEViewer) source tree, project `Tools/PackageUnpack`.

- Source commit: `a0bfb468d42be831b126632fd8a0ae6b3614f981`
- Target: x86 Windows, Visual Studio 2022 Build Tools 14.44
- SHA-256: `A724FFD162C1D14D167FE0DA32769EFD15486A7DB96AB4CA8CD1C2FFF8CECBFE`
- License: see [UEViewer-LICENSE.txt](UEViewer-LICENSE.txt)

Build the source project using UEViewer's `Tools/PackageUnpack/decompress.project` and its `Tools/genmake`/MSVC build workflow. This binary was built with the upstream-generated NMake project; optional Oodle support was absent from the source checkout and is not enabled. UE3 LZO, LZX, and zlib code is built in.

Example read-only use (the input package is never overwritten):

```powershell
.\decompress.exe -game=dis `
  '-path=E:\Dishonored Reverse Engineering\Dishonored RHCP\DishonoredGame\CookedPCConsole' `
  '-out=E:\Dishonored Reverse Engineering\assets\extracted\dishonored-blink' `
  DishonoredGame.upk
```

The decompressed package belongs under ignored `assets/extracted/`; it contains game data and must not be committed.
