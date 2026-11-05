param([string]$Root=(Split-Path $PSScriptRoot -Parent))
$ErrorActionPreference='Stop'
. (Join-Path $Root 'runtime/SOMA-VR-Support.ps1')
function Assert($condition,$message){if(!$condition){throw $message}}
$fixture=Join-Path $Root ('audit/ji-logging/support-'+[Guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory((Join-Path $fixture 'config'))
$cfg=Join-Path $fixture 'config/main_init.cfg';[IO.File]::WriteAllText($cfg,'<Directories MainSaveFolder="Main" />')
$expected=Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'My Games/Soma/Main/hpl.log'
Assert ((Get-SomaNativeLog $fixture '') -eq $expected) 'Default native path'
[IO.File]::WriteAllText((Join-Path $fixture 'config/custom space.cfg'),'<Directories MainSaveFolder="IsolatedTest" />')
Assert ((Get-SomaNativeLog $fixture '-cfg "config/custom space.cfg"') -like '*IsolatedTest\hpl.log') 'Quoted custom config'
Assert (!(Get-SomaNativeLog $fixture '-cfg')) 'Malformed cfg must not guess'
[IO.File]::WriteAllText($cfg,'<Directories MainSaveFolder="../escape" />')
Assert (!(Get-SomaNativeLog $fixture '')) 'Traversal must fail'
[IO.File]::WriteAllText($cfg,'<Directories MainSaveFolder="Main" />')
$src=Join-Path $fixture 'native-input.log';[IO.File]::WriteAllText($src,'NATIVE ORIGINAL')
$session=[pscustomobject]@{SessionId='test';StartUtc=[DateTime]::UtcNow.AddSeconds(-2).ToString('o');NativeLog=$src;NativeBeforeUtc=''}
Save-SomaNativeLog $fixture $session
Assert ((Get-Content (Join-Path $fixture 'SOMA-native.log') -Raw) -eq 'NATIVE ORIGINAL') 'Copy mismatch'
Assert ((Get-Content (Join-Path $fixture 'SOMA-native-status.json') -Raw|ConvertFrom-Json).Status -eq 'current-session-candidate') 'Fresh identification'
$session.StartUtc=[DateTime]::UtcNow.AddMinutes(1).ToString('o');Save-SomaNativeLog $fixture $session
Assert ((Get-Content (Join-Path $fixture 'SOMA-native-status.json') -Raw|ConvertFrom-Json).Status -eq 'stale-not-confirmed-current') 'Stale must be labelled'
$session.NativeLog=Join-Path $fixture 'missing.log';Save-SomaNativeLog $fixture $session
Assert ((Get-Content (Join-Path $fixture 'SOMA-native.log') -Raw) -like '*native log missing*') 'Missing must replace stale copy'
$session.NativeLog=$src;$session.StartUtc=[DateTime]::UtcNow.AddSeconds(-2).ToString('o')
$session|ConvertTo-Json|Set-Content (Join-Path $fixture 'SOMA-VR-session.json')
$large=Join-Path $fixture 'large.log';[IO.File]::WriteAllText($large,('x'*9000000)+'END')
Copy-SomaSupportFile $large (Join-Path $fixture 'bounded.log')
Assert ((Get-Item (Join-Path $fixture 'bounded.log')).Length -lt 8388800) 'Bounded size'
Assert ([IO.File]::ReadAllText((Join-Path $fixture 'bounded.log')).EndsWith('END')) 'Tail preserved'
[IO.File]::WriteAllText((Join-Path $fixture 'hpl3vr.log'),'CURRENT VR')
[IO.File]::WriteAllText((Join-Path $fixture 'secret.txt'),'DO NOT PACKAGE')
[IO.File]::WriteAllText((Join-Path $fixture 'save.sav'),'DO NOT PACKAGE')
$zip=Export-SomaSupport $fixture
$z=[IO.Compression.ZipFile]::OpenRead($zip)
try {$names=@($z.Entries|ForEach-Object FullName);Assert ($names -contains 'SOMA-native.log') 'Native in ZIP';Assert ($names -contains 'hpl3vr.log') 'VR in ZIP';Assert ($names -notcontains 'secret.txt' -and $names -notcontains 'save.sav') 'Allowlist'} finally {$z.Dispose()}
# Archiving and collection are launcher work, no game process required.
for($i=0;$i -lt 5;$i++){$s=Start-SomaSupportSession $fixture '' ([pscustomobject]@{edition='fixture';sha256='fixture'});[IO.File]::WriteAllText((Join-Path $fixture 'hpl3vr.log'),('SESSION '+$i))}
Assert (@(Get-ChildItem (Join-Path $fixture 'SOMA-VR-Logs') -Directory).Count -eq 3) 'Session retention'
for($i=0;$i -lt 4;$i++){[void](Export-SomaSupport $fixture)}
Assert (@(Get-ChildItem (Join-Path $fixture 'SOMA-VR-Support') -Filter '*.zip').Count -eq 3) 'Zip retention'
# Crash/startup failure before session metadata still supports manual collection.
Remove-Item -LiteralPath (Join-Path $fixture 'SOMA-VR-session.json')
Assert (Test-Path -LiteralPath (Export-SomaSupport $fixture)) 'No-session collection'
foreach($name in @('Launch-SOMA-VR.ps1','SOMA-VR-Support.ps1')){$tokens=$null;$errors=$null;[void][Management.Automation.Language.Parser]::ParseFile((Join-Path $Root ('runtime/'+$name)),[ref]$tokens,[ref]$errors);Assert (!$errors) ('Parser '+$name)}
'PASS support collection: default/custom path, stale/missing, bounded tail, allowlist, retention, no-session, PS parser'|Tee-Object (Join-Path $fixture 'result.txt')
