# Read-only PE comparison. No signature scanning, address guessing, or game mutation.
function Get-SomaLaunchReport([string]$Path, [string]$ReferencePath) {
    $report = Get-SomaExecutableReport $Path $ReferencePath
    $dllName = 'hpl3vr.dll'
    $edition = 'Steam engine layout'
    if ($report.sha256 -eq '395cd54830c8e66e22166e71ac6fe95fd3bb5433b898737836744a6d178a0a6a') {
        # Exact executable identity selects a separately compiled native port.
        # Do not accept a merely similar layout against the Steam reference.
        $report.status = 'VerifiedExecutable'
        $report.differences = @()
        $report.scope = 'Exact Epic/GOG executable identity. Runtime validation is separate from this check.'
        $dllName = 'hpl3vr-store.dll'
        $edition = 'Epic / GOG engine layout'
    }
    $report | Add-Member -NotePropertyName runtime_dll -NotePropertyValue $dllName
    $report | Add-Member -NotePropertyName edition -NotePropertyValue $edition
    return $report
}
function Get-SomaSha256([byte[]]$Bytes) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash($Bytes))).Replace('-','').ToLowerInvariant() }
    finally { $sha.Dispose() }
}
function Get-SomaExecutableReport([string]$Path, [string]$ReferencePath) {
    $reference = Get-Content -LiteralPath $ReferencePath -Raw | ConvertFrom-Json
    if ($reference.schema -ne 1) { throw 'Unsupported SOMA executable reference schema.' }
    $file = Get-Item -LiteralPath $Path
    if ($file.Length -lt 256 -or $file.Length -gt 536870912) { throw 'Invalid SOMA executable size.' }
    [byte[]]$bytes = [IO.File]::ReadAllBytes($file.FullName)
    $whole = Get-SomaSha256 $bytes
    if ($bytes[0] -ne 77 -or $bytes[1] -ne 90) { throw 'Not a Windows executable (missing MZ header).' }
    [long]$pe = [BitConverter]::ToUInt32($bytes,60)
    if ($pe -gt $bytes.Length-24 -or [BitConverter]::ToUInt32($bytes,[int]$pe) -ne 17744) { throw 'Invalid PE header.' }
    $machine = [BitConverter]::ToUInt16($bytes,[int]$pe+4)
    $count = [BitConverter]::ToUInt16($bytes,[int]$pe+6)
    $characteristics = [BitConverter]::ToUInt16($bytes,[int]$pe+22)
    $optionalSize = [BitConverter]::ToUInt16($bytes,[int]$pe+20)
    [long]$optional = $pe+24
    [long]$table = $optional+$optionalSize
    if ($count -lt 1 -or $count -gt 96 -or $optionalSize -lt 240 -or $table+40*$count -gt $bytes.Length) { throw 'Invalid PE section layout.' }
    if ($machine -ne 34404 -or [BitConverter]::ToUInt16($bytes,[int]$optional) -ne 523) { throw 'This VR DLL requires a 64-bit x86 SOMA executable.' }
    [byte[]]$header = New-Object byte[] $optionalSize
    [Array]::Copy($bytes,$optional,$header,0,$optionalSize)
    # Checksum and certificate-table location do not change mapped engine addresses.
    [Array]::Clear($header,64,4); [Array]::Clear($header,144,8)
    $optionalHash = Get-SomaSha256 $header
    $differences = New-Object 'Collections.Generic.List[string]'
    if ($machine -ne $reference.machine) { $differences.Add('Machine architecture') }
    if ($characteristics -ne $reference.characteristics) { $differences.Add('PE characteristics') }
    if ($optionalHash -ne $reference.optional_header_sha256) { $differences.Add('Mapped image/entry point/import/relocation directory layout') }
    if ($count -ne $reference.sections.Count) { $differences.Add('Section count') }
    $sections = @()
    for ($i=0; $i -lt $count; $i++) {
        [int]$at = $table+40*$i
        $name = [Text.Encoding]::ASCII.GetString($bytes,$at,8).TrimEnd([char]0)
        $rva = [BitConverter]::ToUInt32($bytes,$at+12)
        $virtualSize = [BitConverter]::ToUInt32($bytes,$at+8)
        [long]$rawSize = [BitConverter]::ToUInt32($bytes,$at+16)
        [long]$rawOffset = [BitConverter]::ToUInt32($bytes,$at+20)
        if ($rawOffset+$rawSize -gt $bytes.Length) { throw "Truncated PE section: $name" }
        [byte[]]$sectionHeader = New-Object byte[] 40
        [Array]::Copy($bytes,$at,$sectionHeader,0,40)
        $headerHash = Get-SomaSha256 $sectionHeader
        $contentHash = $null
        if ($name -ne '.rsrc') {
            [byte[]]$content = New-Object byte[] ([int]$rawSize)
            [Array]::Copy($bytes,$rawOffset,$content,0,$rawSize)
            $contentHash = Get-SomaSha256 $content
        }
        $sections += [ordered]@{ name=$name; rva=$rva; virtual_size=$virtualSize; raw_size=$rawSize; raw_offset=$rawOffset; header_sha256=$headerHash; sha256=$contentHash }
        if ($i -lt $reference.sections.Count) {
            $expected = $reference.sections[$i]
            if ($name -ne $expected.name -or $headerHash -ne $expected.header_sha256) { $differences.Add("Section $i layout ($name)") }
            if ($contentHash -ne $expected.sha256) { $differences.Add("Section $i engine bytes ($name)") }
        }
    }
    $status = 'Incompatible'
    if ($whole -eq $reference.sha256) { $status = 'VerifiedExecutable' }
    elseif ($differences.Count -eq 0) { $status = 'EquivalentEngineUnverified' }
    return [pscustomobject][ordered]@{
        schema=1; executable=$file.Name; sha256=$whole; bytes=$bytes.Length; machine=$machine
        status=$status; differences=@($differences.ToArray()); optional_header_sha256=$optionalHash; sections=$sections
        scope='Executable comparison only. GOG/Epic gameplay, dependencies and script versions are not validated.'
    }
}
