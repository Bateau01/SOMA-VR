$ErrorActionPreference='Stop'
$g='C:\Users\BateauPC\.codex\visualizations\2026\09\10\01a08a5d-ef11-7e72-946a-520c0112c85c\SOMA_VR_S26AY_SHUTTLE\validation\Game'
$env:HV_NATIVE_EXE='C:\Program Files\Epic Games\SOMA\Soma.exe'
& C:\Python314\python.exe tests/test_omni_sequence_hv.py $g > build/store-sequence-final.log
if($LASTEXITCODE){throw 'Store sequence failed'}
Remove-Item Env:HV_NATIVE_EXE
& C:\Python314\python.exe tests/test_key_geometry_ht.py $g > build/key-geometry-final.log
if($LASTEXITCODE){throw 'Key geometry failed'}
& build/delivery-hv-final/UpdaterTests.exe build/delivery-hv-final/UpdaterRetry build/delivery-hv-final/embedded-payload 'C:\Program Files\Epic Games\SOMA\Soma.exe' > build/delivery-hv-final/UpdaterRetry.log
if($LASTEXITCODE){throw 'Updater retry failed'}
Write-Output 'PASS store sequence, key geometry and updater retry'
