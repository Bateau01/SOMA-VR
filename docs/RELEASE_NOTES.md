# SOMA VR 1.0.8-S26HQ

- The gameplay desktop mirror combines the existing eye images with a left-eye-dominant overlap blend, aligned by their projection bounds. Fills the visible monitor area without stretching; crops vertically as needed. Nearby objects may reveal parallax at the blend boundary. This approximates SteamVR-style spectator framing; it is not Valve's compositor implementation or a depth-correct third camera.
- The combined path replaces the full-size intermediate copy with one desktop draw. Headset eye textures remain read-only; no extra scene render, physics change, or change to menu/credits/loading transitions.
- The shader is prepared during the menu. Unavailable shaders/invalid geometry fall back to the existing full-left-eye mirror. DESKTOP MIRROR OFF bypasses composition.
- Retains S26HP menu cursor correction and S26HO automatic updates. Paused remote-readable diagnostics remain excluded.

Tests: real OpenGL driver at 1920x1080 (0x/4x MSAA), 2560x1440, and 3440x1440 (4x MSAA), checking output pixels, GL state restoration, source-eye immutability and off/menu/transition/resume guards. Isolated mirror-only GPU timings roughly 0.011-0.023 ms combined versus 0.011-0.023 ms cropped left-eye. These synthetic measurements are not whole-game benchmarks or guarantees on other GPUs.

Final live check: full 2560x1440 monitor framing, bottom strip removed, and pause/resume confirmed by the tester. The menu cursor correction keeps the native cursor visible while the applicable VR menu is active. No controller-binding changes.
