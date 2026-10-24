    if(h9_abs(orbit)>H576AZ_WHEEL_ANGLE_STEP_CAP_RAD)orbit=(orbit<0.0f)?-H576AZ_WHEEL_ANGLE_STEP_CAP_RAD:H576AZ_WHEEL_ANGLE_STEP_CAP_RAD;
    if(h9_abs(wrist)>H576AZ_WHEEL_ANGLE_STEP_CAP_RAD)wrist=(wrist<0.0f)?-H576AZ_WHEEL_ANGLE_STEP_CAP_RAD:H576AZ_WHEEL_ANGLE_STEP_CAP_RAD;
    float ao=h9_abs(orbit),aw=h9_abs(wrist),angle=0.0f;const char* mode="idle";
    if(ao<H576AZ_WHEEL_ANGLE_DEADZONE_RAD&&aw<H576BA_WHEEL_WRIST_DEADZONE_RAD){angle=0.0f;}
    else if(aw<H576BA_WHEEL_WRIST_DEADZONE_RAD){angle=orbit;mode="orbit";g_h576baWheelOrbitPackets++;}
    else if(ao<H576AZ_WHEEL_ANGLE_DEADZONE_RAD){angle=wrist;mode="wrist";g_h576baWheelWristPackets++;}
    else{
        float ww=0.0f;if(radius<=H576BA_WHEEL_WRIST_BLEND_INNER_M)ww=1.0f;else if(radius>=H576BA_WHEEL_WRIST_BLEND_OUTER_M)ww=0.0f;else ww=(H576BA_WHEEL_WRIST_BLEND_OUTER_M-radius)/(H576BA_WHEEL_WRIST_BLEND_OUTER_M-H576BA_WHEEL_WRIST_BLEND_INNER_M);
        /* Geometry decides the preferred gesture, not an entity name: tiny knobs
           favor wrist twist, broad valve rims favor orbital hand travel. If the
           preferred channel is nearly stationary, the other channel takes over. */
        if(ww>0.75f&&aw>=H576BA_WHEEL_WRIST_DEADZONE_RAD)angle=wrist;
        else if(ww<0.25f&&ao>=H576AZ_WHEEL_ANGLE_DEADZONE_RAD)angle=orbit;
        else angle=orbit*(1.0f-ww)+wrist*ww;
        mode="blend";g_h576baWheelBlendPackets++;
    }
    g_h576baWheelOrbit[hand]=orbit;
