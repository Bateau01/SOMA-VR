param([string]$GameArguments = '', [switch]$CheckOnly, [switch]$StopOnly, [string]$Executable = '', [switch]$Experimental, [switch]$SkipSettingsRepair, [switch]$KeepSSAO, [int]$MonitorIndex = -1, [string]$SettingsPath = '', [string]$SettingsDirectory = '')
$ErrorActionPreference = 'Stop'
# Elevate before cleanup, config writes or injection. SOMA and the injector
# inherit this token. Serialize arguments as data rather than executable text.
$launchIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
$launchPrincipal = New-Object Security.Principal.WindowsPrincipal($launchIdentity)
if (!$launchPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    $forward = @{}
    foreach ($key in $PSBoundParameters.Keys) {
        $value = $PSBoundParameters[$key]
        if ($value -is [Management.Automation.SwitchParameter]) { $value = [bool]$value }
        $forward[$key] = $value
    }
    $packet = @{ Script=$PSCommandPath; Parameters=$forward; OwnerSid=$launchIdentity.User.Value }
    $data = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes([Management.Automation.PSSerializer]::Serialize($packet)))
    $bootstrap = @'
$ErrorActionPreference = 'Stop'
try {
    $packet = [Management.Automation.PSSerializer]::Deserialize([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('__DATA__')))
    if ([Security.Principal.WindowsIdentity]::GetCurrent().User.Value -ne $packet.OwnerSid) {
        throw 'Approve administrator access for the same Windows account. A different account would use different SOMA saves, settings and VR runtime registration.'
    }
    $arguments = $packet.Parameters
    & $packet.Script @arguments
    exit 0
} catch {
    Write-Host $_ -ForegroundColor Red
    [void](Read-Host 'Press Enter to close')
    exit 1
}
'@
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($bootstrap.Replace('__DATA__',$data)))
    try {
        $child = Start-Process -FilePath (Join-Path $PSHOME 'powershell.exe') -Verb RunAs -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-EncodedCommand',$encoded) -PassThru -Wait
        exit $child.ExitCode
    } catch {
        throw ('Administrator approval is required to start SOMA VR. No game was started by this launcher. ' + $_.Exception.Message)
    }
}
# Use the Windows PowerShell modules even when a parent shell supplied a PowerShell 7 module path.
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Utility')
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Management')
function Stop-SomaInstances {
    # Limit cleanup to the two game executable names; never stop Steam or the VR runtime.
    $instances = @(Get-Process -Name Soma,Soma_NoSteam -ErrorAction SilentlyContinue)
    foreach ($instance in $instances) {
        try {
            if ($instance.HasExited) { continue }
            Write-Output ('Closing existing SOMA process ' + $instance.Id + '...')
            # Give the game a short opportunity to shut down normally before clearing an orphan.
            if ($instance.MainWindowHandle -ne [IntPtr]::Zero) {
                [void]$instance.CloseMainWindow()
                [void]$instance.WaitForExit(3000)
            }
            if (!$instance.HasExited) {
                $instance.Kill()
                if (!$instance.WaitForExit(5000)) { throw 'The process did not exit within five seconds.' }
            }
        } catch {
            if (!$instance.HasExited) {
                throw ('Could not close SOMA process ' + $instance.Id + ': ' + $_.Exception.Message + ' Close it in Task Manager, or run the launcher with the same permissions as that process.')
            }
        } finally { $instance.Dispose() }
    }
}
if ($CheckOnly -and $StopOnly) { throw 'Choose either -CheckOnly or -StopOnly.' }
if ($StopOnly) { Stop-SomaInstances; Write-Output 'SOMA process cleanup completed.'; exit 0 }
$gameDir = $PSScriptRoot
if (!$Executable) {
    if (Test-Path -LiteralPath (Join-Path $gameDir 'Soma.exe')) { $Executable = 'Soma.exe' }
    elseif (Test-Path -LiteralPath (Join-Path $gameDir 'Soma_NoSteam.exe')) { $Executable = 'Soma_NoSteam.exe' }
    else { throw 'No Soma.exe or Soma_NoSteam.exe found beside this launcher.' }
}
if ($Executable -notin @('Soma.exe','Soma_NoSteam.exe')) { throw 'Choose Soma.exe or Soma_NoSteam.exe in this game folder; do not rename another program.' }
$exe = Join-Path $gameDir $Executable
$injector = Join-Path $gameDir 'hpl3vr_inject.exe'
foreach ($p in @($exe,$injector,(Join-Path $gameDir 'openxr_loader.dll'))) {
    if (!(Test-Path -LiteralPath $p -PathType Leaf)) { throw "Missing $p. Extract the full mod into the folder containing Soma.exe." }
}
. (Join-Path $gameDir 'SOMA-VR-Compatibility.ps1')
$report = Get-SomaLaunchReport $exe (Join-Path $gameDir 'SOMA-VR-Executable.json')
$dllName = $report.runtime_dll
$dll = Join-Path $gameDir $dllName
if (!(Test-Path -LiteralPath $dll -PathType Leaf)) { throw "Missing $dll. Reinstall the complete VR mod for this edition." }
$reportPath = Join-Path $gameDir 'SOMA-VR-compatibility-report.json'
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $reportPath -Encoding UTF8
Write-Output ('Executable status: ' + $report.status)
Write-Output ('Native runtime: ' + $report.edition + ' (' + $dllName + ')')
Write-Output ('Compatibility report: ' + $reportPath)
if ($report.status -eq 'Incompatible') {
    throw ('This executable needs a native VR port; its engine layout differs from the tested build. No injection attempted. Send SOMA-VR-compatibility-report.json with the storefront/version. Differences: ' + ($report.differences -join '; '))
}
if ($CheckOnly) { Write-Output 'Executable checks completed. No game was started; no settings were changed.'; exit 0 }
if ($report.status -ne 'VerifiedExecutable') {
    if (!$Experimental) { throw 'Engine bytes/layout match, but this executable is untested. Use Launch-SOMA-VR.cmd -Experimental to opt into this limited compatibility test.' }
    Write-Warning 'Experimental executable: engine bytes/layout match, but storefront dependencies, scripts and gameplay are untested.'
}
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Text;
public static class SomaVrLaunch {
 [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
 public struct STARTUPINFO { public int cb; public string reserved,desktop,title; public int x,y,cx,cy,xc,yc,fill,flags; public short show,reserved2; public IntPtr reservedPtr,stdin,stdout,stderr; }
 [StructLayout(LayoutKind.Sequential)]
 public struct PROCESS_INFORMATION { public IntPtr process,thread; public uint pid,tid; }
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)]
 [return:MarshalAs(UnmanagedType.Bool)]
 public static extern bool CreateProcessW(string application,StringBuilder command,IntPtr pa,IntPtr ta,bool inherit,uint flags,IntPtr env,string directory,ref STARTUPINFO si,out PROCESS_INFORMATION pi);
 [DllImport("kernel32.dll",SetLastError=true)] public static extern uint ResumeThread(IntPtr thread);
 [DllImport("kernel32.dll")] public static extern bool CloseHandle(IntPtr handle);
 [DllImport("kernel32.dll")] public static extern bool TerminateProcess(IntPtr process,uint code);
}
'@
Stop-SomaInstances
if (!$SettingsPath -and !$SettingsDirectory) {
    $optionFile = Join-Path $gameDir 'SOMA-VR-Install-Options.json'
    if (Test-Path -LiteralPath $optionFile -PathType Leaf) {
        $options = Get-Content -LiteralPath $optionFile -Raw | ConvertFrom-Json
        if ($options.OwnerSid -eq [Security.Principal.WindowsIdentity]::GetCurrent().User.Value) {
            $SettingsDirectory = [string]$options.SettingsDirectory
        }
    }
}
if (!$SkipSettingsRepair) {
    if ($GameArguments -and !$SettingsPath) { throw 'Custom game arguments require -SettingsPath for the intended profile, or -SkipSettingsRepair.' }
    . (Join-Path $gameDir 'SOMA-VR-Settings.ps1')
    Repair-SomaVrSettings -GameDirectory $gameDir -SettingsPath $SettingsPath -SettingsDirectory $SettingsDirectory -MonitorIndex $MonitorIndex -KeepSSAO:$KeepSSAO
}
$settings = Join-Path $gameDir 'hpl3vr_vr_settings.ini'
if (!(Test-Path -LiteralPath $settings)) {
    Copy-Item -LiteralPath (Join-Path $gameDir 'defaults\hpl3vr_vr_settings.ini') -Destination $settings
}
$calibration = Join-Path $gameDir 'hpl3vr_hand_calibration.ini' 
if (!(Test-Path -LiteralPath $calibration)) {
    Copy-Item -LiteralPath (Join-Path $gameDir 'defaults\hpl3vr_hand_calibration.ini') -Destination $calibration
}
$si = New-Object SomaVrLaunch+STARTUPINFO
$si.cb = [Runtime.InteropServices.Marshal]::SizeOf($si)
$pi = New-Object SomaVrLaunch+PROCESS_INFORMATION
$command = New-Object Text.StringBuilder
[void]$command.Append('"' + $exe + '"')
if ($GameArguments) { [void]$command.Append(' ' + $GameArguments) }
if (![SomaVrLaunch]::CreateProcessW($exe,$command,[IntPtr]::Zero,[IntPtr]::Zero,$false,4,[IntPtr]::Zero,$gameDir,[ref]$si,[ref]$pi)) {
    throw (New-Object ComponentModel.Win32Exception([Runtime.InteropServices.Marshal]::GetLastWin32Error()))
}
$resumed = $false
try {
    $info = New-Object Diagnostics.ProcessStartInfo
    $info.FileName = $injector
    $info.Arguments = $Executable + ' ' + $dllName
    $info.WorkingDirectory = $gameDir
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardInput = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $helper = [Diagnostics.Process]::Start($info)
    try {
        $helper.StandardInput.WriteLine(''); $helper.StandardInput.Close()
        if (!$helper.WaitForExit(25000)) { $helper.Kill(); throw 'The VR injector timed out.' }
        $output = $helper.StandardOutput.ReadToEnd() + $helper.StandardError.ReadToEnd()
        if ($helper.ExitCode -ne 0 -or $output -notmatch 'SUCCESS') { throw "VR injection failed: $output" }
    } finally { $helper.Dispose() }
    if ([SomaVrLaunch]::ResumeThread($pi.thread) -eq [uint32]::MaxValue) { throw 'Could not resume SOMA after loading VR.' }
    $resumed = $true
    Write-Output ('SOMA_VR_PID=' + $pi.pid)
} finally {
    if (!$resumed) { [void][SomaVrLaunch]::TerminateProcess($pi.process,1) }
    [void][SomaVrLaunch]::CloseHandle($pi.thread)
    [void][SomaVrLaunch]::CloseHandle($pi.process)
}

