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

## Explicit limits

- Only the executable hash in the README is targeted by the native hooks.
- The primary documented headset test setup is Quest 3S through Steam Link/SteamVR.
- The user has since tested gaze-directed flashlight and DFR on eye-tracking hardware; this does not establish every eye-reactive interaction.
- Automated callback/math tests and native save loads do not replace controller-driven playthroughs.
- The public package omits private diagnostic logs, saves and the original game executable.

## Recent additions

S26CM adds an executable compatibility report and opt-in launch for engine-equivalent executables; it is not a verified GOG/Epic native port. See the compatibility guide. The root hpl3vr_vr_settings.ini is included with clean defaults.



## 1.05-S26EM additions and test status

- One Windows installer and launcher select the appropriate native DLL for the verified Steam, Epic and GOG executables. Unknown engine layouts remain blocked.
- **DYNAMIC FOVEATED RENDERING**, under EYE TRACKING, has Quality, Balanced, Performance and Custom settings in its own submenu. DFR remains experimental and off by default for new installations, requiring valid gaze and NVIDIA OpenGL `GL_NV_shading_rate_image`. Quality retains a 25-degree sharp radius and 2 x 2 peripheral shading; other presets add a 4 x 4 outer region. Optional gaze-motion protection and GPU performance measurements are available. Only the main opaque-material pass is foveated. Invalid tracking or unsupported hardware retains full quality. The user reported 10-15 FPS improvement under heavy GPU load with S26EH; further gains and visual quality from S26EI presets require headset testing.
- **TEXTURE BUDGET BOOST**, under VIDEO, is off by default. It raises the owned texture budget from 1 GiB to 1.5 GiB without changing the streaming rate. Turning it off restores the prior budget when still owned by the mod. It consumes more memory and is not a guarantee against streaming hitches.
- Initial shoulder retrieval uses consistent item-local grip anchors and initial finger-curl targets for key items, the Omni-Tool and phone. Subsequent grabs and reorientation retain the existing handling. Collision may limit finger closure. Visual grip fit still needs headset testing.
- Valid finger-joint data, unobstructed motion requests and RESET FINGER TRACKING are available independent of controller brand. Automatic rest detection only uses release signals whose meaning is known for that controller profile; other profiles use manual reset. Runtime/controller data quality still determines independent finger motion.

Reprojection/motion smoothing remains controlled by the active VR runtime. This update does not add a cross-runtime motion-smoothing switch or synthetic-frame bridge. Linux/Proton compatibility is deferred and is not claimed by this Windows package.

Automated checks cover the native DLL build, storefront guards, controller mapping, texture-budget lifecycle, grip transforms against Newton collision shapes, and real OpenGL foveation/state restoration including MSAA. The isolated game completed script/interaction regression checks. Epic/GOG reached the normal VR menu and Upsilon in the earlier headset run; the user has not yet confirmed gameplay interactions. The new DFR presets require headset quality/performance validation; the latest holster-grip appearance has not been reconfirmed.

S26EG corrects collision-hand rotation being retained in initial holster orientation and adds DFR application/fallback counts with separate prior-GL-error reporting. See the separate release notes for tests and remaining headset checks.

S26EH aligns the Omni-Tool shaft with the OpenXR grip axis and matches DFR gaze acceptance to the existing bounded eye-tracking policy, with detailed fallback counters. See the separate release notes for tests and remaining headset checks.

S26EI adds an EYE TRACKING > DYNAMIC FOVEATED RENDERING submenu with quality presets, custom radii and peripheral shading, optional gaze-motion protection and asynchronous GPU pass measurements. See the separate release notes for tests and remaining headset checks.




S26EM uses embedded shared retrieval poses only. No personal pose overrides are read. Pose capture and stutter recording controls are removed. World-scale placement retains controller-relative placement; anatomical finger fit is not dynamically adapted.
