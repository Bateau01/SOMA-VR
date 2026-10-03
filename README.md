# SOMA VR

A native VR mod for SOMA, created using its existing HPL3 engine. Includes 6DOF Motion controls, manual/physical interactions, native VR settings, and stereoscopic rendering.

<img width="1734" height="907" alt="exec-6791d6ff-6d40-43cb-bac3-711e245ed17b" src="https://github.com/user-attachments/assets/57e607ae-82e5-47cb-811f-e36af853c133" />

<img width="1024" height="1536" alt="exec-0732d610-9d19-434a-824e-22f9dee6b318" src="https://github.com/user-attachments/assets/da439dec-0070-4f9e-bf7b-02b16d6f9941" />


# Features and validation status

This inventory describes included implementation, not a claim that every interaction or hardware combination has passed physical testing.

## Rendering and presentation

- OpenXR stereoscopic rendering with runtime-provided per-eye FOV and recommended image sizes; asymmetric eye crops and submission.
- Tracked head rotation and translation, world-scale control and recentering.
- Native lighting, shadows and materials for story-dependent human, diving, deep-sea and amputated hand variants, including wrist closures.
- World-scale compensation for apparent hand size; S26BY adds the missing native mesh-update compensation; S26CC retains authored eye height without additional world-scale height compensation.
- Spatial subtitles and hints, subtitle distance settings, and adjustable flat-panel presentation distance.
- Presentation routes for menus, loading, startup sequences, pause and death/retry. These have received fixes but remain part of regression testing.
- Comfort controls for selected post effects, distortion, vignette and camera shake.

## Movement, body and input

- Smooth and snap turning; HMD-, body- and controller-relative movement options.
- Physical crouching and seated/standing-related options, plus button controls.
- Body heading and shoulder holster tracking/recentering logic.
- Native-styled VR SETTINGS menus, including bindings and slider settings.
- Analog grip/trigger finger animation, with additional tracked-finger paths gated by available hardware/runtime data.
- Optional tracker and eye-gaze integration. Eye gaze is not a replacement for the rendered headset FOV.

Valve Index ("Knuckles") controllers have a dedicated binding: right A = jump/accept, right B = run/back, left A = pause, left B = center camera, left stick click = crouch, hold right stick click = hand rebase. Their capacitive sensors (thumbstick, trackpad, A/B, trigger and grip) drive finger rest release, with the full, unobstructed finger range requested from SteamVR. Both trackpad presses are available in BUTTON BINDINGS. HANDS AND HAPTICS settings add smart grip (pinch grabs, finger-open release), grip pressure, point to press, creature haptics and thumb-rest button hints for Index (and Steam Frame) controllers. These have contract tests but no Index hardware test.

Quest Touch controllers do not provide independent full-finger tracking. A device claiming a tracking extension does not prove that it supplies complete, usable finger data. Broad compatibility with PSVR2, Pimax, gloves, etee or other devices is not asserted by this release.

## Physical interactions

- Physical hands with native collision queries and articulated contact handling.
- Loose-object grabbing, two-hand ownership handling and multi-body object support.
- Hinged/sliding doors, drawers, wheels, valves, levers, faucets, flush levers, buttons and special lock mechanisms.
- Finger-driven terminals and keypads, including special screen interaction paths and exit recovery.
- Physical readables such as documents and photographs, with authored interaction callbacks.
- Manual Omni-Tool carrying, slots, panel swipes, retrieval and holstering.
- Manual key-item acquisition, use, storage, retrieval, insertion and removal, with story-specific script bridges and save/reload recovery.
- Stun Baton and Tracer Fluid interaction paths; WAU healing and Site Alpha interaction paths.
- Manual cables/connectors and phone-call interaction paths.
- Head-touch flashlight gesture gated by the game's flashlight availability.
- Authored-animation suppression and physical-hand visibility rules for story sequences.
- Controller haptics whenever something is interactable, or as a reference to the shoulder stowing radius. Pulses vary in intensity depending on the interaction. 

