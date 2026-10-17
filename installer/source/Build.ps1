$ErrorActionPreference = 'Stop'
$base = Split-Path $PSScriptRoot -Parent
$payload = Join-Path $base 'payload'
$updateVersion=Get-Content -LiteralPath (Join-Path $payload 'SOMA-VR-Update-Version.json') -Raw | ConvertFrom-Json
if ($updateVersion.version -ne '1.0.8-S26HQ' -or [long]$updateVersion.build -ne 2026101615) { throw 'Updater version does not match this installer build.' }
$hashes = @{}
foreach ($f in Get-ChildItem $payload -Recurse -File) {
    if ($f.Name -eq 'installer-manifest.json') { continue }
    $rel = $f.FullName.Substring($payload.Length + 1).Replace('\','/')
    $hashes[$rel] = (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
}
@{Build=2026101615;Version='1.0.8-S26HQ';Files=$hashes} | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $payload 'installer-manifest.json') -Encoding UTF8
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = Join-Path $base 'payload.zip'
if (Test-Path -LiteralPath $archive) { Remove-Item -LiteralPath $archive }
[IO.Compression.ZipFile]::CreateFromDirectory($payload,$archive,[IO.Compression.CompressionLevel]::Optimal,$false)
$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
& $compiler /nologo /target:winexe /platform:x64 /optimize+ /out:"$base\output\SOMA-VR-1.0.8-S26HQ-Setup.exe" /win32icon:"$base\art\soma.ico" /win32manifest:"$PSScriptRoot\installer.manifest" /resource:"$archive,payload.zip" /resource:"$base\art\title.png,title.png" /resource:"$base\art\background.png,background.png" /r:System.Windows.Forms.dll /r:System.Drawing.dll /r:System.Web.Extensions.dll /r:System.IO.Compression.dll /r:System.IO.Compression.FileSystem.dll "$PSScriptRoot\Installer.cs"
if ($LASTEXITCODE) { throw 'Compiler failed.' }
Get-FileHash "$base\output\SOMA-VR-1.0.8-S26HQ-Setup.exe"



$setup=Join-Path $base 'output\SOMA-VR-1.0.8-S26HQ-Setup.exe'
@{schema=1;product='SOMA-VR';protocol=1;version='1.0.8-S26HQ';build=2026101615;asset=[IO.Path]::GetFileName($setup);size=(Get-Item -LiteralPath $setup).Length;sha256=(Get-FileHash -LiteralPath $setup -Algorithm SHA256).Hash.ToLowerInvariant()} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $base 'output\SOMA-VR-update.json') -Encoding UTF8
