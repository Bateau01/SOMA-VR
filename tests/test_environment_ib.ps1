param([switch]$Large,[string]$Runtime='')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
if(!$Runtime){$Runtime=Join-Path $root 'runtime'}
if($Large){for($i=0;$i -lt 40;$i++){[Environment]::SetEnvironmentVariable(('SOMA_TEST_'+$i),('x'*8000),'Process')}}
function Snapshot { $v=[Environment]::GetEnvironmentVariables(); @($v.Keys | Sort-Object | ForEach-Object { $_+'='+$v[$_] }) -join "`n" }
$before=Snapshot
# Read-only compilation of the baseline helper confirms the same failure.
$baselineFailed=$false
try { Add-Type -TypeDefinition ((Get-Content "$root\launcher\source\Helper0.cs" -Raw).Replace('SomaVrLaunch','BaselineLaunch')) } catch {
 if(!$Large -or $_.Exception.Message -notmatch '65535'){throw}
 $baselineFailed=$true
}
if($Large -and !$baselineFailed){throw 'Oversized baseline unexpectedly passed'}
Add-Type -Path "$Runtime\SOMA-VR-LaunchSupport.dll"
. "$Runtime\SOMA-VR-Settings.ps1"
$monitor=Get-SomaVrMonitorSize
if($monitor.Width -lt 640 -or $monitor.Height -lt 480){throw 'Invalid monitor'}
$si=New-Object SomaVrLaunch+STARTUPINFO
$si.cb=[Runtime.InteropServices.Marshal]::SizeOf($si)
$pi=New-Object SomaVrLaunch+PROCESS_INFORMATION
$exe=Join-Path $env:SystemRoot 'System32\cmd.exe'
$command=New-Object Text.StringBuilder
[void]$command.Append(('"'+$exe+'" /d /c exit 0'))
if(![SomaVrLaunch]::CreateProcessW($exe,$command,[IntPtr]::Zero,[IntPtr]::Zero,$false,0x08000004,[IntPtr]::Zero,$root,[ref]$si,[ref]$pi)){throw 'CreateProcessW failed'}
try {
 $proc=Get-Process -Id $pi.pid
 if([SomaVrLaunch]::ResumeThread($pi.thread) -eq [uint32]::MaxValue){throw 'Resume failed'}
 if(!$proc.WaitForExit(5000)){[void][SomaVrLaunch]::TerminateProcess($pi.process,1);throw 'Child timed out'}
}finally{[void][SomaVrLaunch]::CloseHandle($pi.thread);[void][SomaVrLaunch]::CloseHandle($pi.process)}
$info=New-Object Diagnostics.ProcessStartInfo
$info.FileName=$exe;$info.Arguments='/d /c echo CHILD_OK'
$info.UseShellExecute=$false;$info.CreateNoWindow=$true
$info.RedirectStandardInput=$true;$info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
$helper=[Diagnostics.Process]::Start($info)
try{$helper.StandardInput.Close();$output=$helper.StandardOutput.ReadToEnd();$helper.WaitForExit();if($helper.ExitCode -ne 0 -or $output -notmatch 'CHILD_OK'){throw 'Redirected child failed'}}finally{$helper.Dispose()}
if((Snapshot) -cne $before){throw 'Environment modified'}
@{large=[bool]$Large;baselineRejected=$baselineFailed;monitor=$monitor;helperLoad='pass';suspendedResume='pass';redirectedProcess='pass';environmentUnchanged=$true} | ConvertTo-Json -Depth 4
