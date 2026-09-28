# SOMA VR S26BY — experimental cumulative release

This package includes the current OpenXR runtime, all cumulative VR script/entity/map overlays, current hand models, optional binaural audio components, source and a Windows launcher.

## Latest correction

The ordinary native hand-mesh update omitted the world-scale compensation that already existed in the held-hand refresh and custom drawing path. Empty hands therefore changed apparent size with world scale, and grabbing could make them visibly resize.

S26BY applies the existing compensation once to the fresh native mesh basis for free, held and healing states. Tracking translation, bone-local units, item dimensions and grip anchoring remain unchanged.

## Verification

- The pre-fix native callback fails the dedicated regression; the fixed callback passes 49,106 checks.
- Checks include both hands, all 31 scale settings, family-identity changes, free/grab/two-hand/healing/release transitions and avoidance of double scaling. Native engine calls and the rig are mocked for this test.
- The release DLL loaded a supplied Upsilon save in the isolated VR copy and exited normally.
- The portable GitHub build produces the exact shipped DLL hash.
- In-headset confirmation of the S26BY hand-size fix is pending.

Earlier integration includes physical terminals, story items, Omni-Tool slots/panels, mechanisms, save/reload handling, comfort options, native hand rendering and other features listed in FEATURES.md. These remain experimental; this release is not a guarantee of every story state or controller.

## Player download

Use `SOMA-VR-vx.xx.zip`, copy the contents of its `SOMA-VR` folder alongside `Soma.exe`, and follow the included README. Back up replaced files and saves first. Existing settings and calibration are preserved.
