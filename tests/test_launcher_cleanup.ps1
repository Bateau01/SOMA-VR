param([string]$Launcher = (Join-Path $PSScriptRoot '..\runtime\Launch-SOMA-VR.ps1'))
$ErrorActionPreference='Stop'
$tokens=$null;$parseErrors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path -LiteralPath $Launcher),[ref]$tokens,[ref]$parseErrors)
if($parseErrors.Count){throw ($parseErrors | Out-String)}
$definition=$ast.Find({param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Stop-SomaInstances'},$true)
if(!$definition){throw 'Missing cleanup function'}
Invoke-Expression $definition.Extent.Text
function Get-Process { param($Name,$ErrorAction) if(($Name -join ',') -ne 'Soma,Soma_NoSteam'){throw 'Unexpected target names'}; return $script:fakeProcesses }
function New-FakeProcess($id,$hasWindow,$exited,$closes,$killFails) {
    $p=[pscustomobject]@{Id=$id;MainWindowHandle=[IntPtr]([int]$hasWindow);HasExited=$exited;Closes=$closes;KillFails=$killFails;Closed=0;Killed=0;Disposed=0}
    $p | Add-Member ScriptMethod CloseMainWindow { $this.Closed++;if($this.Closes){$this.HasExited=$true};return $true }
    $p | Add-Member ScriptMethod WaitForExit { param($ms);return $this.HasExited }
    $p | Add-Member ScriptMethod Kill { $this.Killed++;if($this.KillFails){throw 'Mock access denied'};$this.HasExited=$true }
    $p | Add-Member ScriptMethod Dispose { $this.Disposed++ }
    return $p
}
$script:fakeProcesses=@();Stop-SomaInstances
$a=New-FakeProcess 1 $true $false $true $false
$b=New-FakeProcess 2 $false $false $false $false
$c=New-FakeProcess 3 $true $false $false $false
$d=New-FakeProcess 4 $true $true $false $false
$script:fakeProcesses=@($a,$b,$c,$d);Stop-SomaInstances
if($a.Closed -ne 1 -or $a.Killed -ne 0 -or !$a.HasExited){throw 'Graceful exit failed'}
if($b.Closed -ne 0 -or $b.Killed -ne 1 -or !$b.HasExited){throw 'Headless cleanup failed'}
if($c.Closed -ne 1 -or $c.Killed -ne 1 -or !$c.HasExited){throw 'Hung window cleanup failed'}
if($d.Closed -ne 0 -or $d.Killed -ne 0){throw 'Already-exited process was touched'}
foreach($p in @($a,$b,$c,$d)){if($p.Disposed -ne 1){throw 'Handle not disposed'}}
$e=New-FakeProcess 5 $false $false $false $true
$script:fakeProcesses=@($e);$caught=$false
try{Stop-SomaInstances}catch{$caught=$_.Exception.Message -like '*Could not close SOMA process 5*'}
if(!$caught -or $e.Disposed -ne 1){throw 'Permission failure must be reported and handles disposed'}
Write-Output 'PASS: launcher parses; no processes, graceful exit, headless orphan, hung window, exit race, and access failure (mocked process objects).'
