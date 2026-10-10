# SOMA VR compatibility — 1.05-S26ER

Use the same installer and Launch-SOMA-VR.cmd for Steam, Epic or GOG. The launcher prepares the selected user's settings, uses borderless windowed mode and selects the native DLL by exact executable identity.

| Executable | SHA256 | Native DLL |
|---|---|---|
| Steam Windows x64 | 7c424e6055dda5b3aa41d4b3a9d6ffdebb8f4b50fa8a38769dee82d080b79113 | hpl3vr.dll |
| Epic / GOG Windows x64 | 395cd54830c8e66e22166e71ac6fe95fd3bb5433b898737836744a6d178a0a6a | hpl3vr-store.dll |

The supplied Epic and GOG executables are identical. Selected dependent libraries, scripts and configuration also matched. Native script/interaction fixtures passed with this engine profile. Earlier VR startup reached the main menu and Upsilon; visual gameplay confirmation is pending. Other executable layouts are not supported by assuming their addresses match. Use Check-SOMA-VR-Compatibility.cmd for a report.

The executable is sufficient for initial address mapping, but the installation was used to check dependencies and scripts and run the game. Future compatibility validation needs the matching dependencies and content, not only an EXE.

DFR requires the NVIDIA OpenGL shading-rate extension plus usable eye gaze. Finger tracking accepts valid runtime joint data regardless of brand; automatic rest detection additionally needs known release signals. See SOMA_VR_FEATURES.md. Runtime motion smoothing is not controlled by this build. Linux/Proton is not validated or supported by this Windows installer.
