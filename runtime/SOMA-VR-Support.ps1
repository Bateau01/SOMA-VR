param([switch]$Collect,[switch]$Watch,[string]$GameDirectory=$PSScriptRoot,[int]$GameProcessId=0,[string]$SessionId='')
$ErrorActionPreference='Stop'
# Serialization is confined to launcher/support processes, never the game.
function Get-SomaSupportLock([string]$Root) {
    $hash=[Security.Cryptography.SHA256]::Create()
    try {$key=([BitConverter]::ToString($hash.ComputeHash([Text.Encoding]::UTF8.GetBytes([IO.Path]::GetFullPath($Root).ToLowerInvariant())))).Replace('-','')} finally {$hash.Dispose()}
    $mutex=New-Object Threading.Mutex($false,('Local\SOMA-VR-Support-'+$key))
    try {if(!$mutex.WaitOne(30000)){$mutex.Dispose();throw 'Support collector is busy'}} catch [Threading.AbandonedMutexException] {}
    return $mutex
}
function Save-SomaNativeLog([string]$Root,$Session) {
    $mutex=Get-SomaSupportLock $Root
    try {
        $state=Join-Path $Root 'SOMA-VR-session.json'
        if(Test-Path -LiteralPath $state){$current=Get-Content -LiteralPath $state -Raw|ConvertFrom-Json;if($current.SessionId -ne $Session.SessionId){return}}
        Save-SomaNativeLogCore $Root $Session
    } finally {$mutex.ReleaseMutex();$mutex.Dispose()}
}
function Start-SomaSupportSession([string]$Root,[string]$Arguments,$Report) {
    $mutex=Get-SomaSupportLock $Root
    try {Start-SomaSupportSessionCore $Root $Arguments $Report} finally {$mutex.ReleaseMutex();$mutex.Dispose()}
}
function Copy-SomaSupportFile([string]$Source,[string]$Destination,[long]$Limit=8388608) {
    $inputStream=$null;$outputStream=$null
    try {
        $inputStream=New-Object IO.FileStream($Source,[IO.FileMode]::Open,[IO.FileAccess]::Read,([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete))
        $outputStream=New-Object IO.FileStream($Destination,[IO.FileMode]::Create,[IO.FileAccess]::Write,[IO.FileShare]::Read)
        if($inputStream.Length -gt $Limit){
            $notice=[Text.Encoding]::UTF8.GetBytes("[support collector: older bytes omitted; last $Limit bytes follow]`r`n")
            $outputStream.Write($notice,0,$notice.Length);[void]$inputStream.Seek(-$Limit,[IO.SeekOrigin]::End)
        }
        $buffer=New-Object byte[] 65536;$remaining=$Limit
        while($remaining -gt 0){$n=$inputStream.Read($buffer,0,[int][Math]::Min($buffer.Length,$remaining));if(!$n){break};$outputStream.Write($buffer,0,$n);$remaining-=$n}
    } finally {if($inputStream){$inputStream.Dispose()};if($outputStream){$outputStream.Dispose()}}
}
function Get-SomaNativeLog([string]$Root,[string]$Arguments) {
    $cfg=Join-Path $Root 'config\main_init.cfg'
    if($Arguments -match '(?i)(?:^|\s)-cfg\s+(?:"([^"]+)"|(\S+))'){
        $cfg=if($Matches[1]){$Matches[1]}else{$Matches[2]}
        if(![IO.Path]::IsPathRooted($cfg)){$cfg=Join-Path $Root $cfg}
    } elseif($Arguments -match '(?i)(?:^|\s)-cfg'){return $null}
    if(!(Test-Path -LiteralPath $cfg -PathType Leaf)){return $null}
    $text=[IO.File]::ReadAllText($cfg)
    if($text -notmatch 'MainSaveFolder\s*=\s*"([^"]+)"'){return $null}
    $folder=$Matches[1]
    if([IO.Path]::IsPathRooted($folder) -or $folder -match '(^|[\\/])\.\.([\\/]|$)'){return $null}
    $documents=[Environment]::GetFolderPath([Environment+SpecialFolder]::MyDocuments,[Environment+SpecialFolderOption]::DoNotVerify)
    if(!$documents){return $null}
    return Join-Path (Join-Path (Join-Path $documents 'My Games\Soma') $folder) 'hpl.log'
}
function Save-SomaNativeLogCore([string]$Root,$Session) {
    $status=[ordered]@{SessionId=$Session.SessionId;CollectedUtc=[DateTime]::UtcNow.ToString('o');Source=$Session.NativeLog;Status='missing';Truncated=$false}
    if($Session.NativeLog -and (Test-Path -LiteralPath $Session.NativeLog -PathType Leaf)){
        $f=Get-Item -LiteralPath $Session.NativeLog
        $status.SourceWriteUtc=$f.LastWriteTimeUtc.ToString('o')
        $fresh=$f.LastWriteTimeUtc -ge ([DateTime]::Parse($Session.StartUtc).ToUniversalTime().AddSeconds(-2)) -and $status.SourceWriteUtc -ne $Session.NativeBeforeUtc
        $status.Status=if($fresh){'current-session-candidate'}else{'stale-not-confirmed-current'}
        $status.Truncated=$f.Length -gt 8388608
        Copy-SomaSupportFile $f.FullName (Join-Path $Root 'SOMA-native.log')
    } elseif(!$Session.NativeLog){$status.Status='unresolved-custom-config'}
    if($status.Status -eq 'missing' -or $status.Status -eq 'unresolved-custom-config'){
        [IO.File]::WriteAllText((Join-Path $Root 'SOMA-native.log'),('[support collector: native log '+$status.Status+'; see SOMA-native-status.json]'))
    }
    $status|ConvertTo-Json -Depth 4|Set-Content -LiteralPath (Join-Path $Root 'SOMA-native-status.json') -Encoding UTF8
}
function Get-SomaSupportFiles([string]$Root) {
    $names=@('hpl3vr.log','hpl3vr.log.1','hpl3vr.log.2','hpl3vr.log.3','SOMA-native.log','SOMA-native-status.json','SOMA-VR-session.json','SOMA-VR-compatibility-report.json','SOMA-VR-Update-Version.json','hpl3vr_vr_settings.ini','hpl3vr_simulation_rate.txt')
    foreach($name in $names){$p=Join-Path $Root $name;if(Test-Path -LiteralPath $p -PathType Leaf){Get-Item -LiteralPath $p}}
    Get-ChildItem -LiteralPath $Root -Filter 'hpl3vr*crash*.log' -File | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 2
}
function Start-SomaSupportSessionCore([string]$Root,[string]$Arguments,$Report) {
    $state=Join-Path $Root 'SOMA-VR-session.json';$history=Join-Path $Root 'SOMA-VR-Logs'
    if(Test-Path -LiteralPath $state){
        try {$previous=Get-Content -LiteralPath $state -Raw|ConvertFrom-Json;Save-SomaNativeLog $Root $previous} catch {Write-Warning ('Previous native log collection: '+$_.Exception.Message)}
    }
    if(Test-Path -LiteralPath (Join-Path $Root 'hpl3vr.log')){
        [void][IO.Directory]::CreateDirectory($history)
        $archive=Join-Path $history ('session-'+[DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss')+'-'+[Guid]::NewGuid().ToString('N'))
        [void][IO.Directory]::CreateDirectory($archive)
        foreach($f in Get-SomaSupportFiles $Root){Copy-SomaSupportFile $f.FullName (Join-Path $archive $f.Name)}
        # Only directories owned by this collector, never game folders.
        $rootFull=[IO.Path]::GetFullPath($history).TrimEnd('\')+'\'
        foreach($old in @(Get-ChildItem -LiteralPath $history -Directory -Filter 'session-*'|Sort-Object Name -Descending|Select-Object -Skip 3)){
            $full=[IO.Path]::GetFullPath($old.FullName)
            if(!$full.StartsWith($rootFull,[StringComparison]::OrdinalIgnoreCase) -or ($old.Attributes -band [IO.FileAttributes]::ReparsePoint)){continue}
            Remove-Item -LiteralPath $full -Recurse -Force
        }
    }
    # Rotation segments belong to the old session, which was archived above.
    for($i=1;$i -le 3;$i++){$p=Join-Path $Root ('hpl3vr.log.'+$i);if(Test-Path -LiteralPath $p){Remove-Item -LiteralPath $p -Force}}
    $native=Get-SomaNativeLog $Root $Arguments;$before=$null
    if($native -and (Test-Path -LiteralPath $native)){$before=(Get-Item -LiteralPath $native).LastWriteTimeUtc.ToString('o')}
    $version=$null;try {$version=Get-Content -LiteralPath (Join-Path $Root 'SOMA-VR-Update-Version.json') -Raw|ConvertFrom-Json} catch {}
    $session=[ordered]@{SessionId=[Guid]::NewGuid().ToString('N');StartUtc=[DateTime]::UtcNow.ToString('o');NativeLog=$native;NativeBeforeUtc=$before;Version=$version.version;Build=$version.build;Edition=$Report.edition;ExecutableSha256=$Report.sha256;GameArguments=$Arguments;NativePathNote='From selected main config and Windows Documents; status does not prove no concurrent native game wrote the file.'}
    $session|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $state -Encoding UTF8
    return [pscustomobject]$session
}
function Export-SomaSupport([string]$Root) {
    if(Test-Path -LiteralPath (Join-Path $Root 'SOMA-VR-session.json')){$session=Get-Content -LiteralPath (Join-Path $Root 'SOMA-VR-session.json') -Raw|ConvertFrom-Json}
    else {$session=[pscustomobject]@{SessionId='unknown';StartUtc=[DateTime]::UtcNow.ToString('o');NativeLog=(Get-SomaNativeLog $Root '');NativeBeforeUtc=$null}}
    try {Save-SomaNativeLog $Root $session} catch {Write-Warning ('Native copy: '+$_.Exception.Message)}
    $out=Join-Path $Root 'SOMA-VR-Support'
    try {[void][IO.Directory]::CreateDirectory($out);$probe=Join-Path $out '.write-test';[IO.File]::WriteAllText($probe,'');Remove-Item -LiteralPath $probe} catch {$out=Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'SOMA-VR-Support';[void][IO.Directory]::CreateDirectory($out)}
    $zip=Join-Path $out ('SOMA-VR-support-'+[DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss')+'-'+[Guid]::NewGuid().ToString('N')+'.zip')
    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $file=[IO.File]::Open($zip,[IO.FileMode]::CreateNew);$archive=New-Object IO.Compression.ZipArchive($file,[IO.Compression.ZipArchiveMode]::Create)
    $temp=Join-Path ([IO.Path]::GetTempPath()) ([Guid]::NewGuid().ToString('N')+'.log')
    try {
        foreach($f in Get-SomaSupportFiles $Root){if($f.Name -in @('SOMA-native.log','SOMA-native-status.json')){continue};Copy-SomaSupportFile $f.FullName $temp;[void][IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive,$temp,$f.Name)}
        # Collect native output directly into temporary staging even for protected installs.
        $nativeStage=Join-Path ([IO.Path]::GetTempPath()) ('SOMA-support-'+[Guid]::NewGuid().ToString('N'));[void][IO.Directory]::CreateDirectory($nativeStage)
        try {Save-SomaNativeLog $nativeStage $session;foreach($name in @('SOMA-native.log','SOMA-native-status.json')){[void][IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive,(Join-Path $nativeStage $name),$name)}} finally {foreach($name in @('SOMA-native.log','SOMA-native-status.json')){$p=Join-Path $nativeStage $name;if(Test-Path -LiteralPath $p){Remove-Item -LiteralPath $p}};[IO.Directory]::Delete($nativeStage)}
        $history=Join-Path $Root 'SOMA-VR-Logs'
        if(Test-Path -LiteralPath $history){foreach($dir in @(Get-ChildItem -LiteralPath $history -Directory -Filter 'session-*'|Sort-Object Name -Descending|Select-Object -First 3)){
            if($dir.Attributes -band [IO.FileAttributes]::ReparsePoint){continue}
            foreach($f in Get-SomaSupportFiles $dir.FullName){Copy-SomaSupportFile $f.FullName $temp;[void][IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive,$temp,('previous/'+$dir.Name+'/'+$f.Name))}
        }}
    } finally {$archive.Dispose();$file.Dispose();if(Test-Path -LiteralPath $temp){Remove-Item -LiteralPath $temp}}
    foreach($old in @(Get-ChildItem -LiteralPath $out -Filter "SOMA-VR-support-*.zip" -File|Sort-Object LastWriteTimeUtc -Descending|Select-Object -Skip 3)){Remove-Item -LiteralPath $old.FullName -Force}
    return $zip
}
if($Watch){
    try {
        try {$p=[Diagnostics.Process]::GetProcessById($GameProcessId);$expected=Get-Content -LiteralPath (Join-Path $GameDirectory "SOMA-VR-session.json") -Raw|ConvertFrom-Json;if($expected.SessionId -eq $SessionId -and $p.StartTime.ToUniversalTime() -ge ([DateTime]::Parse($expected.StartUtc).ToUniversalTime().AddSeconds(-10))){$p.WaitForExit()};$p.Dispose()} catch {}
        $session=Get-Content -LiteralPath (Join-Path $GameDirectory 'SOMA-VR-session.json') -Raw|ConvertFrom-Json
        if($session.SessionId -eq $SessionId){Save-SomaNativeLog $GameDirectory $session}
    } catch {Write-Warning ('Support log collection failed: '+$_.Exception.Message)}
}
if($Collect){try {Write-Output (Export-SomaSupport $GameDirectory)} catch {Write-Error $_;exit 1}}
