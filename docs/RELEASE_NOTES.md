# SOMA VR 1.05-S26ER

All 52 authored retrieval poses (26 profiles, both hands) are now shared defaults only. The runtime no longer reads personal item-grip files. Installing this update is sufficient, even if an older hpl3vr_item_grips.dat exists in the game folder. No separate pose file or manual replacement is required.

The poses remain embedded in the Steam and Epic/GOG runtimes and update with the mod. Controller-relative placement, item/state selection, initial finger poses and subsequent normal regrabbing are retained from S26EL.

Removed the temporary TEST TOOLS submenu, pose capture commands, pose-file reading/writing and stutter recording buffer/export paths. The existing movement-stutter fix remains. Normal logging, performance measurements, finger-tracking rest calibration and gameplay settings are retained.

Older capture and diagnostic files are left untouched as inactive historical data; they cannot override the shared poses. Original authoring captures remain archived for future development.

Validation covers all 52 shared poses with a conflicting legacy file present, native Newton placement/orientation tests, isolated Steam/store game profile and menu compilation tests, and installer install/update/uninstall checks. Full normal-game headset confirmation remains pending. World-scale placement adjusts the anchor, but exact anatomical finger fit is not automatically adapted.

Release notes are separate from the installer payload. The root VR settings INI is included; existing settings are preserved. This is a cumulative 1.04 update.

---
# SOMA VR 1.05-S26ER

Includes all 52 authored retrieval poses: left and right hands for 26 item profiles, including the phone, all four Omni-Tool models, both ARK models and formatted/unformatted chips.

Poses are distributed defaults embedded in both the Steam and Epic/GOG runtimes. Retrieval uses the captured contact position, controller-relative orientation and initial finger pose. Ordinary subsequent grabbing and reorientation remain available. Model/state selection uses the existing native script body lookup; it does not replace inventory or story-state ownership.

Existing personal grip captures remain overrides and are preserved during installation. The separate hpl3vr_item_grips.dat contains the complete 52 captures; the author can copy it into the game folder to replace older local captures. Other players do not need this separate file.

Placement uses current object bounds and the current controller basis across world scales. This does not resize objects or guarantee identical anatomical finger fit when the world and hands have different scales.

Validation includes compiled production grip tests, native Newton placement/rotation tests and isolated SOMA script/body-profile tests for Steam and the store executable. These checks do not replace headset confirmation of every retrieved pose in normal gameplay. The installed game and authoring captures were not updated by packaging.

The installer retains existing settings and includes the root VR settings INI. Release notes are supplied separately and are not installed in the game folder. Existing S26EK stutter improvements are retained.

---
# SOMA VR 1.05-S26ER

Removes an obsolete hardware write-watch diagnostic from the shared Steam/Epic/GOG base. It armed debug registers at startup, then enumerated, suspended and resumed game threads every 300 VR frames. The supplied S26EJ recording contains nine 60–68 ms frame intervals at exactly those 300-frame boundaries, in both gameplay and pause menus. The measured scene and physics work did not explain those delays.

Startup watch registration, its own-thread self-test, periodic rearming and the dormant frustum-watch shortcut are disabled. The thread-arming routine also returns without doing work. Guarded byte checks reject an unexpected base DLL. This retires diagnostics; it does not remove the resolution correction or change physics timing, hand collision, DFR, interactions or item grips.

Validation: byte-for-byte comparison against S26EJ for both DLLs requires all changes to remain within these four watch paths and the PE checksum. Production-code recorder/grip/phone checks, native Newton grip tests, storefront guards, isolated SOMA script regressions and installer tests are recorded separately. The installed game is not overwritten during preparation.

The headset timing improvement still needs an S26EK recording. Use VR SETTINGS > TEST TOOLS to record the same movement/turning sequence, then stop and save. This targets the identified periodic stall; it does not claim to eliminate every streaming or rendering hitch.

Install using the included installer, then the normal Launch-SOMA-VR.cmd. Existing player settings and captured item grips are preserved. Release notes are provided separately and are not copied into the game folder. The root VR settings INI remains included. This is a cumulative 1.04 update.

---

# SOMA VR 1.04-S26EJ

## Movement/turning stutter recording

In VR SETTINGS > TEST TOOLS, choose START STUTTER RECORDING. Resume and reproduce the hitch, then return to the same page and choose STOP AND SAVE RECORDING. Send `hpl3vr_stutter.bin` and `hpl3vr.log` from the game folder. Save promptly after reproducing: the recorder retains the newest 32,768 samples, usually about one to three minutes depending on refresh rate and render passes. A new Start clears the in-memory recording; Save replaces the previous capture file. Restarting SOMA starts with recording off.

