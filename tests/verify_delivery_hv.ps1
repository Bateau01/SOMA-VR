$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$testRoot=Join-Path $root 'build/delivery-hv-final'
$payload=Join-Path $testRoot 'embedded-payload'
$setup=Join-Path $root 'installer/output/SOMA-VR-1.0.9-S26HV-Setup.exe'
$manifest=Get-Content (Join-Path $payload 'installer-manifest.json') -Raw | ConvertFrom-Json
foreach($entry in $manifest.Files.PSObject.Properties){
 $path=Join-Path $payload $entry.Name
 if((Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant() -ne $entry.Value){throw "Payload hash mismatch $($entry.Name)"}
 if($entry.Name -match '(^|/)(AGENTS|CLAUDE)\.md$|RELEASE.NOTES|\.flag$|stutter.*\.bin$'){throw "Unexpected packaged file $($entry.Name)"}
}
$update=Get-Content (Join-Path $root 'installer\output\SOMA-VR-update.json') -Raw | ConvertFrom-Json
if($update.sha256 -ne (Get-FileHash $setup).Hash.ToLowerInvariant() -or $update.size -ne (Get-Item $setup).Length -or $update.version -ne $manifest.Version){throw 'Update manifest mismatch'}
Write-Output "PASS embedded payload identity, file hashes, exclusions and update metadata"



