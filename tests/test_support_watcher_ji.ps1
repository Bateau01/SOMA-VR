param([string]$Root=(Split-Path $PSScriptRoot -Parent))
$ErrorActionPreference='Stop'
$exe=Join-Path $env:WINDIR 'System32/WindowsPowerShell/v1.0/powershell.exe'
$collector=Join-Path $Root 'runtime/SOMA-VR-Support.ps1'
$out=Join-Path $Root ('audit/ji-logging/watcher-'+[Guid]::NewGuid().ToString('N'));[void][IO.Directory]::CreateDirectory($out)
foreach($mode in @('normal','killed','obsolete')){
 $dir=Join-Path $out $mode;[void][IO.Directory]::CreateDirectory($dir)
 $native=Join-Path $dir 'native-input.log';[IO.File]::WriteAllText($native,'native '+$mode)
 $sid=[Guid]::NewGuid().ToString('N')
 [pscustomobject]@{SessionId=$sid;StartUtc=[DateTime]::UtcNow.AddSeconds(-1).ToString('o');NativeLog=$native;NativeBeforeUtc=''}|ConvertTo-Json|Set-Content (Join-Path $dir 'SOMA-VR-session.json')
 $seconds=if($mode -eq 'normal'){4}else{20}
 $p=Start-Process -FilePath $exe -ArgumentList @('-NoProfile','-Command',('Start-Sleep '+$seconds)) -WindowStyle Hidden -PassThru
 $watch=Start-Process -FilePath $exe -ArgumentList ('-NoProfile -ExecutionPolicy Bypass -File "'+$collector+'" -Watch -GameDirectory "'+$dir+'" -GameProcessId '+$p.Id+' -SessionId '+$sid) -WindowStyle Hidden -PassThru
 try {
  Start-Sleep -Milliseconds 1500
  if(Test-Path (Join-Path $dir 'SOMA-native.log')){throw 'Copied while target alive'}
  if($mode -eq 'obsolete'){$j=Get-Content (Join-Path $dir 'SOMA-VR-session.json') -Raw|ConvertFrom-Json;$j.SessionId='new-session';$j|ConvertTo-Json|Set-Content (Join-Path $dir 'SOMA-VR-session.json')}
  if($mode -ne 'normal'){$p.Kill()}
  if(!$watch.WaitForExit(12000)){throw 'Watcher failed to exit'}
  $exists=Test-Path (Join-Path $dir 'SOMA-native.log')
  if($mode -eq 'obsolete'){if($exists){throw 'Old watcher overwrote new session'}}elseif(!$exists -or (Get-Content (Join-Path $dir 'SOMA-native.log') -Raw) -ne ('native '+$mode)){throw 'Missing exit copy'}
 } finally {if(!$p.HasExited){$p.Kill()};if(!$watch.HasExited){$watch.Kill()};$p.Dispose();$watch.Dispose()}
}
'PASS real process watcher: deferred copy, normal exit, forced exit, obsolete session rejection'|Tee-Object (Join-Path $out 'result.txt')