The recorder keeps normal frames as well as slow ones so the local baseline and events around a hitch can be compared. It records physics pre/update/post timing, hand root/rig/finger and acquisition work, held-object work, scene-render call timing, OpenXR wait/pose timing, input sticks, held-hand flags, presentation state, frame/physics counters and world identity. It performs no disk writes, formatting, allocation, waits or log output in the sample path. A busy buffer skips a sample and records the dropped count. It adds timing calls while enabled; leave it off for normal play.

These are elapsed CPU-side wall timings, not CPU busy time or GPU timings. Rendering may wait on the driver; OpenXR waiting can be normal pacing. Time outside measured sections may include engine scripts, streaming, scheduling or other work. This build does not claim to have identified or fixed the reported one-frame hitch. The included source tool `scripts/analyze_stutter.py` groups render calls by XR frame and creates a JSON summary with nearby physics events and the largest intervals. No Python installation is needed to record or send the file.

## Save your preferred initial item grip

1. In gameplay, retrieve the phone, Omni-Tool or registered shoulder key item. Regrab/reorient it until the selected hand holds it where you want. Use one hand on the item while capturing.
2. Open VR SETTINGS > TEST TOOLS and select SAVE LEFT ITEM GRIP or SAVE RIGHT ITEM GRIP.
3. Resume gameplay, hold the item still with the desired finger articulation, and wait eight seconds of tracked, unpaused gameplay. A confirmation vibration and the status on the test page report success; failure retains the previous saved profile.
4. Stow and retrieve the same item with the same hand to check the result. For the story phone, check the next retrieval/call; this does not add a new phone inventory or change story callbacks.

Profiles save to `hpl3vr_item_grips.dat` in the game folder, separately per logical item and hand. They contain controller-relative item orientation, a normalized item contact position, and twenty joint-curl values. Retrieval keeps controller orientation, including an inverted shoulder reach. The contact solver still enforces the held object's geometry, so the captured curls are an initial pose target rather than a collision bypass or a permanently frozen hand. Thumb spread and arbitrary bone transforms are not independently recorded. Ordinary regrabs, drops, slot insertion/removal, ownership and story scripts retain their existing behavior.

Saving uses a checked/versioned file and an atomic replacement. Unsupported/corrupt profiles fail closed to the normal grip defaults. Capture rejects unknown items, absent tracking and the same item held in both hands; an in-progress capture fails on world change. No new world/body scans run for this feature. The installer does not ship or overwrite this personal file. To restore all default grips, close SOMA and rename this file. Do not rename the normal hand calibration file.

## Lighter phone Accept touches

The shared phone hit test now accepts a fingertip skin gap up to 12 mm instead of 3 mm. An approach that first touches just outside the button remains armed so sliding onto Accept can work without fully withdrawing first. The visible Accept/Decline regions, rear-surface rejection and withdrawal/re-touch protection remain. This covers the apartment, subway and laboratory phones through their existing shared helper. Terminal/tablet detection and authored call/display scripts are unchanged.

## Validation and limits

Both Steam and Epic/GOG DLLs build. Production-code fixtures passed 1,859 checks covering phone contact/rearming, per-item/hand profile persistence, invalid profiles and failed writes, initial grip geometry, capture gates and bounded recording. Existing real-Newton holster tests passed 691 checks, including 450 controller/hand orientation combinations; the thread-scoped pose seed and 1,561 store guard checks passed. The isolated SOMA script VM completed the existing interaction regressions, settings navigation and native Start/Save recorder commands. The isolated recording verified native render sample export; it was not a reproduction of the user's headset hitch or a physical-hand performance test.

The saved grip's physical feel, all three phone touch sequences and the reported movement/turning stutter still require headset testing. This is a cumulative test build, retaining the S26EI DFR settings and previous fixes. Installed game files were not replaced during preparation. Installer update/personal-file preservation checks are included in the separate validation report. Release notes stay outside the installed game payload. Public version remains 1.04; internal build is S26EJ. GPLv3 licensing and existing credits remain unchanged.

---

# SOMA VR 1.04-S26EI

## Dynamic foveated rendering menu

DFR is now under VR SETTINGS > EYE TRACKING > DYNAMIC FOVEATED RENDERING, with its own submenu and a dedicated BACK row. The existing enabled/disabled preference is retained. New installations still start with DFR disabled.

