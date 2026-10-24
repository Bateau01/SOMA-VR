# SOMA VR

A native full-VR conversion mod for SOMA, created using its existing HPL3 engine. Includes 6DOF Motion controls, manual/physical interactions, native VR settings, and stereoscopic rendering.

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
- Comfort controls for selected post effects, distortion, vignette, camera shake, and more.
- Dynamic Foveated Rendering for performance improvement under heavy GPU loads.
- Texture Budget Boost increase to have textures load in quicker.
- Custom contextualised VR hints.

## Movement, body and input

- Smooth and snap turning; HMD-, body- and controller-relative movement options.
- Physical crouching and seated/standing-related options, plus button controls.
- Body heading and shoulder holster tracking/recentering logic.
- Native-styled VR SETTINGS menus, including bindings and slider settings.
- Analog grip/trigger finger animation, with additional tracked-finger paths gated by available hardware/runtime data.
- Optional tracker and eye-gaze integration. Eye gaze is not a replacement for the rendered headset FOV.
- Finger tracking for controllers that have finger tracking capabilities, like Valve Index Kunckles, Steam Frame controllers, etc.

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

Read [installation and troubleshooting](docs/INSTALLATION.md), [features and compatibility](docs/FEATURES.md), and [release notes](docs/RELEASE_NOTES.md).

## Compatibility and status

The Windows launcher selects native support for the verified Steam executable (`7c424e6055dda5b3aa41d4b3a9d6ffdebb8f4b50fa8a38769dee82d080b79113`) or the identical Epic/GOG executable (`395cd54830c8e66e22166e71ac6fe95fd3bb5433b898737836744a6d178a0a6a`). Other engine layouts require a separate native port. See the test limits below.

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

# FAQ:

- Before reading this, ensure that you've reviewed your VR settings, as well as the button layout and body layout images shown on the GitHub page.

**Q: "My VR hands are stuck and won't come back!"**
A: Hold down your right thumbstick click for a second and it'll reset the position of your hands. This is shown on the button layout image as well as the "BUTTON LAYOUT" setting in your VR settings, under "CONTROLS".

**Q: "How do I interact with the chair at the lab?" or "How do I get into this vent?"**
A: Bring your VR hands and feel around the chair, like the armrest, or feel around the ledge of the vent for a haptics vibration/pulse in your controller, once you feel that pulse, press grip and your character will perform the action. As of v1.0.9, you can now also see guiding holograms for key-items, Omni-Tool, and hand interactions. When you have a key-item or Omni-Tool held, you can now see a hologram of where that key-item can be used. For the Omni-Tool, you can see if you can place an Omni-Tool in a slot when held. For hand holograms, you can see where you can place your hands to perform a interaction, like climbing into vents, or interacting with pilot seat chairs, ladders, etc.

**Q: "My character isn't performing this [X] action!"**
A: You're probably missing something or haven't gone through a scripted sequence.

**Q: "I have limited space and I find interacting with things using my VR hands to be difficult."**
A: You can enable remote grabbing, terminal laser pointer, as well as an interaction laser pointer - all found in your VR settings, under "GAMEPLAY".

**Q: "[X] image effects are too jarring for me, how can I disable them?"**
A: In your VR settings, under "VIDEO", you have the option to selectively disable/enable various image effects, like disabling head bobbing, chromatic aberration, screen shake, distortions, etc, according to your preference.

**Q: "My shoulder holsters are too difficult to reach and feel out of place!" or "My VR camera/perspective doesn't seem to align with my view/character!"**
A: Recenter your view by pressing the dedicated VR controller bind for it. Normally, it's "Y", but for some controllers, that bind may be different. Check the button layout image on the GitHub, or view the "BUTTON LAYOUT" VR settings option, under "CONTROLS".

**Q: "My controller button layout isn't comfortable. How can I change it?"**
A: You can change your button layout in the "BUTTON LAYOUT" VR setting under "CONTROLS".

**Q: "The scale of objects look too large!" Or "The distance for subtitles/hints are too far/close!"**
A: You can change your world scale, subtitle distance, and 2D window distance to be closer or further away in your VR settings, under "GAMEPLAY". Each of them have their own dedicated sliders.

**Q: "My game stutters a lot, despite having a high-end PC!"**
A: SOMA's HPL3 engine isn't well optimised. Physics don't utilise all of your CPU cores, and doesn't support multithreading. So, in heavy physics-demanding areas, your CPU frametime may spike, which can cause FPS drops in some areas. Some areas are also taxing on your GPU, like Site Delta. I recommend enabling "OpenGL Triple Buffering" in your Nvidia Control Panel, or the AMD equivalent. You also have access to Dynamic Foveated Rendering, found in the "EYE-TRACKING" VR setting. If nothing else, you can still use reprojection.

**Q: "My game doesn't feel smooth!"**
A: SOMA's physics run at 60Hz, so things like turning, using your VR hands, performing interactions, enemies, etc, may not be as smooth as you'd like it to be. This is why I implemented "120HZ PHYSICS," found in your VR settings, under "GAMEPLAY". This setting increases that physics rate from 60Hz to 120Hz, and includes fixes that would have normally broken the game with 120Hz Physics, so everything should feel a lot smoother. However, using this mode may cause more stutters and hitches, as physics now has to update twice as often compared to 60Hz. Also, ideally, recommend using 120Hz as your VR headset's display refresh rate, if possible.

**Q: "I'd like to stream my gameplay, but my desktop view is black!"**
A: Enable "DESKTOP MIRROR" in your VR settings, under "VIDEO". You might need to restart SOMA VR for it to take effect.

## AI Disclaimer

This project was created with AI assistance. Despite that, I've already poured over 250 hours on this project. HPL3 is not an easy engine to work with, and this mod took a lot of iterating, testing, decompilation, fixing, and testing again. 
