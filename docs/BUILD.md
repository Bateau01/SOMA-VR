# Building the current native DLL

The verified build requires Windows, Python 3 (tested with 3.12), and Zig 0.13.0. Use the Zig executable directly; the build does not install anything into SOMA.

From the repository root:

```powershell
python -X utf8 scripts/build.py --zig "C:\Tools\zig\zig.exe" --test
```

Output: `build/hpl3vr.dll` (1.0.8-S26HO). SHA256:

`ed8b837e47f2fb46ac604e3c3ef536bf18ec0580b49006eed916abaa3388ad31`

Build the separately guarded Epic/GOG DLL with:

```powershell
python -X utf8 scripts/build_store.py --zig "C:\Tools\zig\zig.exe"
```

Output: `build/store/hpl3vr-store.dll`. SHA256:

`2d7c94d8a1107f33086423c2e02ccb9560eccdfd1b802ccae3d20584d58d0eee`

The store build generates a mapped source copy using `reference/store-profile.json`, verifies signatures, and patches the frozen-base operands for that exact engine layout. Do not mix the DLLs manually; the normal launcher selects them by executable identity.

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

Additional regression checks:

```powershell
python -X utf8 tests/test_transition_height.py "C:\Tools\zig\zig.exe"
powershell -NoProfile -ExecutionPolicy Bypass -File tests/test_launcher_cleanup.ps1
```

Menu-state regression checks (mocked engine state):

```powershell
python -X utf8 tests/test_menu_recovery.py "C:\Tools\zig\zig.exe"
python -X utf8 tests/test_holster_native.py "C:\Tools\zig\zig.exe"
python -X utf8 tests/test_foveation_scope.py "C:\Tools\zig\zig.exe"
```

The real OpenGL foveation test requires a GPU exposing GL_NV_shading_rate_image. It verifies state restoration and shading invocation counts, not headset image quality or whole-game performance. See the release notes for remaining hardware checks.

Gesture regressions: `python tests/test_shoulder_gestures.py "C:\Tools\zig\zig.exe"`. They exercise production gesture code with mocked tracking state, without launching the game.

Rear-region regressions: `python tests/test_shoulder_rear.py C:\Tools\zig\zig.exe`. These use production functions with synthetic state.

Rear-region regressions: `python tests/test_shoulder_rear.py C:\Tools\zig\zig.exe`. These use production functions with synthetic state.

GB rebuilds both native DLLs and updates MenuHandler, PlayerToolHandler and Catherine scripts for guarded recall. The GA Push-prop fix remains included. Run tests/test_omni_recall.py and tests/test_extra_buttons.py with your Zig path.


S26GF binaries (SHA-256):

hpl3vr.dll: ab38b44c6e916f322677e1ac4ae42b9936f849108f2f17a2de15c1e37df26c71
hpl3vr-store.dll: b2692235e3cee95d3e9cfe6376b5a51d67ffda5ff227241829e3f3aaa31dde22


S26GG binaries (SHA-256):

hpl3vr.dll: fde3327573fbdaca0e38d2099c671ac0a5255e289a86aa42d6c7e0076c55f9e5
hpl3vr-store.dll: e9baf8064d6dd5bafb5f20b8133cbc179c652d25a10ceb0a7bf604e9fb32e05c


S26GG binaries (SHA-256):

hpl3vr.dll: fde3327573fbdaca0e38d2099c671ac0a5255e289a86aa42d6c7e0076c55f9e5
hpl3vr-store.dll: e9baf8064d6dd5bafb5f20b8133cbc179c652d25a10ceb0a7bf604e9fb32e05c


S26GH binaries (SHA-256):

hpl3vr.dll: de1cff24e49111a2b932fa05b42a5c53d3f6aad0791c5dea9c9fc5cd79b4e0ce
hpl3vr-store.dll: e05a4aa49ea8cdbbf19e1ae8a2ef8e3358cb57a89d45268c1976914e27801c1d


1.07-S26GI binaries (SHA-256):

hpl3vr.dll: a872cd11cbfbf49ce0108e480eeebdfca852412fcce24216e33a54cd8a795728
hpl3vr-store.dll: 8c29311e76b25ead2f7dbe25a0442aa4c7224e4086d010b7c2fe015df7b34309


1.07-S26GJ binaries (SHA-256):

hpl3vr.dll: 8aa26fd833f7e2f2f30bec10b6a102832d75add62e362c679a2a9b5349bfcbe8
hpl3vr-store.dll: b043a88a6a6b1d9c6bd3c4f0f95b7b6225f12f399e933b5a68e32a82c78a14bc