| Preset | Sharp radius | Outer region starts | Outer shading | Gaze protection |
| --- | --- | --- | --- | --- |
| QUALITY (default) | 25 degrees | 45 degrees (unused at 2 x 2) | 2 x 2 | Off |
| BALANCED | 20 degrees | 40 degrees | 4 x 4 | On |
| PERFORMANCE | 15 degrees | 35 degrees | 4 x 4 | On |

All presets shade at full rate around gaze, with 2 x 2 shading outside the sharp region. Balanced and Performance add 4 x 4 shading beyond their outer boundary. Larger blocks reduce shader work but can make peripheral detail and aliasing more visible. Changing individual controls switches to CUSTOM. SHARP REGION RADIUS spans 10-35 degrees; OUTER REGION START spans 25-60 degrees and stays at least 5 degrees outside the sharp radius. The outer boundary has no effect when OUTER SHADING is 2 X 2. RESTORE DEFAULTS restores Quality tuning and disables measurements without changing the DFR enable toggle.

The full-quality region now uses an angular cone about gaze, so it remains conservative when looking toward the edge of an asymmetric eye projection. A tile safety margin remains. Quality retains the previous nominal 25-degree radius and 2 x 2 periphery. Optional GAZE MOTION PROTECTION widens the protected region for delayed samples or rapid gaze changes and gradually returns after movement stops. It never narrows the requested region. This is a bounded safety margin, not a calibrated eye-motion predictor. Invalid/stale tracking still renders at full rate. More aggressive tuning requires headset visual evaluation.

## Performance measurements

PERFORMANCE MEASUREMENTS enables sparse, asynchronous GPU timestamp samples around the main opaque rendering pass. Samples are written to hpl3vr.log as S26EI DFR GPU entries, split into OFF, APPLIED and FALLBACK, with resolution, settings, mean and maximum pass time. Settings/toggle changes invalidate older pending samples. Readback only occurs when ready; a busy query ring skips samples instead of waiting. No glFinish or extra scene rendering is introduced. Measurements are off by default. These are per-eye opaque-pass GPU times, not total frametime or FPS.

For comparison, enable measurements, spend roughly 10 seconds in a stable scene with DFR off, then enable DFR with Quality, Balanced and Performance in turn. Keep render resolution and viewpoint comparable. Compare GPU frametime in the runtime overlay as well. Turning measurements off avoids issuing new timestamp queries.

The user reported 10-15 FPS improvement under heavy GPU load in S26EH. That report does not establish an additional gain for these presets. A real-GPU synthetic fixture measured fewer fragment shader invocations for Balanced and Performance than Quality, with correct state restoration and 4x MSAA. Whole-game performance and visual comfort for the new presets remain to be tested in a headset.

DFR continues to affect only the main opaque-material pass. Lighting, shadow maps, transparency and post effects remain full rate. Extending into additional passes requires measured benefit and separate visual validation; this build does not apply aggressive shading to them speculatively. Reprojection remains runtime-controlled.

## Validation and package

Both Steam and Epic/GOG native DLLs build successfully. Tests cover 3,765 tuning/guard cases, timestamp boundaries and invalid gaze, the busy-GPU query queue, nested timestamp reservations, three-preset GPU shading and state restoration including query-buffer binding and MSAA. The isolated SOMA script VM completed the existing interaction regressions and new preset, configuration round-trip, invalid-value and Back-navigation checks without script errors. Installer install/update/uninstall and previous-version upgrade checks preserve personal settings.

This cumulative Windows installer includes the S26EH Omni-Tool grip correction and all earlier features. Installed game files were not modified during preparation. Release notes remain outside the game payload; GPLv3 licensing and the user's GitHub documentation/credits baseline are retained. Linux remains deferred.

---

# SOMA VR 1.04-S26EH

## Omni-Tool shoulder retrieval

Corrected the authored Omni-Tool profile: its head points along local -Z, which must follow OpenXR grip -Z (the shaft direction through closed fingers). The previous profile rotated this axis onto grip +Y, leaving the tool almost horizontal when held upright. S26EH removes that quarter-turn. The previous correction for collision-hand rotation is retained. Initial contact anchor and finger pose remain consistent; later regrabs remain contact-driven.

The expanded native Newton fixture checks both hands, inverted reaches, calibration, collision offsets and the actual shaft-axis relationship. S26EG fails the new orientation expectation; S26EH passes all 691 checks, including 450 orientation combinations. These are transform tests, not visual confirmation of the corrected grip in a headset.

