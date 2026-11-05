# Reporting a SOMA VR problem

After leaving SOMA, run Collect-SOMA-VR-Logs.cmd in the game folder. Send the resulting ZIP from SOMA-VR-Support with the steps that caused the problem. If that folder cannot be written, the ZIP is saved in Documents/SOMA-VR-Support. Logs can contain your Windows account paths; review the ZIP before sharing it.

Launch-SOMA-VR.cmd also collects the native game log after the process exits. In the game folder:
- hpl3vr.log: latest VR messages; .1, .2 and .3 retain older segments.
- SOMA-native.log: copy of the native profile's hpl.log; the original remains in Documents.
- SOMA-native-status.json: whether the native file appears current, stale, missing or unresolved.
- SOMA-VR-session.json: build, executable and session identity.
- SOMA-VR-Logs: up to three earlier sessions.

Use the VR launcher for automatic collection. A direct game launch does not start the exit collector, but the manual shortcut still works. Run the shortcut after exiting for a stable report and to avoid compression work during gameplay. Forced termination can lose the final queued VR messages; keep any separate crash logs as well.
