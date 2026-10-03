function Get-SomaVrMonitorSize([int]$MonitorIndex = -1) {
    if (-not ('SomaVrDisplay' -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class SomaVrDisplay {
 [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
 public struct Mode {
  [MarshalAs(UnmanagedType.ByValTStr,SizeConst=32)] public string device;
  public ushort spec,driver,size,extra; public uint fields;
  public int x,y; public uint orientation,fixedOutput;
  public short color,duplex,yResolution,ttOption,collate;
  [MarshalAs(UnmanagedType.ByValTStr,SizeConst=32)] public string form;
  public ushort logPixels; public uint bits,width,height,flags,frequency;
  public uint icmMethod,icmIntent,media,dither,reserved1,reserved2,panningWidth,panningHeight;
 }
 [DllImport("user32.dll",CharSet=CharSet.Unicode)]
 public static extern bool EnumDisplaySettings(string device,int number,ref Mode mode);
}
'@
    }
    Add-Type -AssemblyName System.Windows.Forms
    $screens = @([Windows.Forms.Screen]::AllScreens)
    if ($MonitorIndex -lt -1 -or $MonitorIndex -ge $screens.Count) { throw 'Invalid monitor index. Use -1 for primary, or a zero-based monitor index.' }
    $screen = if ($MonitorIndex -eq -1) { [Windows.Forms.Screen]::PrimaryScreen } else { $screens[$MonitorIndex] }
    $mode = New-Object SomaVrDisplay+Mode
    $mode.size = [Runtime.InteropServices.Marshal]::SizeOf($mode)
    if (![SomaVrDisplay]::EnumDisplaySettings($screen.DeviceName,-1,[ref]$mode) -or $mode.width -lt 640 -or $mode.height -lt 480) { throw 'Cannot determine the selected monitor pixel resolution. No settings changed.' }
    [pscustomobject]@{ Width=[int]$mode.width; Height=[int]$mode.height; Device=$screen.DeviceName }
}

function Convert-SomaVrSettings([string]$Text,[int]$Width,[int]$Height,[bool]$KeepSSAO) {
    if ($Width -lt 640 -or $Height -lt 480 -or $Width -gt 32768 -or $Height -gt 32768) { throw 'Invalid monitor dimensions.' }
    # HPL configuration files are XML fragments, with multiple top-level elements.
    $xml = New-Object System.Xml.XmlDocument
    $xml.PreserveWhitespace = $true
    $xml.XmlResolver = $null
    $xml.LoadXml('<SomaSettings>' + $Text + '</SomaSettings>')
    $changes = @{ Screen=@{Width="$Width";Height="$Height";FullScreen='false';Vsync='false'}; Engine=@{LimitFPS='false';SleepWhenOutOfFocus='false'} }
    if (!$KeepSSAO) { $changes.Graphics = @{SSAOActive='false'} }
    foreach ($section in $changes.Keys) {
        $nodes = @($xml.DocumentElement.SelectNodes($section))
        if ($nodes.Count -gt 1) { throw "Duplicate $section configuration section; refusing to guess." }
        if ($nodes.Count -eq 0) { $node = $xml.CreateElement($section); [void]$xml.DocumentElement.AppendChild($node) } else { $node = $nodes[0] }
        foreach ($key in $changes[$section].Keys) { $node.SetAttribute($key,$changes[$section][$key]) }
    }
    $xml.DocumentElement.InnerXml
}

function Write-SomaVrSettingsPlan($Plan) {
    $directory = Split-Path -Parent $Plan.Path
    $temp = Join-Path $directory ('svr-' + [Guid]::NewGuid().ToString('N') + '.tmp')
    $stage = 'create the settings directory'
    try {
        [void][IO.Directory]::CreateDirectory($directory)
        $stage = 'write the temporary settings file'
        [IO.File]::WriteAllText($temp,$Plan.Updated,(New-Object Text.UTF8Encoding($false)))
        $stage = 'replace the settings file and retain its backup'
        if ($Plan.Exists) {
            $backup = $Plan.Path + '.vr-backup-' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfff') + '-' + [Guid]::NewGuid().ToString('N')
            [IO.File]::Replace($temp,$Plan.Path,$backup)
            Write-Output ('Original settings backed up: ' + $backup)
        } else { [IO.File]::Move($temp,$Plan.Path) }
        Write-Output ('Prepared settings: ' + $Plan.Path)
    } catch {
        $cause = $_.Exception.GetBaseException()
        $detail = 'Settings update failed while trying to ' + $stage + '. Destination: "' + $Plan.Path + '". Directory currently exists: ' + [IO.Directory]::Exists($directory) + '. Cause: ' + $cause.GetType().FullName + ' (HRESULT ' + $cause.HResult + '): ' + $cause.Message
        throw ($detail + "`nCheck Windows Security Protection history for a blocked write and whether the Documents folder is available/writable. This error alone does not prove antivirus interference. To launch without changing these settings, run Launch-SOMA-VR.cmd -SkipSettingsRepair; configure the required settings manually first.")
    } finally {
        # A cleanup failure must not conceal the original write/replace error.
        if ([IO.File]::Exists($temp)) {
            try { [IO.File]::Delete($temp) } catch { Write-Warning ('Could not remove temporary settings file: ' + $temp) }
        }
    }
}

function Repair-SomaVrSettings([string]$GameDirectory,[string]$SettingsPath,[int]$MonitorIndex=-1,[switch]$KeepSSAO,[string]$SettingsDirectory) {
    $display = Get-SomaVrMonitorSize $MonitorIndex
    if ($SettingsPath) {
        if (!(Test-Path -LiteralPath $SettingsPath -PathType Leaf)) { throw 'The explicit settings file does not exist.' }
        $files = @((Get-Item -LiteralPath $SettingsPath).FullName)
    } else {
        $documents = [Environment]::GetFolderPath([Environment+SpecialFolder]::MyDocuments,[Environment+SpecialFolderOption]::DoNotVerify)
        if (!$documents -and !$SettingsDirectory) { throw 'Windows Documents folder could not be located. Select a user config folder in the installer or pass -SettingsDirectory.' }
        $main = if ($SettingsDirectory) { [IO.Path]::GetFullPath($SettingsDirectory) } else { Join-Path $documents 'My Games\Soma\Main' }
        $files = @()
        if (Test-Path -LiteralPath $main -ErrorAction Stop) {
            $files = @(Get-ChildItem -LiteralPath $main -Filter '*user_settings.cfg' -File -ErrorAction Stop | Select-Object -ExpandProperty FullName)
        }
        # Seed the standard default profile on a first installation. Do not edit game defaults.
        if (!$files.Count) { $files = @(Join-Path $main 'Default_user_settings.cfg') }
    }
    # Validate every candidate before modifying any file.
    $plans = foreach ($file in $files) {
        $exists = Test-Path -LiteralPath $file -PathType Leaf
        $inputPath = if ($exists) { $file } else { Join-Path $GameDirectory 'config\default_user_settings.cfg' }
        $original = [IO.File]::ReadAllText($inputPath)
        $updated = Convert-SomaVrSettings $original $display.Width $display.Height ([bool]$KeepSSAO)
        [pscustomobject]@{Path=$file;Exists=$exists;Original=$original;Updated=$updated}
    }
    foreach ($plan in $plans) {
        if ($plan.Exists -and $plan.Original -ceq $plan.Updated) { Write-Output ('Settings already prepared: ' + $plan.Path); continue }
        Write-SomaVrSettingsPlan $plan
    }
    # Verify on disk, including files that already appeared prepared.
    foreach ($plan in $plans) {
        $actual = [IO.File]::ReadAllText($plan.Path)
        if ((Convert-SomaVrSettings $actual $display.Width $display.Height ([bool]$KeepSSAO)) -cne $actual) {
            throw ('Settings changed during launch preparation: ' + $plan.Path + '. Game startup stopped; retry the launcher.')
        }
    }
    Write-Output ('VR desktop target: ' + $display.Device + ' ' + $display.Width + 'x' + $display.Height + ' physical pixels. Headset resolution unchanged.')
}


