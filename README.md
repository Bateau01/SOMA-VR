# SOMA VR

SOMA VR is an unofficial mod that lets you play SOMA, Frictional Games' sci-fi horror game, in a VR headset. It runs inside the game's own HPL3 engine instead of mirroring a flat screen. SOMA renders both eyes in stereo through OpenXR, your head and hands are tracked in 6DOF, and you open doors, turn valves, type on terminals and pick things up with your own hands. The game's story, scripts and lighting are kept, and VR options live in the game's own menus under **VR SETTINGS**.

This repository is a fork of [Bateau01/SOMA-VR](https://github.com/Bateau01/SOMA-VR), the original mod (up to version 1.04-S26EB). The fork adds Valve Index controller support, finger-aware hand interactions and haptics, and a set of presence and performance options. [What this fork adds and changes](#what-this-fork-adds-and-changes) lists all of them.

<img width="1734" height="907" alt="SOMA VR gameplay" src="https://github.com/user-attachments/assets/57e607ae-82e5-47cb-811f-e36af853c133" />

<img width="1024" height="1536" alt="SOMA VR hands" src="https://github.com/user-attachments/assets/da439dec-0070-4f9e-bf7b-02b16d6f9941" />

## What the mod does

- **Stereo VR rendering** through OpenXR, using the headset's own per-eye field of view and resolution, with world-scale control and recentering.
- **Physical hands** that change with the story (human, diving suit, deep-sea suit and damaged variants), with real collisions, grabbing, throwing and two-handed objects.
- **Hands-on interactions** for doors, drawers, wheels, valves, levers, buttons, keypads and terminals, readables, the Omni-Tool, key items, cables and phones. Authored story callbacks are preserved.
- **Movement and comfort**: smooth or snap turning, head-, body- or controller-relative movement, physical crouching, and comfort toggles for screen shake, distortion, vignette and head bob.
- **VR-placed text**: spatial subtitles and hints, and adjustable distance for menus and loading screens.
- **Optional extras**: finger tracking where the controllers support it, eye-gaze and tracker integration, and binaural (HRTF) audio through Steam Audio.
- **Flatscreen still works**: launch SOMA normally without the VR launcher and the modified scripts take their original non-VR paths.

The full inventory and its testing status is in [docs/FEATURES.md](docs/FEATURES.md).

## What this fork adds and changes

Both sets of changes below are on `main`. Neither is in a published release yet.

### 1.05-S26EC: Valve Index controllers and HANDS AND HAPTICS

- **Valve Index ("Knuckles") support** at the same level as the Steam Frame path:
  - Dedicated bindings: right A = jump/accept, right B = run/back, left A = pause, left B = center camera, left stick click = crouch, hold right stick click = hand rebase.
  - The capacitive sensors (stick, trackpad, A/B, trigger, grip) open and close each finger group.
  - The full finger range is requested, so a closed fist reaches the fist pose.
  - Both trackpad presses can be remapped in BUTTON BINDINGS.
- **New VR SETTINGS > HANDS AND HAPTICS page.** It uses the per-finger sensing of Index and Steam Frame controllers; other controllers keep their previous behaviour.
  - **Smart grip:** a thumb-and-index pinch grabs (light items sit between your fingertips), and opening your fingers releases at once.
  - **Grip pressure:** squeeze strength matters for tearing, spinning wheels and holding heavy items.
  - **Point to press:** only a pointing finger presses terminals, screens and switches.
  - **Any finger on keypads:** optional; lets any extended finger press.
  - **Creature haptics:** the creature-proximity static becomes a rumble in both controllers.
  - **Button hints:** rest your thumb on A or B to see that button's current action above your wrist.

### S26ED: presence and performance

| Option | Where | Default | What it does |
| --- | --- | --- | --- |
| HEAD TAP FLASHLIGHT | HANDS AND HAPTICS | On | Tap the top of your head with an empty hand to switch the flashlight on or off, with a short confirmation pulse. |
| CLIMB LADDERS WITH HANDS | HANDS AND HAPTICS | On | Grip and pull down to climb up, push up to climb down. The stick still works, and a light pulse marks each step. |
| SHOW BODY (EXPERIMENTAL) | HANDS AND HAPTICS | Off | Shows Simon's diving-suit body at your feet, turning with you. Diving-suit sections only. |
| RENDER SCALE | VIDEO | 100% | 60-150% of the headset's recommended resolution, in 5% steps. Applies at the next launch. |
| DEPTH FOR REPROJECTION | VIDEO | Off | Sends scene depth to the VR runtime so its frame smoothing can use distance. It turns itself off for the session if anything doesn't match. |
| TEXTURE BUDGET BOOST | VIDEO | Off | Raises the engine's texture upload budget from 1 GiB to 1.5 GiB. |

### Behaviour that changed from the original mod

- **Flashlight:** toggled by tapping the top of your head (it was a grip or trigger press near your face). It can be turned off in HANDS AND HAPTICS.
- **Ladders:** your hands now stay visible on ladders while hand climbing is on.
- **Texture budget:** the boost is a menu toggle. The hidden `hpl3vr_texture_streaming.txt` file is no longer read.
- **Index controllers:**
  - The grip uses the capacitive closure of your fingers.
  - With smart grip on, just holding the controller (middle, ring and little finger closed) no longer starts a grab.
- **Point to press:** with finger tracking on, terminals and keypads need a pointing finger. Turn POINT TO PRESS off for the old behaviour.

Every new option can be switched off in VR SETTINGS. The fork's additions have automated tests (see [docs/BUILD.md](docs/BUILD.md)), but **none has been tested on Index, Steam Frame or other headset hardware yet**. Grab feel, thresholds, haptic strength, ladder feel and the body's pose still need real-world confirmation. Reports are welcome.

Release-by-release details are in [docs/RELEASE_NOTES.md](docs/RELEASE_NOTES.md).

## Install

You need an existing copy of SOMA. The mod is an overlay for your game folder, not a standalone game. Back up your SOMA folder first.

**This fork has no prebuilt release yet.** The original mod's installers are on [Bateau01/SOMA-VR Releases](https://github.com/Bateau01/SOMA-VR/releases), but they don't include this fork's additions. To install this fork, use one of these:

- **Build the installer** (Windows): follow [installer/README.txt](installer/README.txt). Copy `runtime/` into `installer/payload`, create `installer/output`, then run `installer/source/Build.ps1`.
- **Copy the overlay by hand:** copy the contents of `runtime/` into your SOMA game folder. See [docs/INSTALLATION.md](docs/INSTALLATION.md).

With the installer:

1. Run the setup and check that it found your SOMA game folder and the folder containing `user_settings.cfg`. Browse to them yourself if not.
2. Press **Install**. A confirmation appears when the mod is installed.
3. Start SteamVR (or Virtual Desktop) with OpenXR as the active runtime, connect your headset and controllers, then run `Launch-SOMA-VR.cmd` from the SOMA game folder. It runs as administrator.

If this is your first time running SOMA, launch it once in flatscreen and finish the initial menu setup before installing, so the game creates its settings files.

Your existing `hpl3vr_vr_settings.ini` and hand calibration files are kept when you update. Troubleshooting is in [docs/INSTALLATION.md](docs/INSTALLATION.md).

## Compatibility

- **Executable:** the mod targets one verified 64-bit Windows `Soma.exe` (SHA256 `7c424e6055dda5b3aa41d4b3a9d6ffdebb8f4b50fa8a38769dee82d080b79113`), and the launcher checks it before injecting. GOG and Epic builds are untested; [docs/COMPATIBILITY.md](docs/COMPATIBILITY.md) explains how to check yours.
- **Headsets:** the original mod was developed on a Meta Quest 3S over Steam Link with an RTX 5080. Eye sizes and projections come from the runtime, but that doesn't guarantee every headset, runtime or controller works.
- **Controllers:** Quest Touch controllers don't provide independent full-finger tracking, so the finger-based HANDS AND HAPTICS features don't apply to them. PSVR2, Pimax, gloves and etee are not claimed as supported.

## Building from source

The native DLL builds with Python 3 and Zig 0.13.0, and the build is deterministic:

```powershell
python -X utf8 scripts/build.py --zig "C:\Tools\zig\zig.exe" --test
```

[docs/BUILD.md](docs/BUILD.md) has the expected hash, the regression tests and how the payload is linked into the frozen base DLL.

## Repository layout

- `runtime/`: the player overlay: DLL, injector, launcher, scripts, hand assets and audio components.
- `source/`: the native payload (`s26n.c` and its `.inc` modules) and the audio adapter.
- `installer/`: the Windows installer source.
- `scripts/`: build and package-verification tools.
- `tests/`: regression and contract tests.
- `third_party/`: the frozen base DLL the build links against.
- `reference/`: Steam Audio development headers.
- `legacy/`: recovered historical C++ snapshots. This is not the active build.
- `docs/`: installation, features, compatibility, build details and release notes.

## Reporting a problem

Describe the issue, the map or object, the steps to reproduce, your headset and controllers, OpenXR runtime, refresh rate and build, and whether it was a new game or an existing save. Attach `hpl3vr.log` from the game folder and `hpl.log` from `Documents\My Games\Soma\Main`, plus the crash log if the game crashed.

## Credits and notices

SOMA and its original scripts and assets are by Frictional Games; this is an unofficial mod. The original SOMA VR mod is by [Bateau01](https://github.com/Bateau01/SOMA-VR). Steam Audio is by Valve. OpenXR is a Khronos standard, and the OpenXR loader is included. MinHook notices are included.

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Licensed under GPL-3.0.

## AI disclaimer

This project was created with AI assistance. From the original author: "Despite that, I've already poured over 250 hours on this project. HPL3 is not an easy engine to work with, and this mod took a lot of iterating, testing, decompilation, fixing, and testing again." This fork's additions were also written with AI assistance.