## Dynamic foveated rendering

The reported S26EG session applied DFR on 1,542 of 25,200 passes. Of the remaining passes, 21,249 failed the gaze check and 2,408 were outside the eligible render scope. There were no DFR setup errors. This establishes poor activation coverage; it does not measure GPU savings.

The DFR consumer used a stricter timestamp window than the gaze producer and gameplay gaze features: 50 ms past / 10 ms future versus 100 ms either way. It now uses the same bounded window, retaining the head pose sampled at the gaze timestamp. Invalid, inactive, nonfinite or out-of-window samples still render at full quality. Counters now distinguish lock contention, invalid tracking, past/future timestamp rejection and samples accepted by the corrected window. The prior log did not distinguish those reasons, so the exact share of rejections fixed needs a new hardware run.

Actual production gaze acceptance is tested at timestamp boundaries, with head rotation, invalid tracking and nonfinite poses (34 checks). The old consumer fails these tests. The existing real GPU fixture verifies reduced fragment shading, invalid-gaze fallback, asymmetric views, MSAA, GL error handling and state restoration. DFR still only reduces shading in the main opaque-material pass. It does not reduce CPU physics/interaction work, and no whole-game FPS improvement is claimed from these tests.

## Package and testing

This cumulative Windows package retains Steam/Epic/GOG support and existing preferences. DFR and texture boost remain off by default for a clean installation. Runtime-controlled reprojection and deferred Linux work are unchanged. Release notes stay outside the installed game payload.

Hardware check: retrieve the Omni-Tool with an inverted wrist, bring it forward, rotate it upright, and check both hands and later regrabs. Compare DFR off/on in the same scene using GPU frametime. New gaze counters identify why it falls back without logging every frame. Updated headset alignment and performance remain to be confirmed.

---

# SOMA VR 1.04-S26EG

## Holster orientation

Initial retrieval now uses the tracked controller's orientation directly. S26EF included the collision-resolved hand rotation when preparing the item, while the existing latch also preserved that hand offset. A hand rotated by shoulder contact could therefore leave the held item tilted after the controller returned upright. The correction keeps the physical contact position but removes that extra rotation from the initial item orientation. Normal world grabs and later regrabs are unchanged.

An expanded native-Newton fixture reproduces the old failure and passes with the correction: 691 checks, including 450 orientation cases across both hands, inverted reaches, hand calibration and collision-root rotations. This verifies the transform composition, not headset appearance of every item profile.

## DFR status and error attribution

The reported S26EF session did activate DFR at 3512x3620 with valid gaze and 16x16 shading-rate tiles. The log has no comparative GPU timings and does not establish an FPS benefit. The first implementation still only reduces peripheral shading in the main opaque-material pass; it does not reduce physics/interaction CPU work. A visible difference near the gaze centre is not expected.

S26EG records application and fallback counts periodically and when toggling DFR. OpenGL errors already present before setup are now distinguished from errors caused during setup. A prior error no longer discards a healthy shading-rate texture. Actual setup failures still render full-rate and recover on a later pass. Real GPU checks cover prior-error separation, injected setup failure, state restoration, asymmetric projections and 4x MSAA.

Reprojection/motion smoothing remains controlled by the VR runtime. There is no custom reprojection toggle or generated-frame bridge in this package. These logs do not establish whether runtime motion smoothing was active.

## Installation and testing

This cumulative Windows installer retains the S26EF Steam/Epic/GOG selection, controller generalisation, initial holster grips, optional texture budget and experimental DFR. DFR and texture budget are off by default; existing preferences are preserved. Linux remains deferred. Release notes are separate from the installed game payload.

Headset check: draw the Omni-Tool with the wrist inverted over the shoulder, bring it forward and rotate the wrist, then stow/retrieve and regrab with the other hand. Check DFR off/on in the same scene and resolution using GPU frametime, rather than judging only image sharpness. The new log counters identify whether DFR remains active or falls back; they are not performance measurements.

---

# SOMA VR 1.04-S26EF

## 1.04-S26EF additions and test status

