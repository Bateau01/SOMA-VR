# Official stable releases only. No download or install until the player agrees.
function Get-SomaVrUpdatePlan($Release,$Manifest,[long]$CurrentBuild) {
    if ($Release.draft -or $Release.prerelease) { return $null }
    if ($Manifest.schema -ne 1 -or $Manifest.product -ne 'SOMA-VR' -or $Manifest.protocol -ne 1) { throw 'Unsupported update manifest.' }
    $build=[long]$Manifest.build
    if ($build -le $CurrentBuild) { return $null }
    if ([string]$Manifest.version -notmatch '^\d+\.\d+(?:\.\d+)?-S\d+[A-Z]+$') { throw 'Invalid update version.' }
    if ([string]$Manifest.sha256 -notmatch '^[a-fA-F0-9]{64}$') { throw 'Invalid installer checksum.' }
    $name=[string]$Manifest.asset
    if ($name -cne ('SOMA-VR-'+$Manifest.version+'-Setup.exe')) { throw 'Unexpected installer asset name.' }
    $assets=@($Release.assets | Where-Object { $_.name -ceq $name })
    if ($assets.Count -ne 1) { throw 'Release must contain exactly one matching installer.' }
    $asset=$assets[0]
    $size=[long]$Manifest.size
    if ($size -le 0 -or $size -gt 536870912 -or [long]$asset.size -ne $size) { throw 'Unexpected installer size.' }
    $prefix='https://github.com/Bateau01/SOMA-VR/releases/download/'
    if (![string]$asset.browser_download_url -or !([string]$asset.browser_download_url).StartsWith($prefix,[StringComparison]::Ordinal)) { throw 'Installer is not an official repository release asset.' }
    [pscustomobject]@{Build=$build;Version=[string]$Manifest.version;Url=[string]$asset.browser_download_url;Size=$size;Hash=([string]$Manifest.sha256).ToLowerInvariant();Name=$name}
}
function Test-SomaVrDownloadedUpdate([string]$Path,$Plan) {
    if ((Get-Item -LiteralPath $Path).Length -ne $Plan.Size) { throw 'Downloaded installer size does not match the release.' }
    if ((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Plan.Hash) { throw 'Downloaded installer checksum does not match the release.' }
}
function Get-SomaVrUpdateJson([string]$Url) {
    Invoke-RestMethod -Uri $Url -Headers @{'User-Agent'='SOMA-VR-Updater';'Accept'='application/vnd.github+json'} -TimeoutSec 8 -ErrorAction Stop
}
function Confirm-SomaVrUpdate([string]$Current,[string]$Next) {
    Add-Type -AssemblyName System.Windows.Forms
    [Windows.Forms.MessageBox]::Show("SOMA VR $Next is available. You have $Current.`n`nDownload and install this update now? Your saves and settings will be kept.`n`nChoose No to play your current version.",'SOMA VR update',[Windows.Forms.MessageBoxButtons]::YesNo,[Windows.Forms.MessageBoxIcon]::Information) -eq [Windows.Forms.DialogResult]::Yes
}
function Invoke-SomaVrUpdate([string]$GameDirectory) {
    $stage=$null;$installStarted=$false
    try {
        # Never update underneath a running game. Check-only and stop-only skip this function entirely.
        if (@(Get-Process -Name Soma,Soma_NoSteam -ErrorAction SilentlyContinue).Count) { return $false }
        $local=Get-Content -LiteralPath (Join-Path $GameDirectory 'SOMA-VR-Update-Version.json') -Raw | ConvertFrom-Json
        [Net.ServicePointManager]::SecurityProtocol=[Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
        $release=Get-SomaVrUpdateJson 'https://api.github.com/repos/Bateau01/SOMA-VR/releases/latest'
        if ($release.draft -or $release.prerelease) { return $false }
        $meta=@($release.assets | Where-Object { $_.name -ceq 'SOMA-VR-update.json' })
        if ($meta.Count -ne 1) { return $false }
        $url=[string]$meta[0].browser_download_url
        if (!$url.StartsWith('https://github.com/Bateau01/SOMA-VR/releases/download/',[StringComparison]::Ordinal) -or [long]$meta[0].size -gt 16384) { throw 'Invalid update manifest asset.' }
        $plan=Get-SomaVrUpdatePlan $release (Get-SomaVrUpdateJson $url) ([long]$local.build)
        if (!$plan) { return $false }
        if (!(Confirm-SomaVrUpdate ([string]$local.version) $plan.Version)) { return $false }
        $stage=Join-Path ([IO.Path]::GetTempPath()) ('SOMA-VR-Update-'+[Guid]::NewGuid().ToString('N'))
        [void][IO.Directory]::CreateDirectory($stage)
        $installer=Join-Path $stage $plan.Name
        Write-Host ('Downloading SOMA VR '+$plan.Version+'...')
        Invoke-WebRequest -UseBasicParsing -Uri $plan.Url -OutFile $installer -TimeoutSec 300 -ErrorAction Stop
        Test-SomaVrDownloadedUpdate $installer $plan
        $info=New-Object Diagnostics.ProcessStartInfo
        $info.FileName=$installer
        # Windows paths cannot contain quotes; trim the trailing separator before quoting.
        $root=[IO.Path]::GetFullPath($GameDirectory).TrimEnd('\')
        if ($root.Contains('"')) { throw 'Invalid game directory.' }
        $info.Arguments='--update "'+$root+'" --expected-build '+$plan.Build
        $info.UseShellExecute=$false;$info.CreateNoWindow=$true
        Write-Host 'Installing the update...'
        $installStarted=$true
        $process=[Diagnostics.Process]::Start($info)
        try { $process.WaitForExit();if ($process.ExitCode -ne 0) { throw ('Installer failed (code '+$process.ExitCode+'). See %LOCALAPPDATA%\SOMA-VR-Installer\Logs.') } } finally { $process.Dispose() }
        $installed=Get-Content -LiteralPath (Join-Path $root '.soma-vr-installer\receipt.json') -Raw | ConvertFrom-Json
        if ([long]$installed.Build -ne $plan.Build) { throw 'The installer did not confirm the requested build.' }
        Write-Host ('SOMA VR '+$plan.Version+' installed successfully. Starting the updated launcher...')
        return $true
    } catch {
        if (Test-Path -LiteralPath (Join-Path $GameDirectory '.soma-vr-installer\pending-transaction')) { throw 'Update recovery is required. Run the installer and select Recover interrupted install.' }
        if ($installStarted) { throw ('Update did not complete: '+$_.Exception.Message+' Start the installer to review or repair it before launching again.') }
        Write-Warning ('SOMA VR update was not applied: '+$_.Exception.Message+' Continuing with the installed version.')
        return $false
    } finally {
        if ($stage -and (Test-Path -LiteralPath $stage)) { try { $resolved=[IO.Path]::GetFullPath($stage); $tempRoot=[IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')+'\'; if (!$resolved.StartsWith($tempRoot,[StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetFileName($resolved) -notmatch '^SOMA-VR-Update-[a-f0-9]{32}$') { throw 'Unexpected download directory.' }; Remove-Item -LiteralPath $resolved -Recurse -Force -ErrorAction Stop } catch { Write-Warning ('Update download retained at '+$stage) } }
    }
}
