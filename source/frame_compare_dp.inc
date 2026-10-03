/* Read-only comparison of Steam Frame motion ranges. It runs only with the
   existing finger diagnostic sample, at most 12 times per hand, and never
   publishes the alternate pose to physics or rendering. */
static void s26dp_compare_motion_range(Handle tracker,Handle space,i64 time,i32 hand){
    if(!tracker||!p_s26qLocateHand||hand<0||hand>1||!g_s26diFrameHand[hand]||!g_s26dnMotionRangeEnabled)return;
    for(i32 mode=0;mode<2;++mode){
        S26QJoint joints[26];zero_bytes(joints,sizeof(joints));
        S26QJoints out;zero_bytes(&out,sizeof(out));out.type=1000051003;out.count=26;out.joints=joints;
        S26QHandLocate li;zero_bytes(&li,sizeof(li));li.type=1000051002;li.baseSpace=space;li.time=time;
        S26DNMotionRange range;
        s26dn_motion_range(&li,&range,mode==1);if(mode==1)range.range=2;
        i32 result=p_s26qLocateHand(tracker,&li,&out);
        float values[5]={-1,-1,-1,-1,-1};
        if(result==0&&out.active&&out.count==26)for(i32 f=0;f<5;++f){float v[4];if(s26di_frame_curl(joints,hand,f,v))values[f]=v[1];}
        ext_Log(">>> S26DP RANGE COMPARE h%d time %lld mode %s result %d active %u curl %.4f/%.4f/%.4f/%.4f/%.4f",hand,(long long)time,mode?"controller":"default",result,out.active,values[0],values[1],values[2],values[3],values[4]);
    }
}
