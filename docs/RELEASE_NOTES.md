# SOMA VR 1.0.8-S26HO

- The Windows launcher checks the official Bateau01/SOMA-VR latest stable GitHub release before starting the game. A newer supported release prompts Yes/No before downloading or installing.
- Yes downloads and verifies the installer size/SHA256, updates the same game folder using the existing backup/rollback installer, preserves the selected user-config folder, and restarts the updated launcher with the original launch arguments.
- No, offline/API failures, no supported update, or a running SOMA process skip updating. Check-only and stop-only do not contact GitHub. -SkipUpdateCheck bypasses the check for that launch.
- Failed/incomplete installation prevents automatic game launch until resolved; a settings-preserving rollback is attempted by the installer.
- Future releases must include the generated SOMA-VR-update.json and the matching Setup.exe. Installer ZIPs alone are not enough for automatic updating. Drafts and prereleases are excluded.

Gameplay DLLs are byte-identical to S26HM. The paused S26HN readable diagnostic is not included. The reported remote-readable drop remains unresolved.
