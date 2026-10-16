
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '..\runtime\SOMA-VR-Settings.ps1')
$source='<Screen Width="2574" Height="1431" RefreshRate="60" FullScreen="true" Vsync="true" /><Engine LimitFPS="true" SleepWhenOutOfFocus="true" /><Input SmoothMouse="true" MouseSensitivity="1.7" /><Graphics SSAOActive="true" TextureQuality="0" />'
foreach($size in @(@(1920,1080),@(2560,1440),@(3440,1440))){
 foreach($hz in @(60,72,90,120,144,165,180,240)){
  foreach($keep in @($true,$false)){
   $out=Convert-SomaVrSettings $source $size[0] $size[1] $keep $hz
   [xml]$xml="<Root>$out</Root>"
   if($xml.Root.Screen.Width -ne $size[0] -or $xml.Root.Screen.Height -ne $size[1] -or $xml.Root.Screen.RefreshRate -ne $hz){throw 'Screen mismatch'}
   if($xml.Root.Input.SmoothMouse -ne 'false' -or $xml.Root.Input.MouseSensitivity -ne '1.7'){throw 'Input mismatch'}
   if($xml.Root.Screen.Vsync -ne 'false' -or $xml.Root.Screen.FullScreen -ne 'false' -or $xml.Root.Engine.LimitFPS -ne 'false' -or $xml.Root.Engine.SleepWhenOutOfFocus -ne 'false'){throw 'Existing calibration lost'}
   if($xml.Root.Graphics.SSAOActive -ne $keep.ToString().ToLowerInvariant() -or $xml.Root.Graphics.TextureQuality -ne '0'){throw 'Graphics preference lost'}
   if((Convert-SomaVrSettings $out $size[0] $size[1] $keep $hz) -cne $out){throw 'Not idempotent'}
  }
 }
}
foreach($hz in @(0,1,19,1001)){[xml]$xml='<Root>'+(Convert-SomaVrSettings $source 2560 1440 $false $hz)+'</Root>';if($xml.Root.Screen.RefreshRate -ne '60'){throw 'Invalid Hz overwrote saved value'}}
[xml]$empty='<Root>'+(Convert-SomaVrSettings '' 1920 1080 $false 120)+'</Root>'
if($empty.Root.Input.SmoothMouse -ne 'false' -or $empty.Root.Screen.RefreshRate -ne '120'){throw 'Missing sections not created'}
$caught=$false;try{Convert-SomaVrSettings '<Input/><Input/>' 1920 1080 $false 120}catch{$caught=$true};if(!$caught){throw 'Duplicate Input not rejected'}
$display=Get-SomaVrMonitorSize
Write-Output ('Detected selected display: '+($display|ConvertTo-Json -Compress))
Write-Output 'PASS 48 setting combinations; invalid refresh fallback; unrelated values preserved; idempotence; duplicate validation.'