- One Windows installer and launcher select the appropriate native DLL for the verified Steam, Epic and GOG executables. Unknown engine layouts remain blocked.
- **DYNAMIC FOVEATED RENDERING**, under VIDEO, is experimental and off by default. It requires valid eye gaze and the NVIDIA OpenGL `GL_NV_shading_rate_image` extension. The central 25-degree radius retains full shading resolution; peripheral shading is reduced in the main opaque geometry pass. Other passes, including shadows, menus and post effects, retain their normal rate. Unsupported hardware, stale gaze or invalid projections use full-rate rendering. This is not a universal GPU backend or a demonstrated whole-game FPS improvement.
- **TEXTURE BUDGET BOOST**, under VIDEO, is off by default. It raises the owned texture budget from 1 GiB to 1.5 GiB without changing the streaming rate. Turning it off restores the prior budget when still owned by the mod. It consumes more memory and is not a guarantee against streaming hitches.
- Initial shoulder retrieval uses consistent item-local grip anchors and initial finger-curl targets for key items, the Omni-Tool and phone. Subsequent grabs and reorientation retain the existing handling. Collision may limit finger closure. Visual grip fit still needs headset testing.
- Valid finger-joint data, unobstructed motion requests and RESET FINGER TRACKING are available independent of controller brand. Automatic rest detection only uses release signals whose meaning is known for that controller profile; other profiles use manual reset. Runtime/controller data quality still determines independent finger motion.

Reprojection/motion smoothing remains controlled by the active VR runtime. This update does not add a cross-runtime motion-smoothing switch or synthetic-frame bridge. Linux/Proton compatibility is deferred and is not claimed by this Windows package.

Automated checks cover the native DLL build, storefront guards, controller mapping, texture-budget lifecycle, grip transforms against Newton collision shapes, and real OpenGL foveation/state restoration including MSAA. The isolated game completed script/interaction regression checks. Epic/GOG reached the normal VR menu and Upsilon in the earlier headset run; the user has not yet confirmed gameplay interactions. DFR gaze behavior and initial holster-grip appearance still require headset validation.

The S26EE MSAA fixes and existing menu/ultrawide presentation corrections are retained. The installer preserves personal settings and excludes release notes from the game payload.

---

SOMA VR 1.04-S26EF

MSAA gameplay image-copy correction

- Extend multisample handling to both finished gameplay eyes. Resolve the full source at native size, then apply the existing per-eye crop and resize to the VR target.
- Keep the single-copy path when the window has no multisampling. Reuse the native-size intermediate buffer rather than allocating one per frame.
- Select the destination explicitly, preserve scissor/read/draw state, and reject capture errors instead of reporting success. Bounded EYE COPY diagnostics identify the eye, sample count, crop and error.
- Retain S26ED menu startup correction and all existing 1.04 functionality. Installer preserves personalized settings. Release notes are separate.

Evidence: player logs now confirm two samples in the window framebuffer. The player confirms disabling MSAA resolves the frozen-menu gameplay issue. The gameplay capture previously performed the same unsupported resolve-plus-resize operation corrected in the menu path.

Validation: real OpenGL tests at 1080p, 1440p and ultrawide sizes, with zero/two/four samples. Verified distinct left/right pixel contents and crops through repeated menu/gameplay cycles, state restoration and incomplete-framebuffer rejection. Existing window/menu regression groups passed. These are isolated rendering tests, not a full headset playthrough; MSAA-enabled gameplay confirmation on the affected PC remains required.

# SOMA VR 1.04-S26EB

- Generalized finger tracking: accepts active, valid OpenXR hand-joint data without an Index/Steam Frame controller whitelist. All controllers use the authored resting pose and curl path. The FINGER TRACKING toggle retains grip/trigger fallback when disabled; unavailable/invalid skeletal data also falls back. Runtime-estimated poses may still be unsuitable on controllers without individual finger sensing.
- RESET FINGER TRACKING now supports compatible skeletal controllers generally. Select START RESET, release fingers during the five-second countdown, and hold a steady resting pose. Controllers without capacitive contact actions can use this explicit reset. Known touch/press, unstable or saturated input rejects the sample; failure retains the old reference. The reference is session-only and is cleared when the controller profile changes.
- Neutral controller wording: D-PAD LEFT, D-PAD UP, D-PAD DOWN, D-PAD RIGHT, LEFT SHOULDER and RIGHT SHOULDER. No headset brand appears in the reset menu.
- Expanded the button remapper to accept both shoulder buttons, the remaining D-pad directions, right X/Y, View and Menu when exposed by the supported input profile. Existing six default assignments and saved source IDs are preserved. Extra buttons have no default gameplay action until rebound.
- Removed temporary skeletal joint dumps, alternate-motion-range comparison queries and human-mesh bone-pose captures. Retained bounded startup, capability and reset-result messages.
- Retains the verified human-pinky repair, lighting/shadow correction and exact desktop client-size correction from 1.03-S26EA. No hand mesh, weights, material or texture files changed in this update.

