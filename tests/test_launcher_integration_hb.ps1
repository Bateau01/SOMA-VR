$ErrorActionPreference='Stop'
$r=Split-Path $PSScriptRoot -Parent
. (Join-Path $r 'runtime\SOMA-VR-Settings.ps1')
$work=Join-Path $r ('audit\settings-'+[guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($work)
foreach($name in @('Default_user_settings.cfg','Player_123_user_settings.cfg')){
 [IO.File]::WriteAllText((Join-Path $work $name),'<Input SmoothMouse="true" InvertMouse="true" /><Screen Width="1936" Height="1067" RefreshRate="60"/><Other Keep="yes"/>')
}
function Get-SomaVrMonitorSize {param($MonitorIndex);[pscustomobject]@{Width=3440;Height=1440;RefreshRate=180;Device='TEST MONITOR'}}
Repair-SomaVrSettings -GameDirectory $work -SettingsDirectory $work | Out-Null
foreach($p in Get-ChildItem $work -Filter '*user_settings.cfg'){
 [xml]$xml='<Root>'+[IO.File]::ReadAllText($p.FullName)+'</Root>'
 if($xml.Root.Screen.RefreshRate -ne '180' -or $xml.Root.Screen.Width -ne '3440' -or $xml.Root.Input.SmoothMouse -ne 'false' -or $xml.Root.Input.InvertMouse -ne 'true' -or $xml.Root.Other.Keep -ne 'yes'){throw 'Saved profile verification failed'}
}
if(@(Get-ChildItem $work -Filter '*.vr-backup-*').Count -ne 2){throw 'Backups missing'}
Repair-SomaVrSettings -GameDirectory $work -SettingsDirectory $work | Out-Null
if(@(Get-ChildItem $work -Filter '*.vr-backup-*').Count -ne 2){throw 'Idempotent run wrote new backups'}
Write-Output 'PASS default and named profile writes, backups, verification and idempotent launch; real user settings untouched.'

# Real process termination, isolated to one disposable test executable.
$t=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $r 'runtime\Launch-SOMA-VR.ps1'),[ref]$t,[ref]$errors)
$fn=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Stop-SomaInstances'},$true)
Invoke-Expression $fn.Extent.Text
$exe=Join-Path $work 'SomaStopProbe.exe'
Add-Type -TypeDefinition 'public class SomaStopProbe { public static void Main(){ System.Threading.Thread.Sleep(60000); } }' -OutputAssembly $exe -OutputType ConsoleApplication
$script:probe=Start-Process -FilePath $exe -WindowStyle Hidden -PassThru
$script:probeId=$script:probe.Id
function Get-SomaProcesses {
 $found=Get-Process -Id $script:probeId -ErrorAction SilentlyContinue
 if($found){$found}
}
try {
 Stop-SomaInstances -Force
 $check=Get-Process -Id $script:probeId -ErrorAction SilentlyContinue
 if($check){throw 'Probe survived'}
 Write-Output 'PASS actual forced termination of isolated disposable process; no game/Steam processes targeted.'
} finally {
 $remaining=Get-Process -Id $script:probeId -ErrorAction SilentlyContinue
 if($remaining -and $remaining.ProcessName -eq 'SomaStopProbe'){$remaining.Kill()}
}
