# S26CD save-to-VR investigation

The reporter's S26CC log initializes OpenXR with 4036 x 3376 recommended eye images and recognizes both controllers. It then records AUTHORED LOAD BEGIN but no AUTHORED GAME HANDOFF or GAMEPLAY CAMERA AUTHORITY ON. AUTHORED RESUME later promotes gameplay rendering. This is a presentation/camera-authorization mismatch; the log alone does not establish a Pimax driver defect.

MenuHandler's no-recap branch previously called ContinueLoading(true), cleaned up, and returned without the VRLIFE G event used by the visible recap branch. S26CD retains the native post-load wait for this VR path and uses the engine's completion predicate before StartLoadedGame. Flatscreen keeps ContinueLoading(true). Resume cannot override an outstanding title/load presentation latch.

Ghidra reference: executable SHA256 7c424e6055dda5b3a9d6ffdebb8f4b50fa8a38769dee82d080b79113. Script registration at 0x1401951a0 binds ContinueLoading to 0x1401886d0, IsDoneLoadingSavedGame to 0x1401886f0 and StartLoadedGame to 0x140188720. The completion predicate requires phase 6 and bytes +0x2c8/+0x2c9. ContinueLoading(true) clears the two wait options at +0x270, whereas false releases the current wait using +0x2ca. StartLoadedGame similarly releases the completed phase-6 wait. Consequently polling completion after disabling waits is not a reliable substitute for preserving that wait.

Automated tests use mocked engine state and do not establish optical correctness on the reported headset. Native validation results are supplied separately. The prior S26CC authored-height behavior and fixed apparent hand size are retained.
