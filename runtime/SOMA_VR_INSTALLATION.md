# Installation and troubleshooting

## What to download

Download the latest release build `SOMA-VR-vx.xx.zip`. It contains the cumulative overlay: the DLL, injector, OpenXR loader, scripts, modified entity/map data, all current hand families, audio components and a launcher.

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

At launch, the selected monitor supplies the desktop resolution and refresh rate. The launcher sets windowed mode, disables V-Sync, engine FPS limiting, sleep when unfocused, SSAO (unless explicitly kept), and mouse smoothing. It applies this to detected default and named user profiles, retaining backups when values change. An unspecified monitor refresh leaves the saved refresh unchanged. Headset resolution and refresh remain controlled by the VR runtime.


Use the in-game **VR SETTINGS** page. The package now includes a root `hpl3vr_vr_settings.ini` with clean defaults (`body_slot_debug_visual=0`). Back up or keep your existing root INI when extracting an update if you have customized it. Extracting the packaged INI over yours replaces its values. The launcher only creates it from `defaults` when it is missing; it never overwrites an existing INI. In-game menu preferences in your user profile are separate. The root calibration file is also preserved. On a fresh installation, the launcher copies the reference rig calibration out of `defaults` only if the root calibration is missing. The reference contains hand orientation and bone-fit parameters, not play-session logs or headset account data.

Do not copy another player's saves or runtime FOV cache. Let the runtime create its own cache. Retired SET_HAND batch files are not included; normal story-driven hand selection remains the intended path.

## If something goes wrong

- **Storefront selection:** the same launcher automatically chooses the Steam or Epic/GOG native DLL for the verified executables. No extra command or experimental flag is needed for those profiles. For unknown builds, run `Check-SOMA-VR-Compatibility.cmd` and provide its report; a different engine layout remains blocked.
- **SOMA remains running after quitting:** relaunch with Launch-SOMA-VR.cmd, or run Stop-SOMA-VR.cmd to close it without restarting. Stop-SOMA-VR.cmd immediately force-terminates Soma.exe / Soma_NoSteam.exe and checks that they exited. The launcher still tries a brief normal close before forcing termination. These commands affect active games too; save progress first.
- **VR initialization fails:** confirm the headset connection and active OpenXR runtime, then examine `hpl3vr.log` in the game directory.
- **Missing hand family/material:** check that all `hand_*.skin`, `hands_*.dds` and `entities/soma_vr` files were copied, not only the DLL.
- **Script load error:** preserve the exact error and identify the build. Mixing DLL-only updates with old scripts can leave incompatible components.
- **World-scale hand-size check:** set scale to 0.70 with empty hands, grab and release a prop, then return to 1.00. Apparent hand size should remain constant. S26CC reverts the extra apparent-eye-height offset; fixed apparent hand size remains. Headset confirmation remains necessary.

## Flatscreen and uninstall

Launch the un-injected game normally for flatscreen. Script behavior is gated by active VR status.

To uninstall, close SOMA and restore your backed-up original files. A platform file verification can restore original game files, but it does not necessarily remove extra mod files. Remove only files identified as mod-added in your backup/install record. Do not delete your save directory as part of uninstalling.

`SOMA_VR_MANIFEST.json` lists every shipped overlay file and SHA256. Keep it with the release for troubleshooting and comparing installations.

S26EF: the desktop game is borderless windowed and may visually fill the monitor. DFR is under EYE TRACKING; texture-budget boost is under VIDEO. Both are disabled by default. See the features document for hardware requirements and validation limits.

## Controller button bindings

Open VR SETTINGS > CONTROLS > BUTTON BINDINGS and select an action. CHANGE BINDING listens for a button after you release the existing press. If the button is already assigned, a confirmation shows the resulting assignment for the other action. When the edited action was unassigned, the displaced action becomes unassigned; otherwise their buttons swap. No changes are applied until you confirm.

CLEAR BINDING removes that action's assignment. It is hidden when already unassigned. Clearing a standard action asks for confirmation; clearing Pause also reminds you that keyboard ESC can reopen the menu. BACK or a ten-second capture timeout leaves the current assignment intact. RESTORE DEFAULTS restores the normal layout, with Omni-Tool recall unassigned.

## Seated interaction options

Both options default to OFF under VR SETTINGS > GAMEPLAY.

REMOTE GRAB opens a submenu with an ON/OFF toggle and RANGE. Range defaults to 2 m and can be set from 1 to 3 m in 0.5 m steps. Point at a loose prop: a cyan beam, target marker and subtle cyan mesh-edge outline identify the selected prop. Hold your configured grab control to pull the prop toward the hand. Release to cancel. A blocked path or lost tracking cancels the pull. Once it reaches the hand, normal grabbing and release take over.

This first version supports loose, single-body, one-handed carry props up to 6 kg in ordinary gameplay. It excludes key items, the Omni-Tool, phones, handheld tablets, mounted/jointed objects, doors, drawers and other mechanisms. Physical contact and holster retrieval take priority. Remote pulls cannot begin while another authored interaction owns the player state.

TERMINAL LASER POINTER supports fixed terminals and laptops within 3 m. Point at the screen and press trigger once to focus it, then release and press trigger to select an option. Hold trigger for a supported drag/hold operation. The cyan marker shows the selection position. Physical screen touches take priority. Phones and handheld tablets keep their physical controls. Authored screen permissions remain in effect.

This accessibility build has passed automated input/lifetime checks, pickup/binding regressions, both edition builds, and isolated Newton collision/wake tests. Headset reach, beam alignment and clicks still need a hands-on check before public release.

The remote-grab outline follows the selected prop and the active pull. It clears on target loss, handoff, pause, tracking loss or map changes. It adds no grab range or new eligible objects. Its final brightness and stereo appearance still need a headset check.

VR settings show up to eight settings per page. Use NEXT PAGE and PREVIOUS PAGE within the category. Saved option values and controller bindings are retained. Remote targeting ignores invisible, non-colliding scripted areas; solid obstacles still block it.