Validation: all 17 automated regression groups passed, including live SDL client-size tests at 1920x1080, 2560x1440 and 3440x1440, OpenXR failure/fallback simulations, skeletal geometry/publication, delayed reset, all fourteen button sources, saved assignments, menu layout and mesh consistency. The user's latest S26EA log recorded startup correction from 2560x1431 to 2560x1440 and four native menu transitions with matching 2560x1440 client, drawable and graphics-owner dimensions. The user confirmed the pinky repair and finger reset worked.

These tests do not certify every headset/controller driver. Third-party controllers such as etee require their runtime to expose usable XR_EXT_hand_tracking data and supported gameplay actions; no etee hardware test was performed. The shared neutral-pose mapping and new shoulder-button assignments still need hardware confirmation. Runtime-generated coupling between fingers cannot be reconstructed into independent sensor measurements by the mod.

Install/update using the included installer. Personal VR settings are preserved. Release notes remain a separate download and are not copied into the game folder.

# SOMA VR 1.03 (S26DF)

- Moved DOUBLE-TAP SPRINT to VR SETTINGS > CONTROLS, directly above BUTTON BINDINGS. BACK and all options have separate rows.
- Includes the ARK wake-up crash fix from S26DD. The Phi launch-button reference is cleared across map and save transitions.
- The ending completed without crashing in the author's retest. Double-tap sprint was also confirmed working.
- Release notes and historical build-change documents are no longer installed into the game folder. Release notes are provided separately for GitHub.

This is a cumulative release. Existing features, launcher settings preparation, ultrawide support and the root VR settings INI are included. The installer preserves existing customized settings.

Connector changes from S26DC are retained; their latest hardware retest is still pending.


# SOMA VR 1.03 (S26DE)

- Fixed DOUBLE-TAP SPRINT overlapping BACK in VR SETTINGS > GAMEPLAY. BACK now occupies its own row.
- Includes the ARK wake-up crash fix from S26DD. The Phi launch-button reference is cleared across map and save transitions.
- The ending completed without crashing in the author's retest. Double-tap sprint was also confirmed working.
- Release notes and historical build-change documents are no longer installed into the game folder. Release notes are provided separately for GitHub.

This is a cumulative release. Existing features, launcher settings preparation, ultrawide support and the root VR settings INI are included. The installer preserves existing customized settings.

Connector changes from S26DC are retained; their latest hardware retest is still pending.


# 1.02-S26DD

SOMA VR 1.02-S26DD

Cumulative over 1.02-S26DC. Installed game files and original saves were not changed.

ARK wake-up crash
The crash log retains Phi's launch-button body 0x116c70b40 after the Phi world is replaced by the ARK world. The legacy fingertip debounce path passes this retained body to NewtonCollisionPointDistance when hands resume. The recorded fault is Newton.dll+0x90b4 in the matrix operation called at +0x36be2 by the nearest-point routine. This is a concrete stale-world pointer defect consistent with the crash; the old log does not contain fault registers for a complete crash dump.

The correction invalidates the legacy button latch, pass body, pending poke references, near-control reference and related contact presentation state at ordinary map departure, save/title/new-game reset, and raw physics-world replacement. Cleanup only clears mod-owned references; it makes no native queries or object destruction during teardown. Normal in-world button debounce, collision, grabbing and physics cadence are unchanged. This applies to all these transitions, not an ARK-specific map exception.

Rendering
The user confirmed S26DC credits enter 2D and the ARK returns to 3D. Credits use the shared flat presentation path and inherit its ultrawide handling. No rendering, FOV, viewport or hand-material change is made here. The native human-hand Root_Ctrl warnings also occur during a direct ARK load that completed without a crash; they are not being treated as proof of the crash cause.

Validation
The corrected DLL compiled with warnings treated as errors. 49,106 hand-scale checks and 299 extracted button-lifetime/debounce and transition-wiring checks passed. The lifetime tests seed stale identifiers and verify the actual consumer never queries them after cleanup, while fresh-button debounce still works. A direct ARK replay with the unchanged baseline completed the wake-up without crashing (user confirmed); that route does not recreate the retained Phi launch-button reference. The original Phi-through-credits-to-ARK route still needs hardware retesting on this corrected build. Full installer install/reinstall/uninstall checks are recorded with the source evidence. No exhaustive crash-free guarantee is claimed.

