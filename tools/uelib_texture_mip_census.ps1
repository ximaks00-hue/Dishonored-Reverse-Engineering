param(
    [Parameter(Mandatory = $true)] [string] $PackagePath,
    [Parameter(Mandatory = $true)] [string] $TextureFileCachePath,
    [Parameter(Mandatory = $true)] [int] $PackageIndex,
    [Parameter(Mandatory = $true)] [string] $UelibAssemblyPath,
    [Parameter(Mandatory = $true)] [string] $OutputCsv,
    [Parameter(Mandatory = $true)] [string] $SummaryJson,
    [string] $ClassAliasName,
    [string] $ClassAliasImplementationType
)

$ErrorActionPreference = 'Stop'
Add-Type -Path (Resolve-Path -LiteralPath $UelibAssemblyPath).Path

function Get-RangeDigest {
    param([string] $Path, [long] $Offset, [long] $Count)
    if ($Offset -lt 0 -or $Count -lt 0 -or $Count -gt [int]::MaxValue) {
        throw "Invalid byte range: $Path offset=$Offset size=$Count"
    }
    $stream = [System.IO.File]::OpenRead($Path)
    try {
        if ($Offset + $Count -gt $stream.Length) {
            throw "Byte range outside file: $Path offset=$Offset size=$Count length=$($stream.Length)"
        }
        [void] $stream.Seek($Offset, [System.IO.SeekOrigin]::Begin)
        $bytes = [byte[]]::new([int]$Count)
        $stream.ReadExactly($bytes, 0, $bytes.Length)
        return [System.Convert]::ToHexString([System.Security.Cryptography.SHA256]::HashData($bytes))
    }
    finally {
        $stream.Dispose()
    }
}

