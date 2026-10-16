# Accessibility controls

Under VR SETTINGS > GAMEPLAY, REMOTE GRAB and TERMINAL LASER POINTER are on the first page. INTERACTION LASER POINTER is on the second page. All default to OFF and can be enabled independently.

REMOTE GRAB: point toward an eligible loose prop, dropped owned item, or readable. The selected target receives a cyan rim. Hold your grab button to pull it toward your hand; keep holding to catch it. Release to cancel. Range defaults to 2 m and is adjustable from 1 to 3 m. Free multi-body assemblies up to 25 kg total are supported; anchored mechanisms and scripted socket extraction are not remotely pulled. Dropped key-item eligibility remains session-local.

TERMINAL LASER POINTER: point at a fixed terminal or laptop and press trigger to enter/use it. Physical fingertip touch takes priority while touching its screen. Phones and handheld tablets retain their direct-touch controls.

INTERACTION LASER POINTER: point at a permitted talk, datamine or examine interaction and press trigger. This uses the game's interaction permission and callback. It does not remotely operate sockets, doors, heal gestures or held devices.

The laser beams are solid with filled cursors. REMOTE GRAB uses target highlighting rather than a beam. BACK steps to the previous settings page and then returns to the parent menu.

The launcher updates only SOMA's cached edge-glow fragment, preserving stock untagged highlighting. A shader-cache warning means that update could not be applied; include the warning when reporting an invisible outline.
