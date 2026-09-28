# SOMA VR

A native VR mod for SOMA, created using its existing HPL3 engine. Includes 6DOF Motion controls, manual/physical interactions, native VR settings, and stereoscopic rendering.

**Current package: S26BY, 27 September 2026.** This is a cumulative mod package, not just the latest update. A separately purchased, compatible copy of SOMA is required. The game executable and the full game are not included.

## Download and install

Download the latest `SOMA-VR-vx.xx.zip` from this repository's **Releases** section. Consider creating a backup of your existing SOMA game folder. I tried to implement dual-mode functionality, but that hasn't been fully tested yet.

1. Download and extract the latest release of SOMA-VR in the "Releases" section.
2. Extract contents of the "SOMA-VR-vx.xx" to the root of your SOMA game directory (where Soma.exe is located). Replace all files if prompted. I recommend creating a backup of your existing SOMA game folder.
3. [FIRST TIME INSTALLATION ONLY] Navigate to your user settings config file (C:\Users[YOUR_NAME]\Documents\My Games\Soma\Main), open the "YOURNAME_ID_user_settings.cfg", and make these changes:

- Engine LimitFPS="false"
- FullScreen="false"

4. Start SteamVR and ensure that your headset and controllers are connected. Ensure that SteamVR is using OpenXR as its runtime.
5. To launch SOMA VR, run "Launch-SOMA-VR.cmd" from your root game directory. If prompted with an error stating "access is denied," or "elevation required," or anything in that regard, run that same file as an administrator.

Existing `hpl3vr_vr_settings.ini` and root hand calibration files are preserved. For a new installation, the launcher seeds the included reference hand-rig calibration only if a calibration file does not already exist. The runtime supplies default comfort settings when no settings file exists. Manual injection users should also copy `defaults/hpl3vr_hand_calibration.ini` to the game root on a fresh install.

Read [installation and troubleshooting](docs/INSTALLATION.md), [features and compatibility](docs/FEATURES.md), and [release notes](docs/RELEASE_NOTES.md).

## Compatibility and status

The supplied runtime targets one verified 64-bit Windows `Soma.exe`. Its SHA256 is `7c424e6055dda5b3aa41d4b3a9d6ffdebb8f4b50fa8a38769dee82d080b79113`. The launcher checks this before injection. Other executable versions require testing and may need different native addresses.

This mod was created using my existing hardware setup, which includes a Meta Quest 3S via Steam Link, with an RTX 5080. OpenXR runtime discovery, eye projections and render dimensions are dynamic; that does not establish compatibility with every headset, runtime or controller. Eye gaze, finger tracking and tracker support depend on both hardware and runtime exposure.

## Repository layout

- `runtime/`: cumulative player overlay, launcher, native hand assets and audio components.
- `source/`: current native payload, included support code and audio adapter source.
- `scripts/`: portable build and package-verification tools.
- `tests/`: the S26BY native hand-size regression test and its pre-fix fixture.
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
