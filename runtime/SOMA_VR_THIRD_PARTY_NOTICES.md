# Third-party components and provenance

- **SOMA:** original game, scripts, entity/map data and hand art by Frictional Games. The overlay contains modified game-derived files needed for the mod. The game executable, full game, saves and game FMOD libraries are not included. This document does not grant a license to Frictional Games' material.
- **Steam Audio 4.8.1:** Valve Corporation. The bundled `phonon.dll` is the existing official Windows x64 binary. See `runtime/vr_audio_s/ATTRIBUTION.txt`, `LICENSE-SteamAudio.md` and `THIRDPARTY-SteamAudio.md`.
- **OpenXR SDK loader:** Khronos Group and contributors. The existing runtime loader is included. See `runtime/licenses/OpenXR-SDK-LICENSE.txt` and https://github.com/KhronosGroup/OpenXR-SDK.
- **MinHook:** Tsuda Kageyu and contributors, including the disassembler notices. Used by the native hook implementation. See `runtime/licenses/MinHook-LICENSE.txt` and https://github.com/TsudaKageyu/minhook.
- **FMOD Ex:** Firelight Technologies. The adapter uses the runtime from the user's SOMA installation. The proprietary runtime and development SDK are not included.

The mod's legacy base DLL and injector are supplied from the existing project. Historical C++ snapshots are not included in this archive. Their exact build provenance is described in `docs/PROVENANCE.json` and `docs/BUILD.md`.