Installation
Close SOMA. Extract SOMA-VR-1.02-S26DD-Installer.zip and run SOMA-VR-1.02-S26DD-Setup.exe, then choose INSTALL / UPDATE / REPAIR. Includes the full cumulative mod, updated launcher and root hpl3vr_vr_settings.ini. The installer preserves existing customized settings. The source archive also contains the runtime overlay for manual copying; preserve your customized INI before overwriting it.

Retest
Use the Phi save before the final button, press it with your VR hand, proceed through the credits and finish waking in the ARK. Directly loading the ARK save alone does not test the stale-button transition. The previous connector changes are retained and remain awaiting your hardware test.


# 1.02-S26DC

SOMA VR 1.02-S26DC

Cumulative over 1.02-S26DB. Manual installation package; your installed game and saves were not overwritten.

Phi final launch
Physical VR hands become visible when Catherine finishes asking Simon to press the launch button. The temporary replacement suppresses the authored hand mesh. The native launch-button callback ends that exception immediately when pressed, restoring the native seated ending/cutscene policy. The window persists in new saves and can be recovered from the enabled button and seated camera state in older saves. Map departure clears the override. Crane operation and the remainder of the ending retain their native sequence.

Credits and ARK epilogue
Added explicit flat presentation at the authored credits start. Both natural completion and skipping use the same credits-stop/map-change path. VR promotion waits for the ARK destination map to enter, report ready and complete three physics steps, using the existing destination handoff. Pause/resume cannot prematurely promote the credits. Title/new-game/save-load events clear the credits state. This does not reset the player or pretend that credits start is a new game.

Connectors
The connector-only auxiliary selection now also samples up to eight recent physical contact points on the hand, including finger contact beyond the palm. Stale contacts, contact points more than 12mm from the current hand mesh and duplicate origins are rejected. The extra rays run only on a fresh connector grip attempt, bounded to 54 total rays including the existing palm sample. Only a verified auxiliary area pointing to a same-owner jointed carry assembly can win this route. Native socket springs, detach callbacks, cable joints, doors/drawers and readable priority are preserved. This addresses a remaining palm-only coverage limitation; the latest capped log cannot prove that it explains every missed connector grab.

WAU
The Alpha insertion correction that you reported working is retained unchanged.

Validation
Native DLL build passed with warnings treated as errors. 49,106 hand-scale checks; 60 extracted credits-lifecycle checks; 10 extracted connector-origin checks; 17 auxiliary handoff checks and four actual Upsilon map/asset mappings; 93 direct cable selection checks; 19 mechanism contact checks; 77 readable-priority checks; 675 sprint checks; 84 insertion-boundary checks; 614 mouth-permission checks; 45 fist-point checks passed. Authored Phi event ordering and destination readiness assertions passed. SOMA's native script loader completed the updated Phi map script without a script compile error in a separate test profile. The isolated launch did not complete a playable sequence and is not an end-to-end test. No headset confirmation of this build's final button, credits or connector feel has been obtained. Installer full-payload tests are recorded alongside the package.

Install
Close SOMA, extract the installer ZIP, run SOMA-VR-1.02-S26DC-Setup.exe and choose INSTALL / UPDATE / REPAIR. Full cumulative mod and launcher included, with clean root hpl3vr_vr_settings.ini. Installer preserves existing customized settings. Source archive includes the full player overlay and build source.

Hardware check
At Phi, finish loading the gun, wait for Catherine's prompt, press the physical launch button, and check that the native ending resumes. Let credits run (or skip), then verify the ARK wake-up is 3D. Recheck Upsilon connector grips around the handle, including finger-side contact, then release and regrab.


# 1.02-S26DB

SOMA VR 1.02-S26DB

Cumulative over S26DA. Prepared for manual installation; installed game files and saves were not overwritten.

DOUBLE-TAP SPRINT
New optional GAMEPLAY toggle, uppercase, off by default. Push the left stick forward, return to neutral, then push forward again within 0.35 seconds. Sprint remains active while the stick is moved and clears when it returns to neutral. Menus, non-gameplay states, map transitions, invalid input and tracking gaps clear the gesture. Uses OpenXR timestamps, not a headset-specific frame count. Existing Run button and native sprint eligibility remain in use. Saved in the player's SOMA_VR_Comfort/DoubleTapSprint setting.

