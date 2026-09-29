# Experimental executable compatibility

The storefront name alone does not establish compatibility. This mod uses native function/data addresses from a specific 64-bit SOMA executable. Changing the launch command cannot adapt those addresses to a different build.

## For GOG/Epic testers

1. Back up your game files and install the full overlay into that installation's game folder. Do not copy the Steam game executable into another edition.
2. Run `Check-SOMA-VR-Compatibility.cmd`. This checks the executable and produces `SOMA-VR-compatibility-report.json`; it does not start/stop SOMA or inject the DLL.
3. Send that report with your storefront and game version. It contains a filename, hashes and PE layout, not game executable contents, saves or account information.

Results:

- `VerifiedExecutable`: exact executable hash already used for the mod. This is not a check of the installation's other assets or dependencies.
- `EquivalentEngineUnverified`: all compared engine sections and mapped layout match. From a command prompt in the game folder, `Launch-SOMA-VR.cmd -Experimental` opts into testing. Gameplay and storefront-specific dependencies still need validation.
- `Incompatible`: engine bytes/layout differ. The launcher will not inject, even with `-Experimental`. The actual executable needs native analysis and a compatibility port. A report helps identify the build but is not sufficient to derive new addresses by itself.

If Soma.exe is absent, the launcher checks Soma_NoSteam.exe. To select explicitly:

```bat
Check-SOMA-VR-Compatibility.cmd -Executable Soma_NoSteam.exe
Launch-SOMA-VR.cmd -Executable Soma_NoSteam.exe -Experimental
```

Do not rename an executable to bypass compatibility: its contents are checked. No storefront installation is considered supported merely because a process can be launched or a DLL loaded. The GOG and Epic builds have not been tested.

## What the comparison does

The tested full SHA256 is accepted. For experimental equivalents, the comparison requires the same architecture, PE characteristics, optional-header layout (except checksum and certificate-table location), section headers, and raw content of every non-resource section. Resource bytes are excluded but their section layout must match. This deliberately rejects builds with shifted native code/data rather than guessing addresses. Script/asset and dependency equivalence is not proved by this comparison.

## Settings file

`hpl3vr_vr_settings.ini` is shipped at the game root with clean defaults and in `defaults` for missing-file restoration. Keep your customized root copy when updating. Replacing it during extraction resets values contained there; user-profile menu preferences remain separate.
