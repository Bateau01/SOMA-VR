$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$testRoot=Join-Path $root 'build\delivery-ia-final'
New-Item -ItemType Directory -Path $testRoot -Force | Out-Null
$setup=Join-Path $root 'installer\output\SOMA-VR-1.0.9-S26IA-Setup.exe'
$assembly=[Reflection.Assembly]::LoadFile($setup)
$stream=$assembly.GetManifestResourceStream('payload.zip')
$embedded=Join-Path $testRoot 'embedded.zip'
$out=[IO.File]::Open($embedded,[IO.FileMode]::Create)
try{$stream.CopyTo($out)}finally{$out.Dispose();$stream.Dispose()}
Add-Type -AssemblyName System.IO.Compression.FileSystem
$payload=Join-Path $testRoot 'embedded-payload'
if(Test-Path -LiteralPath $payload){throw 'Use a fresh delivery test directory'}
[IO.Compression.ZipFile]::ExtractToDirectory($embedded,$payload)
$baseline=Join-Path $testRoot 'baseline-payload'
[IO.Compression.ZipFile]::ExtractToDirectory('C:\Users\BateauPC\.codex\visualizations\2026\09\10\01a08a5d-ef11-7e72-946a-520c0112c85c\SOMA_VR_108_S26HQ_COMBINED_MIRROR\repo\installer\payload.zip',$baseline)
$compiler=Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$testManifest=Join-Path $testRoot 'test.manifest'
(Get-Content (Join-Path $root 'installer\source\installer.manifest') -Raw).Replace('requireAdministrator','asInvoker') | Set-Content $testManifest
$results=@()
foreach($name in @('FullTests','CurrentUpgradeTests','TransactionTests','UpdaterTests')){
 $exe=Join-Path $testRoot ($name+'.exe')
 & $compiler /nologo /target:exe /platform:x64 /optimize+ /main:$name /out:$exe /win32manifest:$testManifest /r:System.Windows.Forms.dll /r:System.Drawing.dll /r:System.Web.Extensions.dll /r:System.IO.Compression.dll /r:System.IO.Compression.FileSystem.dll (Join-Path $root 'installer\source\Installer.cs') (Join-Path $root ('installer\source\'+$name+'.cs'))
 if($LASTEXITCODE){throw "Compile failed $name"}
 $install=Join-Path $testRoot ('Install space é '+$name)
 $testArgs=@($install,$payload)
 if($name -eq 'CurrentUpgradeTests'){$testArgs=@($install,$baseline,$payload)}
 if($name -eq 'UpdaterTests'){$testArgs+= 'C:\Program Files\Epic Games\SOMA\Soma.exe'}
 & $exe @testArgs > (Join-Path $testRoot ($name+'.log')) 2>&1
 $rc=$LASTEXITCODE
 $results+=@{test=$name;exit=$rc;log=($name+'.log')}
 $results | ConvertTo-Json | Set-Content (Join-Path $root 'docs\v109-evidence\installer_delivery_ia.json')
 if($rc){throw "Test failed $name"}
 Write-Output "PASS $name"
}
$manifest=Get-Content (Join-Path $payload 'installer-manifest.json') -Raw | ConvertFrom-Json
foreach($entry in $manifest.Files.PSObject.Properties){
 $path=Join-Path $payload $entry.Name
 if((Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant() -ne $entry.Value){throw "Payload hash mismatch $($entry.Name)"}
 if($entry.Name -match 'capture_swap|stack_snapshot|hy_frame|(^|/)(AGENTS|CLAUDE)\.md$|RELEASE.NOTES|\.flag$|stutter.*\.bin$'){throw "Unexpected packaged file $($entry.Name)"}
}
$update=Get-Content (Join-Path $root 'installer\output\SOMA-VR-update.json') -Raw | ConvertFrom-Json
if($update.sha256 -ne (Get-FileHash $setup).Hash.ToLowerInvariant() -or $update.size -ne (Get-Item $setup).Length -or $update.version -ne $manifest.Version){throw 'Update manifest mismatch'}
Write-Output "PASS embedded payload identity, file hashes, exclusions and update metadata"