Connectors
The recorded Upsilon interaction accepted an InteractAux area but the VR handoff searched only for a hinge/slider. Jointed carry bodies were also rejected by the loose-contact extraction bridge. Added a narrowly gated handoff from an accepted authored auxiliary area to its published parent/main body, with connected-assembly proof. The native OnInteract executes once and still starts the stock sticky-area spring and its detach callback. Auxiliary cable volumes now take priority over incidental housing/mechanism selection on a fresh grip. Direct physical contact with a native carry body can also use the jointed extraction path. No cable joints are removed and no story callback is manually skipped. Both Upsilon pairs were checked against their map, auxiliary, entity, main-body and ball-joint definitions. Other supported carry assemblies share the code; this is not hardware certification of every connector.

WAU Alpha
The S26DA measurements put several actual fist attempts 19-22 cm in front of the old target and up to about 11 cm laterally away. The target used the inner jaw lip bones rather than the farther-forward outer fleshy opening. Alpha's target is moved 30 cm forward, still behind the outer opening, and its insertion radius is 12 cm with a 14 cm collision-entry corridor. The physical closed fist must reach the insertion volume; only the left hand can trigger Alpha. Authored eligibility and sequence remain in charge. Ordinary healing flowers retain their separate geometry; an Alpha measurement cannot establish their correct target.

Validation
Native build and 49,106 hand-scale regression checks passed. Extracted production-function tests: 675 sprint timing/state checks across 60/72/75/80/90/120/144 Hz; 93 direct cable selection checks; 17 authored cable handoff checks; 19 door/slider transaction checks; 84 insertion-boundary checks; 614 mouth collision-permission/lifecycle checks; 45 fist-point checks; 77 static-readable priority checks. Four reported Upsilon cable mappings verified from game XML. Ghidra confirmed CanInteract/OnInteract are script dispatchers; PlayerState_Interact.SetupInteractVars starts the authored sticky spring. These isolated/mocked checks do not prove the in-headset feel, Alpha activation or release/regrab behavior. No live headset test was performed for S26DB.

Installation
Close SOMA. Extract the installer ZIP, run SOMA-VR-1.02-S26DB-Setup.exe and choose INSTALL / UPDATE / REPAIR. This is the full cumulative package, not a launcher-only update. The installer preserves customized settings; the clean root VR INI remains included. The installer retains its existing legacy long-path limitation for deeply nested destinations.

Suggested hardware check
Test Alpha left-fist insertion without forcing your arm unnaturally far in; pull either Upsilon power connector, release and regrab; confirm doors/drawers and thin readables still grab normally; enable DOUBLE-TAP SPRINT and check start/neutral stop/pause-resume. Save the resulting log.


# 1.02-S26DA

SOMA VR 1.02-S26DA - pickup-priority candidate and WAU measurements

Cumulative over S26CZ. The responsive door/drawer attachment correction remains.

Pickup priority
The S26CZ log contains door interactions while trying connectors and ambiguous static contacts while trying thin readables. Previously static pickup handling waited until after physics, while an earlier door attachment could retire the hand before that contact check. A fresh grip now first considers recent exact static contacts whose native interaction icon is carry-one, carry-two, pickup or read, validates native availability and current hand-mesh proximity (12 mm), and reserves that pickup transaction ahead of mechanisms. Non-interactable and door/drawer contacts do not create ambiguity in this item-only selection. Truly ambiguous item contacts fail closed rather than selecting a drawer. Existing positive-mass loose contact retains first priority. No new search, force law, drawer momentum or joint behavior changes.

WAU status
NOT CLAIMED FIXED. Activation geometry is unchanged from S26CZ. The latest log only samples total distance, which cannot distinguish insufficient depth from lateral error or an incorrect mouth target. The build adds bounded near-mouth measurements of raw/physical axial and radial offsets, target position and axis. Please test Alpha first after a fresh launch, attempt left closed-fist insertion several times, then exit to preserve the log before other maps consume the main log budget. Do not force your arm unnaturally far in. Ordinary flower behavior is not inferred from Alpha alone.

Validation
77 extracted static-item priority checks and integration guard checks passed. Existing 19 mechanism transaction, 84 insertion-boundary, 614 collision-permission and 45 fist-point checks passed. Native build and 49,106 hand-scale checks passed. These are isolated/mocked tests, not hardware verification of connector selection or WAU activation. No map-script edits in this revision.

Installation
Close SOMA, extract the full installer ZIP and run SOMA-VR-1.02-S26DA-Setup.exe, then INSTALL / UPDATE / REPAIR. Customized settings are preserved. Clean root VR INI remains included. Development did not overwrite installed game files or saves. Installer still has a legacy long-path limitation for deeply nested target directories.
