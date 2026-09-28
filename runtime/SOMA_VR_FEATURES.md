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

Quest Touch controllers do not provide independent full-finger tracking. A device claiming a tracking extension does not prove that it supplies complete, usable finger data. Broad compatibility with Valve Index, PSVR2, Pimax, gloves, etee or other devices is not asserted by this release.

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

## Explicit limits

- Only the executable hash in the README is targeted by the native hooks.
- The primary documented headset test setup is Quest 3S through Steam Link/SteamVR.
- The eye-gaze option was not tested with eye-tracking hardware by this user.
- Automated callback/math tests and native save loads do not replace controller-driven playthroughs.
- The public package omits private diagnostic logs, saves and the original game executable.
