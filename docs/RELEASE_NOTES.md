SOMA VR 1.04-S26EE

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
