# Automatic Windows updates

The launcher checks https://api.github.com/repos/Bateau01/SOMA-VR/releases/latest before starting SOMA. Only a published stable release with a supported SOMA-VR-update.json is eligible. The manifest build number must be greater than the installed update-version file; public version tags alone do not cause a downgrade.

The player sees Yes/No before the installer download. No continues the installed game. Yes downloads the matching Setup.exe from this repository, verifies its byte count and SHA256, and runs its update mode for the current game folder. The existing transactional installer preserves preferences and the user's configured profile folder. A successful update re-runs the updated launcher with the original arguments and skips a second update check. An offline check or unsupported release does not prevent play. Failed installations stop the launch; installer logs are in %LOCALAPPDATA%/SOMA-VR-Installer/Logs. An incomplete transaction requires the installer's recovery action.

Use Launch-SOMA-VR.cmd -SkipUpdateCheck to bypass the check once. CheckOnly and StopOnly never check for updates. A running SOMA instance prevents updates. No account, token, or user data upload is needed.

## Publishing future releases

1. Set the new version and increasing numeric build in the package metadata, runtime/SOMA-VR-Update-Version.json, and installer build script as part of normal release preparation. The build script rejects mismatches.
2. Build the installer. installer/source/Build.ps1 generates SOMA-VR-update.json with the actual Setup.exe name, size and SHA256.
3. Upload BOTH the matching Setup.exe and SOMA-VR-update.json as separate assets of the same GitHub release. The Installer ZIP may also be uploaded for manual users, but an installer ZIP alone is not enough for auto-update.
4. Publish the release as stable and mark it Latest. Drafts/prereleases are ignored. Do not edit the installer after generating its manifest; rebuild both together.

Older installed launchers need this update installed manually once. No changes were published to GitHub by this task. GitHub release HTTPS and the repository's publishing permissions establish trust; the SHA256 checks corruption/mismatches, and is not a separate publisher signature.

Validation: updater policy/decline/offline/hash tests and isolated installer update, settings preservation and injected rollback checks. Live GitHub API discovery confirmed v1.07.1 currently contains only the installer ZIP, so it is skipped. A public end-to-end update becomes testable once a future stable release includes the two updater assets.
