# 1.0.9-S26IT

Removed temporary stutter recording controls, capture buffer and file writer. Preserves existing recordings and settings. No gameplay changes or claim of resolved stutters.

# 1.0.9-S26IS - candidate for headset testing

- Restores the pending phone hologram after an answered phone recovers from an unreachable drop. Shared apartment/subway/laboratory helper; native recovery, grabbing, tapping and dialogue are unchanged.
- Shows the VR welcome each launch, with session-only dismissal.
- Adds Storage & Gestures as page three, using a cyan Simon diagram and native text within the unchanged welcome box. Corrects welcome-panel layering over native menu artwork.
- No MSAA selector: native probes confirm the available window setting does not multisample the scene. Full scene MSAA remains unimplemented.
- [Validation, evidence and remaining headset checks](FOLLOWUP_IS.md).

# 1.0.9-S26HV — candidate for headset testing

- Corrects the first Upsilon Omni-Tool hologram permission target after acquisition/shoulder retrieval.
- Keeps the real slot transform while querying AreaInsertOmniTool_TechRoom; suppresses the guide when that authored area is inactive or disabled.
- No item usage, physical insertion, shoulder poses, physics or rendering changes; tracer fluid and stun baton remain excluded.
- Native sequence, campaign guide audit, regression and installer evidence: [guide-audit-hv.md](guide-audit-hv.md). Hardware validation remains pending.

# SOMA VR 1.0.9-S26HU â€” testing candidate

- Allows valid physical buttons while an ordinary laptop/terminal remains focused. Native permissions, held-object restrictions and scripted terminal ownership remain authoritative. This does not cancel the laptop's GUI or change tapping/laser input.
- Startup introduction now uses NEXT PAGE, revised category descriptions and first-time advice. Removes the standalone hand-reset sentence. Refreshes controller-profile information for physical button labels; disconnected/unknown controllers are identified honestly. Existing bindings remain unchanged.
- Moves 120HZ PHYSICS to VIDEO page one and TEXTURE BUDGET BOOST to page two.
- Gates Phi's launch moving-button and auxiliary callback by the authored launch-ready window. Early and duplicate launch actions are rejected.
- Adds Omicron/Phi armrest contact regions and a matching hand guide, gated by the original chair interaction. Existing center interaction remains. Guides OFF retains the added contact regions; flat-screen mode does not enable them.
- Confirms current Omni-Tool guide selection already follows the physical tool's upgrade-model file. All four canonical guide assets load.
- Retains S26HT item guides, including tracer-fluid and stun-baton exclusions.

See v109-followup-hu.md for tests and limitations. Final headset appearance, physical touches and complete story routes remain pending.

---

# SOMA VR 1.0.9-S26HT â€” testing candidate

- Expands interaction guides to all 16 usable campaign key-item identities, including upgraded/repaired states; tracer fluid and the stun baton remain excluded.
- Uses native visible mesh transforms and authored destination positions. Covers Upsilon and Lambda chips, Delta replacement chips, Theta chips, Omicron repair/charging/suit steps, Tau ARK placement and Phi power sockets/ARK frame.
- Preserves native permissions and suit-stage order. Multiple Delta target aliases produce one replacement-chip guide.
- No changes to item usage, campaign progression scripts or authored shoulder poses.
- Retains the previous S26HS fixes and their outstanding headset acceptance checks.

Native placement/permission/lifecycle and installer evidence is recorded in [the audit](key-item-guides-ht.md). Geometry fixtures substitute permission and do not constitute a complete playthrough or headset visual check.

---

# SOMA VR 1.0.8-S26HQ

- The gameplay desktop mirror combines the existing eye images with a left-eye-dominant overlap blend, aligned by their projection bounds. Fills the visible monitor area without stretching; crops vertically as needed. Nearby objects may reveal parallax at the blend boundary. This approximates SteamVR-style spectator framing; it is not Valve's compositor implementation or a depth-correct third camera.
- The combined path replaces the full-size intermediate copy with one desktop draw. Headset eye textures remain read-only; no extra scene render, physics change, or change to menu/credits/loading transitions.
- The shader is prepared during the menu. Unavailable shaders/invalid geometry fall back to the existing full-left-eye mirror. DESKTOP MIRROR OFF bypasses composition.
- Retains S26HP menu cursor correction and S26HO automatic updates. Paused remote-readable diagnostics remain excluded.

Tests: real OpenGL driver at 1920x1080 (0x/4x MSAA), 2560x1440, and 3440x1440 (4x MSAA), checking output pixels, GL state restoration, source-eye immutability and off/menu/transition/resume guards. Isolated mirror-only GPU timings roughly 0.011-0.023 ms combined versus 0.011-0.023 ms cropped left-eye. These synthetic measurements are not whole-game benchmarks or guarantees on other GPUs.

Final live check: full 2560x1440 monitor framing, bottom strip removed, and pause/resume confirmed by the tester. The menu cursor correction keeps the native cursor visible while the applicable VR menu is active. No controller-binding changes.

Updater correction: explicitly parses GitHub release assets returned as JSON text, including a UTF-8 BOM. Internal build 2026101616. Existing affected updaters require a one-time script replacement or manual installation. Upload the Setup.exe separately alongside its matching update manifest.

Internal build 2026101617: fixes Windows PowerShell 5.1 decoding of GitHub octet-stream manifests by decoding raw UTF-8 bytes before parsing. Tested with the actual launcher shell.
