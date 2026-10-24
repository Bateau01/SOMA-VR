    if(g_h482ArticulatedValid[hand]&&g_h30NativeMouseDown&&g_h30NativeUseHand==hand){
        if(g_h5755ceSwingDoorPendingNative[hand]++<2u)ext_Log(">>> S6-HANDS5755CD GRAPH DOOR PENDING %s: native OnInteract handshake live; waiting for exact SwingDoor state | legacy graph-door impulse motor DELETED, fail closed",hand==0?"L":"R");
        return;
    }
    /* H57.55GC: GB correctly retired the Lever's historical H48 tangent impulse
       but accidentally returned from this live jointed-anchor owner without
       dispatching h5755gb_drive_authored_lever(). Hardware therefore logged
       ARMED but zero PACKET records. Bridge this exact live path into the
       authored Lever/RotateBase Look adapter, then still fail closed before any
       generic point impulse. */
    if(h5755fn_exact_lever_names(g_h5729LastModuleName,g_h5729LastClassName)){
        g_h5755gcLeverJointedBridgeCalls[hand]++;
        if(g_h5755gcLeverJointedBridgeLogs[hand]<4u){g_h5755gcLeverJointedBridgeLogs[hand]++;ext_Log(">>> S6-HANDS5755GF LEVER JOINTED BRIDGE %s #%u: exact Lever state -> authored RotateBase Look; generic tangent impulse is structurally unreachable",hand==0?"L":"R",g_h5755gcLeverJointedBridgeCalls[hand]);}
        if(g_h30NativeMouseDown&&g_h30NativeUseHand==hand)
            (void)h5755gb_drive_authored_lever(hand,handV,dt);
        g_h5755gbLeverLegacyImpulseSuppress[hand]++;
        return;
    }
