$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
. (Join-Path $root 'runtime\SOMA-VR-Update.ps1')
$script:checks=0
function Check($value,$message){$script:checks++;if(!$value){throw $message}}
function Reject($action){$rejected=$false;try{& $action}catch{$rejected=$true};Check $rejected 'Expected rejection'}
$m=[pscustomobject]@{schema=1;product='SOMA-VR';protocol=1;build=2026101614;version='1.0.8-S26HP';asset='SOMA-VR-1.0.8-S26HP-Setup.exe';size=3;sha256=('a'*64)}
$a=[pscustomobject]@{name=$m.asset;size=3;browser_download_url=('https://github.com/Bateau01/SOMA-VR/releases/download/v1.0.8/'+$m.asset)}
$r=[pscustomobject]@{draft=$false;prerelease=$false;assets=@($a)}
Check ((Get-SomaVrUpdatePlan $r $m 2026101613).Build -eq $m.build) 'New build missing'
Check ($null -eq (Get-SomaVrUpdatePlan $r $m $m.build)) 'Repeated update'
Check ($null -eq (Get-SomaVrUpdatePlan $r $m 2026101615)) 'Downgrade offered'
$r.prerelease=$true;Check ($null -eq (Get-SomaVrUpdatePlan $r $m 1)) 'Prerelease offered';$r.prerelease=$false
$r.draft=$true;Check ($null -eq (Get-SomaVrUpdatePlan $r $m 1)) 'Draft offered';$r.draft=$false
$m.protocol=2;Reject {Get-SomaVrUpdatePlan $r $m 1};$m.protocol=1
$m.sha256='bad';Reject {Get-SomaVrUpdatePlan $r $m 1};$m.sha256='a'*64
$a.browser_download_url='https://github.com/another/repo/releases/download/x/setup.exe';Reject {Get-SomaVrUpdatePlan $r $m 1}
$a.browser_download_url='https://github.com/Bateau01/SOMA-VR/releases/download/v1.0.8/'+$m.asset
$a.size=5;Reject {Get-SomaVrUpdatePlan $r $m 1};$a.size=3
$r.assets=@($a,$a);Reject {Get-SomaVrUpdatePlan $r $m 1};$r.assets=@($a)
$fixture=Join-Path $root 'build\update-test';[void][IO.Directory]::CreateDirectory($fixture)
$file=Join-Path $fixture 'download';[IO.File]::WriteAllBytes($file,[byte[]]@(1,2,3));$m.sha256=(Get-FileHash $file).Hash
$plan=Get-SomaVrUpdatePlan $r $m 1;Test-SomaVrDownloadedUpdate $file $plan
[IO.File]::WriteAllBytes($file,[byte[]]@(1,2,4));Reject {Test-SomaVrDownloadedUpdate $file $plan}
[IO.File]::WriteAllBytes($file,[byte[]]@(1));Reject {Test-SomaVrDownloadedUpdate $file $plan}
# Exercise orchestration without network, downloads, dialogs or running installers.
Copy-Item (Join-Path $root 'runtime\SOMA-VR-Update-Version.json') $fixture
function Get-Process { @() }
$script:requests=0;$script:prompts=0;$script:downloads=0
function Get-SomaVrUpdateJson($Url){$script:requests++;if($Url -like '*api.github.com*'){return $script:r};return $script:m}
function Confirm-SomaVrUpdate($Current,$Next){$script:prompts++;return $false}
function Invoke-WebRequest { $script:downloads++;throw 'Unexpected download' }
$meta=[pscustomobject]@{name='SOMA-VR-update.json';size=500;browser_download_url='https://github.com/Bateau01/SOMA-VR/releases/download/v1.0.8/SOMA-VR-update.json'}
$r.assets=@($a,$meta)
Check (!(Invoke-SomaVrUpdate $fixture)) 'Decline should continue current game'
Check ($script:prompts -eq 1 -and $script:downloads -eq 0) 'Decline downloaded or executed code'
function Get-SomaVrUpdateJson($Url){throw 'Simulated offline/rate limit'}
Check (!(Invoke-SomaVrUpdate $fixture)) 'Offline should continue current game'
function Get-Process { ,([pscustomobject]@{ProcessName='Soma'}) }
Check (!(Invoke-SomaVrUpdate $fixture)) 'Running game must not be updated'
$errors=$null;$tokens=$null
[void][Management.Automation.Language.Parser]::ParseFile((Join-Path $root 'runtime\Launch-SOMA-VR.ps1'),[ref]$tokens,[ref]$errors)
Check ($errors.Count -eq 0) 'Launcher parse failed'
Write-Host "PASS $script:checks updater policy, hash, decline, offline and running-game checks"
