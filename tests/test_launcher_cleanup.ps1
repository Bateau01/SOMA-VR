param([string]$Launcher = (Join-Path $PSScriptRoot '..\runtime\Launch-SOMA-VR.ps1'))
$ErrorActionPreference='Stop'
$tokens=$null;$parseErrors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path -LiteralPath $Launcher),[ref]$tokens,[ref]$parseErrors)
if($parseErrors.Count){throw ($parseErrors | Out-String)}
foreach($name in @('Get-SomaProcesses','Stop-SomaInstances')){
 $definition=$ast.Find({param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $name},$true)
 if(!$definition){throw "Missing $name"}
 Invoke-Expression $definition.Extent.Text
}
function Get-Process {
 param($Id,$ErrorAction)
 if($script:enumerationFails){throw 'Enumeration denied'}
 if($Id){return $null} # Never invoke real taskkill in this isolated unit test.
 @($script:fakeProcesses | Where-Object {!$_.HasExited})
}
function New-FakeProcess($id,$hasWindow,$closes,$killFails,$name='Soma') {
 $p=[pscustomobject]@{Id=$id;ProcessName=$name;MainWindowHandle=[IntPtr]([int]$hasWindow);HasExited=$false;Closes=$closes;KillFails=$killFails;Closed=0;Killed=0;Disposed=0}
 $p | Add-Member ScriptMethod CloseMainWindow {$this.Closed++;if($this.Closes){$this.HasExited=$true};return $true}
 $p | Add-Member ScriptMethod WaitForExit {param($ms);return $this.HasExited}
 $p | Add-Member ScriptMethod Kill {$this.Killed++;if($this.KillFails){throw 'Mock access denied'};$this.HasExited=$true}
 $p | Add-Member ScriptMethod Dispose {$this.Disposed++}
 return $p
}
$script:fakeProcesses=@();Stop-SomaInstances -Force
$a=New-FakeProcess 1 $true $true $false
$b=New-FakeProcess 2 $false $false $false 'Soma_NoSteam'
$c=New-FakeProcess 3 $true $false $false
$unrelated=New-FakeProcess 4 $true $false $false 'vrserver'
$script:fakeProcesses=@($a,$b,$c,$unrelated);Stop-SomaInstances
if($a.Closed -ne 1 -or $a.Killed -ne 0 -or !$a.HasExited){throw 'Graceful exit failed'}
if($b.Closed -ne 0 -or $b.Killed -ne 1 -or !$b.HasExited){throw 'Headless cleanup failed'}
if($c.Closed -ne 1 -or $c.Killed -ne 1 -or !$c.HasExited){throw 'Hung window cleanup failed'}
if($unrelated.Closed -or $unrelated.Killed){throw 'Unrelated process targeted'}
foreach($p in @($a,$b,$c)){if($p.Disposed -ne 1){throw 'Handle not disposed'}}
$force=New-FakeProcess 5 $true $true $false
$script:fakeProcesses=@($force);Stop-SomaInstances -Force
if($force.Closed -ne 0 -or $force.Killed -ne 1){throw 'Explicit stop was not immediately forceful'}
$e=New-FakeProcess 6 $false $false $true
$script:fakeProcesses=@($e);$caught=$false
try{Stop-SomaInstances -Force}catch{$caught=$_.Exception.Message -like '*SOMA is still running*'}
if(!$caught -or $e.Killed -ne 3){throw 'Surviving process not reported/retried'}
$script:enumerationFails=$true;$caught=$false
try{Stop-SomaInstances -Force}catch{$caught=$true}
if(!$caught){throw 'Enumeration failure disguised as success'}
Write-Output 'PASS: graceful launch cleanup; explicit immediate force; headless/hung processes; unrelated process excluded; bounded retries; survivors and enumeration errors reported.'
