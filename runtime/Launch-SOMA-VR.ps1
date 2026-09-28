param([string]$GameArguments = '', [switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
# Use the Windows PowerShell modules even when a parent shell supplied a PowerShell 7 module path.
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Utility')
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Management')
$gameDir = $PSScriptRoot
$exe = Join-Path $gameDir 'Soma.exe'
$dll = Join-Path $gameDir 'hpl3vr.dll'
$injector = Join-Path $gameDir 'hpl3vr_inject.exe'
foreach ($p in @($exe,$dll,$injector,(Join-Path $gameDir 'openxr_loader.dll'))) {
    if (!(Test-Path -LiteralPath $p -PathType Leaf)) { throw "Missing $p. Extract the full mod into the folder containing Soma.exe." }
}
$expectedExe = '7c424e6055dda5b3aa41d4b3a9d6ffdebb8f4b50fa8a38769dee82d080b79113'
if ((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedExe) {
    throw 'This Soma.exe does not match the executable validated for S26BY. See SOMA_VR_README.txt; other executable builds need compatibility testing.'
}
if (Get-Process -Name Soma -ErrorAction SilentlyContinue) { throw 'SOMA is already running. Close it before using this launcher.' }
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
if ($CheckOnly) { Write-Output 'Executable and launcher checks passed. No game was started.'; exit 0 }
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
    $info.Arguments = 'Soma.exe hpl3vr.dll'
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
