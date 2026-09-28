# Installation and troubleshooting

## What to download

Download the latest release build `SOMA-VR-vx.xx.zip`. It contains the cumulative overlay: the DLL, injector, OpenXR loader, scripts, modified entity/map data, all current hand families, audio components and a launcher.

This is for an existing compatible SOMA installation. It does not contain `Soma.exe`, the full maps, game audio, or the other files needed to run the game independently.

## Installation:

1. Download and extract the latest release of SOMA-VR in the "Releases" section.
2. Extract contents of the "SOMA-VR-vx.xx" to the root of your SOMA game directory (where Soma.exe is located). Replace all files if prompted. I recommend creating a backup of your existing SOMA game folder.
3. [FIRST TIME INSTALLATION ONLY] Navigate to your user settings config file (C:\Users[YOUR_NAME]\Documents\My Games\Soma\Main), open the "YOURNAME_ID_user_settings.cfg", and make these changes:

- Engine LimitFPS="false"
- FullScreen="false"

4. Start SteamVR and ensure that your headset and controllers are connected. Ensure that SteamVR is using OpenXR as its runtime.
5. To launch SOMA VR, run "Launch-SOMA-VR.cmd" from your root game directory. If prompted with an error stating "access is denied," or "elevation required," or anything in that regard, run that same file as an administrator.

## Troubleshooting:

- If your game immediately crashes upon injection, ensure that SteamVR is using OpenXR as its runtime.
- If your game still immediately crashes, navigate to your user settings config file (C:\Users[YOUR_NAME]\Documents\My Games\Soma\Main), open the "YOURNAME_ID_user_settings.cfg" file, and ensure that your screen's width and height is set to your monitor's resolution (E.G, Width = 2560, Height = 1440 for 2560x1440).
- If your game's menu looks weirdly cropped, ensure that your game is running in windowed mode instead of fullscreen.

For any other in-game related issues, please upload "hpl3vr.log" from your game's root directory, and "hpl.log" from your C:\Users[YOUR_NAME]\Documents\My Games\Soma\Main. Include a description of what the issue is, where this issue occurred, what VR headset and controllers you're using, and your operating system.

If you crash, please also include the crash log found in your SOMA game root directory.

## Settings and calibration

Use the in-game **VR SETTINGS** page. Your existing `hpl3vr_vr_settings.ini` is not replaced by this package. The root calibration file is also preserved. On a fresh installation, the launcher copies the reference rig calibration out of `defaults` only if the root calibration is missing. The reference contains hand orientation and bone-fit parameters, not play-session logs or headset account data.

Do not copy another player's saves or runtime FOV cache. Let the runtime create its own cache. Retired SET_HAND batch files are not included; normal story-driven hand selection remains the intended path.

## If something goes wrong

- **Unsupported executable:** the launcher detected a different `Soma.exe` hash. Report the game edition/version and hash. Do not assume fixed native addresses are compatible with another executable.
- **SOMA remains running after quitting:** relaunch with Launch-SOMA-VR.cmd, or run Stop-SOMA-VR.cmd to close it without restarting. Both commands close all Soma.exe / Soma_NoSteam.exe instances, including active games; save progress first.
- **VR initialization fails:** confirm the headset connection and active OpenXR runtime, then examine `hpl3vr.log` in the game directory.
- **Missing hand family/material:** check that all `hand_*.skin`, `hands_*.dds` and `entities/soma_vr` files were copied, not only the DLL.
- **Script load error:** preserve the exact error and identify the build. Mixing DLL-only updates with old scripts can leave incompatible components.
- **World-scale hand-size check:** set scale to 0.70 with empty hands, grab and release a prop, then return to 1.00. Apparent hand size should remain constant. S26CC reverts the extra apparent-eye-height offset; fixed apparent hand size remains. Headset confirmation remains necessary.

## Flatscreen and uninstall

Launch the un-injected game normally for flatscreen. Script behavior is gated by active VR status.

To uninstall, close SOMA and restore your backed-up original files. A platform file verification can restore original game files, but it does not necessarily remove extra mod files. Remove only files identified as mod-added in your backup/install record. Do not delete your save directory as part of uninstalling.

`SOMA_VR_MANIFEST.json` lists every shipped overlay file and SHA256. Keep it with the release for troubleshooting and comparing installations.
