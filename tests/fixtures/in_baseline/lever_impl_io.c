static i32 h5755gb_drive_authored_lever(i32 hand,const float* handVel,float dt){
    if(hand<0||hand>1||!handVel||dt<=0.0005f||!p_h34PlayerAnalog||g_h5755gbLeverNativeFailClosed[hand])return 0;
    if(!h5755fn_exact_lever_names(g_h5729LastModuleName,g_h5729LastClassName))return 0;
    if(g_h5755gbLeverNativeWarmup[hand]){g_h5755gbLeverNativeWarmup[hand]--;return 1;}
    void* pi=h34_player_input_interface();if(!pi||!g_h37aAnalogGuardReady){g_h5755gbLeverNativeFailClosed[hand]=1;ext_Log(">>> S6-HANDS5755GF LEVER NATIVE ROTATEBASE FAIL-CLOSED %s: native cLuxPlayer/analog guard unavailable; generic hinge impulse remains structurally unreachable",hand==0?"L":"R");return 0;}

    /* GE: use the exact authored hinge frame to reduce a 3-D controller step to
       its single physically valid tangential DOF. Awkward push/pull along the
       hinge pin, radial motion toward/away from the pivot, and wrist twist no
       longer become RotateBase input. */
    const void* body=(g_h482ArticulatedValid[hand]&&g_h482DriveBody[hand])?g_h482DriveBody[hand]:g_h14GripBody[hand];
    const void* joint=(g_h482ArticulatedValid[hand]&&g_h482DriveJoint[hand])?g_h482DriveJoint[hand]:g_h15GripJoint[hand];
    const float* anchor=(g_h482ArticulatedValid[hand]&&g_h482DriveBody[hand])?g_h482DriveBodyAnchor[hand]:g_h15GripBodyAnchor[hand];
    if(!body||!joint||!anchor||!p_h14GetMatrix)return 1;
    float pin[3],pivot[3];void* jw=0;if(!h48_hinge_frame(joint,pin,pivot,&jw))return 1;
    float bm[16],current[3];p_h14GetMatrix(body,bm);h14_transform_point(bm,anchor,current);
    float radial[3]={current[0]-pivot[0],current[1]-pivot[1],current[2]-pivot[2]};float axial=h10_dot(radial,pin);radial[0]-=pin[0]*axial;radial[1]-=pin[1]*axial;radial[2]-=pin[2]*axial;float radius=h10_len3(radial[0],radial[1],radial[2]);if(radius<0.025f)return 1;float ir=1.0f/radius;radial[0]*=ir;radial[1]*=ir;radial[2]*=ir;
    float tangent[3];h10_cross(pin,radial,tangent);if(!h10_norm3(tangent))return 1;

    float d[3]={handVel[0]*dt,handVel[1]*dt,handVel[2]*dt};float rawDm=h10_len3(d[0],d[1],d[2]);
    float tangentStep=h10_dot(d,tangent);float radialStep=h10_dot(d,radial),axialStep=h10_dot(d,pin);
    /* GF: a hinge responds to angular travel, not meters.  Normalize the valid
       tangential controller step by the live authored hinge radius so equal
       physical arc angles have equal native input on short and long levers. */
    // S26GG: RotateBase integrates this speed input by dt again. Express it
    // in authored 60-Hz units before thresholds, preserving response per second.
    float angleStep=(tangentStep/radius)*(float)g_s26gdRateMultiplier;float aas=h9_abs(angleStep);
    if(aas<H5755GF_LEVER_ANGLE_DEADZONE_RAD){if(rawDm>0.00040f)g_h5755geLeverRadialAxialRejects[hand]++;return 1;}
    if(aas>H5755GF_LEVER_ANGLE_STEP_CAP_RAD)angleStep=(angleStep<0.0f)?-H5755GF_LEVER_ANGLE_STEP_CAP_RAD:H5755GF_LEVER_ANGLE_STEP_CAP_RAD;
    if(!g_h576bdLeverScriptOK){g_h5755gbLeverNativeFailClosed[hand]=1;ext_Log(">>> S6-HANDS5756BD LEVER SIGNED PACKET FAIL-CLOSED %s: matched RotateBase script marker missing; no camera-space fallback and no direct body impulse emitted",hand==0?"L":"R");return 0;}
    /* H57.56BD: angleStep already has the physically correct sign around the
       authored Hinge pin. Do not project it back into camera-space X/Y and ask
       stock Lever::GetSpeedAdd() to reconstruct the sign. That approximation
       made some orientations effectively one-way. Send the signed scalar in X
       with z=3; the matched RotateBase script injects it directly as fSpeedAdd. */
    float signedSpeedAdd=angleStep*H5755GF_LEVER_ANGLE_LOOK_GAIN;
    if(signedSpeedAdd>H5755GF_LEVER_AXIS_CAP)signedSpeedAdd=H5755GF_LEVER_AXIS_CAP;if(signedSpeedAdd<-H5755GF_LEVER_AXIS_CAP)signedSpeedAdd=-H5755GF_LEVER_AXIS_CAP;
    if(h9_abs(signedSpeedAdd)<0.0025f)return 1;
    float a[4]={signedSpeedAdd,0.0f,H576BD_LEVER_ANALOG_TAG,0.0f};
    g_h37aSyntheticAnalogHand=hand;g_h37aSyntheticFellThrough=0;g_h37aSyntheticAnalogDepth++;p_h34PlayerAnalog(pi,H34_ANALOG_LOOK,a);
    if(g_h37aSyntheticAnalogDepth)g_h37aSyntheticAnalogDepth--;g_h37aSyntheticAnalogHand=-1;g_h34AnalogCalls++;g_h30NativeMotionEvents++;g_h5755gbLeverNativePackets[hand]++;g_h5755geLeverTangentPackets[hand]++;
    if(g_h37aSyntheticFellThrough){g_h5755gbLeverNativeFallthrough[hand]++;g_h5755gbLeverNativeFailClosed[hand]=1;ext_Log(">>> S6-HANDS5756BD LEVER SIGNED PACKET FAIL-CLOSED %s: exact Lever did not consume z=3 signed packet; camera fallback blocked and no direct body impulse emitted",hand==0?"L":"R");return 0;}
    if(g_h5755geLeverTangentLogs[hand]<16u){g_h5755geLeverTangentLogs[hand]++;ext_Log(">>> S6-HANDS5756BD LEVER SIGNED ANGULAR PACKET %s #%u: rawStep %.4f m -> tangent %+.4f m (radial %+.4f axial %+.4f) radius %.3f m -> signed angle %+.4f rad -> RotateBase speedAdd %+.4f tag %.1f | positive/negative hinge motion preserved directly",hand==0?"L":"R",g_h5755geLeverTangentPackets[hand],(double)rawDm,(double)tangentStep,(double)radialStep,(double)axialStep,(double)radius,(double)angleStep,(double)signedSpeedAdd,(double)H576BD_LEVER_ANALOG_TAG);}
    return 1;
}