These systems preserve authored story callbacks where implemented. Their presence is not proof of every map/save-state combination; continue reporting reproducible failures.

## Audio and dual mode

- Optional binaural HRTF processing using Steam Audio through the mod's FMOD Ex adapter.
- The adapter retains SOMA's authored attenuation, occlusion, reverb and event handling. This is not a new geometry-based acoustic simulation of every room.
- Script bridges distinguish an active VR runtime from ordinary flatscreen gameplay. Launch SOMA without injection for flatscreen; the modified scripts retain their non-VR paths.

## Download and install

Download the latest `SOMA-VR-vx.xx.zip` from this repository's **Releases** section. Consider creating a backup of your existing SOMA game folder. I tried to implement dual-mode functionality, but that hasn't been fully tested yet.

1. Download and extract the latest release of SOMA-VR in the "Releases" section.
2. Run the SOMA-VR setup.exe file.
3. Ensure that the path to your SOMA game directory, as well as the folder containing your user_settings.cfg folder are detected. If the setup isn't able to automatically detect those folders, you can manually search for them.
4. Press "Install". If done correctly, you should receive a confirmation prompt stating that the VR mod was successfully installed.
5. To launch SOMA VR, navigate to your SOMA game directory, and run the "LAUNCH-SOMA-VR.cmd" file. It should run as an administrator. Ensure that your VR headset and controllers are connected, and SteamVR or VD is running using the OpenXR or VDXR runtime.

Existing `hpl3vr_vr_settings.ini` and root hand calibration files are preserved. For a new installation, the launcher seeds the included reference hand-rig calibration only if a calibration file does not already exist. The runtime supplies default comfort settings when no settings file exists. Manual injection users should also copy `defaults/hpl3vr_hand_calibration.ini` to the game root on a fresh install.

Read [installation and troubleshooting](docs/INSTALLATION.md), [features and compatibility](docs/FEATURES.md), and [release notes](docs/RELEASE_NOTES.md).

## Compatibility and status

The supplied runtime targets one verified 64-bit Windows `Soma.exe`. Its SHA256 is `7c424e6055dda5b3aa41d4b3a9d6ffdebb8f4b50fa8a38769dee82d080b79113`. The launcher checks this before injection. Other executable versions require testing and may need different native addresses.

This mod was created using my existing hardware setup, which includes a Meta Quest 3S via Steam Link, with an RTX 5080. OpenXR runtime discovery, eye projections and render dimensions are dynamic; that does not establish compatibility with every headset, runtime or controller. Eye gaze, finger tracking and tracker support depend on both hardware and runtime exposure.

## Repository layout

- `runtime/`: cumulative player overlay, launcher, native hand assets and audio components.
- `source/`: current native payload, included support code and audio adapter source.
- `scripts/`: portable build and package-verification tools.
- `tests/`: native hand-size, menu/height and launcher regression tests, including the pre-fix hand-size fixture.
- `third_party/`: the frozen base DLL required by the current native build.
- `reference/`: Steam Audio development headers.
- `legacy/`: recovered session-4 and session-5 C++ source snapshots; not the active build.
- `docs/`: installation, feature status, build details, provenance, release notes and GitHub instructions.

See [BUILD.md](docs/BUILD.md) for the verified native build.

## Reporting a problem

Describe the issue, map, object, steps to reproduce, headset/controllers, OpenXR runtime, refresh rate and build. Include whether it was a new game or an existing save. Additionally, please upload hpl3vr.log and hpl.log for debugging.

## Credits and notices

SOMA and its original scripts and assets are by Frictional Games. This is an unofficial mod. Steam Audio is by Valve; OpenXR is a Khronos standard, with the OpenXR loader included here. MinHook notices are included.

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). GPL3.0 Licensed.

## AI Disclaimer

This project was created with AI assistance. Despite that, I've already poured over 250 hours on this project. HPL3 is not an easy engine to work with, and this mod took a lot of iterating, testing, decompilation, fixing, and testing again. 

