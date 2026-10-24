$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$compiler=Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
& $compiler /nologo /target:library /optimize+ /out:"$root\runtime\SOMA-VR-LaunchSupport.dll" "$PSScriptRoot\Helper0.cs" "$PSScriptRoot\Helper1.cs"
if($LASTEXITCODE){throw 'Launcher helper compilation failed'}
