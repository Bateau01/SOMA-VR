# Installation and troubleshooting

## What to download

Download `SOMA-VR-1.04-S26EE-Installer.zip`, extract it, run `SOMA-VR-1.04-S26EE-Setup.exe`, and select **INSTALL / UPDATE / REPAIR**. The installer requests administrator access and preserves customized settings. The manual overlay instructions below apply to the `runtime` folder in the source archive. It contains the cumulative overlay: the DLL, injector, OpenXR loader, scripts, modified entity/map data, all current hand families, audio components and a launcher.

This is for an existing compatible SOMA installation. It does not contain `Soma.exe`, the full maps, game audio, or the other files needed to run the game independently.

## Installation:

1. Download and extract the latest release of SOMA-VR in the "Releases" section.
2. Run the SOMA-VR setup.exe file.
3. Ensure that the path to your SOMA game directory, as well as the folder containing your user_settings.cfg folder are detected. If the setup isn't able to automatically detect those folders, you can manually search for them.
4. Press "Install". If done correctly, you should receive a confirmation prompt stating that the VR mod was successfully installed.
5. To launch SOMA VR, navigate to your SOMA game directory, and run the "LAUNCH-SOMA-VR.cmd" file. It should run as an administrator. Ensure that your VR headset and controllers are connected, and SteamVR or VD is running using the OpenXR or VDXR runtime.

# NOTE:

- If it's your first time installing SOMA, please launch SOMA flatscreen first and complete the initial menu setup **before installing the VR mod**, as SOMA needs to generate the user_setting.cfg files.
- To use eye-tracking features (on a VR headset with eye-tracking), **in your SteamVR application on your PC, open Settings > Steam Link > toggle "Share eye tracking data to other apps on this PC" on. If you're using Virtual Desktop, open Streaming > toggle "Forward tracking data to PC". Restart SOMA if it's already open.**

## Troubleshooting:

- If your game immediately crashes upon injection, ensure that SteamVR is using OpenXR as its runtime.
- If your SOMA main menu looks out of place, try re-centering your camera using its designated keybind.
- If your cursor won't appear in SOMA's main menu when using your VR controllers, ensure that your SOMA game window is focused on your PC.

For any other in-game related issues, please upload "hpl3vr.log" from your game's root directory, and "hpl.log" from your C:\Users[YOUR_NAME]\Documents\My Games\Soma\Main. Include a description of what the issue is, where this issue occurred, what VR headset and controllers you're using, and your operating system.

If you crash, please also include the crash log found in your SOMA game root directory.

## Settings and calibration

Use the in-game **VR SETTINGS** page. The package now includes a root `hpl3vr_vr_settings.ini` with clean defaults (`body_slot_debug_visual=0`). Back up or keep your existing root INI when extracting an update if you have customized it. Extracting the packaged INI over yours replaces its values. The launcher only creates it from `defaults` when it is missing; it never overwrites an existing INI. In-game menu preferences in your user profile are separate. The root calibration file is also preserved. On a fresh installation, the launcher copies the reference rig calibration out of `defaults` only if the root calibration is missing. The reference contains hand orientation and bone-fit parameters.

Do not copy another player's saves or runtime FOV cache. Let the runtime create its own cache. Retired SET_HAND batch files are not included; normal story-driven hand selection remains the intended path.

## If something goes wrong

- **Other storefront or unsupported executable:** run `Check-SOMA-VR-Compatibility.cmd` and send `SOMA-VR-compatibility-report.json` with the storefront/version. An equivalent-engine result can be tried with `Launch-SOMA-VR.cmd -Experimental`; a different engine layout remains blocked and needs a native port. See the compatibility guide. GOG/Epic have not been validated.
- **SOMA remains running after quitting:** relaunch with Launch-SOMA-VR.cmd, or run Stop-SOMA-VR.cmd to close it without restarting. Both commands close all Soma.exe / Soma_NoSteam.exe instances, including active games; save progress first.
- **VR initialization fails:** confirm the headset connection and active OpenXR runtime, then examine `hpl3vr.log` in the game directory.
- **Missing hand family/material:** check that all `hand_*.skin`, `hands_*.dds` and `entities/soma_vr` files were copied, not only the DLL.
- **Script load error:** preserve the exact error and identify the build. Mixing DLL-only updates with old scripts can leave incompatible components.
- **World-scale hand-size check:** set scale to 0.70 with empty hands, grab and release a prop, then return to 1.00. Apparent hand size should remain constant. S26CC reverts the extra apparent-eye-height offset; fixed apparent hand size remains. Headset confirmation remains necessary.

## Flatscreen and uninstall

Launch the un-injected game normally for flatscreen. Script behavior is gated by active VR status.

To uninstall, close SOMA and restore your backed-up original files. A platform file verification can restore original game files, but it does not necessarily remove extra mod files. Remove only files identified as mod-added in your backup/install record. Do not delete your save directory as part of uninstalling.

`SOMA_VR_MANIFEST.json` lists every shipped overlay file and SHA256. Keep it with the release for troubleshooting and comparing installations.
