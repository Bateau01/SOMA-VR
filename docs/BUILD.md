# Building the current native DLL

The verified build requires Windows, Python 3 (tested with 3.12), and Zig 0.13.0. Use the Zig executable directly; the build does not install anything into SOMA.

From the repository root:

```powershell
python -X utf8 scripts/build.py --zig "C:\Tools\zig\zig.exe" --test
```

Output: `build/hpl3vr.dll`. The checked release hash is:

```text
80a31c06d48a5b979a04f4e9b3c6242a48f3145d49e2fd319c97f42f703eb761
```

The GitHub package was rebuilt using this portable script and matched that hash. The extracted native-rendering regression test reproduces the pre-fix failure and passes after the fix. It mocks engine calls and a small rig; it is not a test of all live controller interactions.

## How this code is built

The current implementation compiles `source/s26n.c` and its included `.inc` files, then appends/links the payload into the exact `third_party/hpl3vr_S5-P2_base.dll` using `scripts/apply_payload.py`. The patcher verifies the base hash and expected original instructions.

The frozen base DLL is an explicit build input. The `legacy` C++ files are historical source snapshots recovered from the supplied archives. They are not a proven byte-identical rebuild of this base.

## Audio adapter

The active adapter source is `source/audio_s.c`. Its compiled DLL and the Steam Audio runtime are in `runtime/vr_audio_s`. Players do not need audio development headers.

To rebuild the adapter, supply the FMOD Ex 4.44.06 C headers (`fmod.h`, `fmod_dsp.h` and their referenced headers) in `reference/`. They are not bundled as an FMOD SDK. Steam Audio 4.8.1 headers are included with their corresponding notices. Then:

```powershell
C:\Tools\zig\zig.exe cc -target x86_64-windows-gnu -O2 -Wall -Wextra -Werror -shared source/audio_s.c -o build/hpl3vr_audio_s.dll
```

The adapter dynamically uses the FMOD runtime already supplied with SOMA; no game FMOD library is shipped in the mod.

## Hand asset tools

Current ready-to-use meshes and collision/skin data are included under `runtime`. The authoring/conversion scripts and `export_wrist.c` are retained in `source` for reference. Some authoring scripts still use the historical staging layout and have `/PATH/TO/SOMA` placeholders. They are not part of the portable core build; review their input/output paths before adapting them. Rebuilding the core DLL does not regenerate or overwrite hand assets.

## Scope

Production source and scripts are the current snapshot. The repository does not manufacture old Git commits or bundle every obsolete diagnostic build. It omits private test-machine logs and save files. The source filenames retain their development names to avoid breaking includes or patch symbols.