$packagePathFull = (Resolve-Path -LiteralPath $PackagePath).Path
$tfcPathFull = (Resolve-Path -LiteralPath $TextureFileCachePath).Path
$packageHash = (Get-FileHash -LiteralPath $packagePathFull -Algorithm SHA256).Hash.ToUpperInvariant()
$tfcHash = (Get-FileHash -LiteralPath $tfcPathFull -Algorithm SHA256).Hash.ToUpperInvariant()
$package = [UELib.UnrealLoader]::LoadPackage($packagePathFull, [System.IO.FileAccess]::Read)
try {
    if ([string]::IsNullOrWhiteSpace($ClassAliasName) -xor [string]::IsNullOrWhiteSpace($ClassAliasImplementationType)) {
        throw 'ClassAliasName and ClassAliasImplementationType must be supplied together.'
    }
    if (-not [string]::IsNullOrWhiteSpace($ClassAliasName)) {
        $aliasType = [UELib.Engine.UTexture2D].Assembly.GetType($ClassAliasImplementationType, $false)
        if ($null -eq $aliasType -or -not $aliasType.IsSubclassOf([UELib.Engine.UTexture2D])) {
            throw "Class alias implementation must derive from UELib.Engine.UTexture2D: $ClassAliasImplementationType"
        }
        $package.AddClassType($ClassAliasName, $aliasType)
    }
    $package.InitializePackage()
    $texture = @($package.Objects | Where-Object { $_.PackageIndex.Index -eq $PackageIndex })
    if ($texture.Count -ne 1) { throw "Expected one object at package index $PackageIndex; found $($texture.Count)" }
    $texture = $texture[0]
    if ($texture -isnot [UELib.Engine.UTexture2D]) {
        throw "Expected UTexture2D-compatible object; got $($texture.GetType().FullName)"
    }
    $texture.Load()

    $cacheProperty = @($texture.Properties | Where-Object { $_.Name.ToString() -eq 'TextureFileCacheName' })
    if ($cacheProperty.Count -ne 1) { throw "Expected one TextureFileCacheName property; found $($cacheProperty.Count)" }
    $cacheName = ([string]$cacheProperty[0].Value).Trim('"')
    if ([System.IO.Path]::GetFileNameWithoutExtension($tfcPathFull) -ne $cacheName) {
        throw "Cache basename mismatch: property=$cacheName file=$([System.IO.Path]::GetFileNameWithoutExtension($tfcPathFull))"
    }

    $serializedWidth = @($texture.Properties | Where-Object { $_.Name.ToString() -eq 'SizeX' })
    $serializedHeight = @($texture.Properties | Where-Object { $_.Name.ToString() -eq 'SizeY' })
    $serializedFormat = @($texture.Properties | Where-Object { $_.Name.ToString() -eq 'Format' })
    if ($serializedWidth.Count -gt 1 -or $serializedHeight.Count -gt 1 -or $serializedFormat.Count -gt 1) {
        throw 'Expected at most one serialized SizeX, SizeY, and Format property.'
    }
    $serializedPropertyRows = [System.Collections.Generic.List[object]]::new()
    foreach ($property in $texture.Properties) {
        $serializedValue = if ($null -eq $property.Value) { $null } else { $property.Value.ToString() }
        $serializedPropertyRows.Add([PSCustomObject]@{
            name = $property.Name.ToString()
            value = $serializedValue
        })
    }

    $serialOffset = [long]$texture.ExportTable.SerialOffset
    $serialSize = [long]$texture.ExportTable.SerialSize
    $serialEnd = $serialOffset + $serialSize
    $guid = $texture.TextureFileCacheGuid
    $rows = [System.Collections.Generic.List[object]]::new()
    $mipIndex = 0
    foreach ($mip in $texture.Mips) {
        $bulk = $mip.Data
        $flags = $bulk.Flags.ToString()
        $external = $flags.Contains('StoreInSeparateFile')
        $storagePath = if ($external) { $tfcPathFull } else { $packagePathFull }
        $offset = [long]$bulk.StorageOffset
        $size = [long]$bulk.StorageSize
        $end = $offset + $size
        $inFile = $offset -ge 0 -and $size -ge 0 -and $end -le (Get-Item -LiteralPath $storagePath).Length
        $withinSerial = if ($external) { $false } else { $offset -ge $serialOffset -and $end -le $serialEnd }
        $sliceHash = if ($inFile) { Get-RangeDigest -Path $storagePath -Offset $offset -Count $size } else { '' }
        $prefix = ''
        if ($inFile -and $size -gt 0) {
            $sliceStream = [System.IO.File]::OpenRead($storagePath)
            try {
                [void]$sliceStream.Seek($offset, [System.IO.SeekOrigin]::Begin)
                $prefixBytes = [byte[]]::new([int][Math]::Min(16, $size))
                $sliceStream.ReadExactly($prefixBytes, 0, $prefixBytes.Length)
                $prefix = [System.Convert]::ToHexString($prefixBytes)
            }
            finally { $sliceStream.Dispose() }
        }
        $rows.Add([PSCustomObject]@{
            package_index = $PackageIndex
            object_name = $texture.Name.ToString()
            owner_class = $texture.ExportTable.ClassName.ToString()
            mip_index = $mipIndex
            width = [uint32]$mip.SizeX
            height = [uint32]$mip.SizeY
            bulk_flags = $flags
            element_count = [int]$bulk.ElementCount
            storage_size = $size
            storage_offset = $offset
            storage_end_exclusive = $end
            storage_file = if ($external) { [System.IO.Path]::GetFileName($tfcPathFull) } else { [System.IO.Path]::GetFileName($packagePathFull) }
            range_in_file = $inFile
            inline_range_within_export_serial = $withinSerial
            slice_sha256 = $sliceHash
            slice_prefix_hex = $prefix
        })
        $mipIndex++
    }

    $outPath = [System.IO.Path]::GetFullPath($OutputCsv)
    $summaryPath = [System.IO.Path]::GetFullPath($SummaryJson)
    New-Item -ItemType Directory -Path ([System.IO.Path]::GetDirectoryName($outPath)) -Force | Out-Null
    New-Item -ItemType Directory -Path ([System.IO.Path]::GetDirectoryName($summaryPath)) -Force | Out-Null
    $rows | Export-Csv -LiteralPath $outPath -NoTypeInformation -Encoding utf8

    $externalRows = @($rows | Where-Object { $_.bulk_flags -like '*StoreInSeparateFile*' })
    $inlineRows = @($rows | Where-Object { $_.bulk_flags -notlike '*StoreInSeparateFile*' })
    $summary = [ordered]@{
        package_file = $packagePathFull
        package_sha256 = $packageHash
        package_index = $PackageIndex
        object_name = $texture.Name.ToString()
        owner_class = $texture.ExportTable.ClassName.ToString()
        parser_class_type = $texture.GetType().FullName
        serialized_texture_width = if ($serializedWidth.Count -eq 1) { [uint32]$serializedWidth[0].Value } else { $null }
        serialized_texture_height = if ($serializedHeight.Count -eq 1) { [uint32]$serializedHeight[0].Value } else { $null }
        serialized_texture_format = if ($serializedFormat.Count -eq 1) { $serializedFormat[0].Value.ToString() } else { $null }
        serialized_properties = $serializedPropertyRows
        export_serial_offset = $serialOffset
        export_serial_size = $serialSize
        export_serial_end_exclusive = $serialEnd
        texture_cache_name = $cacheName
        texture_file_cache_guid_components = [ordered]@{ A = $guid.A; B = $guid.B; C = $guid.C; D = $guid.D }
        tfc_file = $tfcPathFull
        tfc_file_size = (Get-Item -LiteralPath $tfcPathFull).Length
        tfc_file_sha256 = $tfcHash
        mip_count = $rows.Count
        external_mip_count = $externalRows.Count
        inline_mip_count = $inlineRows.Count
        all_mip_ranges_in_file = (@($rows | Where-Object { -not $_.range_in_file }).Count -eq 0)
        all_inline_ranges_within_export_serial = (@($inlineRows | Where-Object { -not $_.inline_range_within_export_serial }).Count -eq 0)
        external_mip_offsets_in_tfc = @($externalRows | ForEach-Object { $_.storage_offset })
        output_csv = $outPath
    }
    $summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $summaryPath -Encoding utf8
    $summary | ConvertTo-Json -Depth 6
}
finally {
    $package.Dispose()
}
