/* Roomscale is a change of tracking/body reference, not an authored teleport.
   Character SetPosition(false) clears camera history. Keep the native history,
   translate its world positions, and translate the existing camera by exactly
   the collision-accepted delta. Native physics/ownership/velocities are untouched.
   Called synchronously from Player.Update, only inside its pending QUERY. */
typedef void (__attribute__((ms_abi)) *S26IESetPosition)(void*,const float*,u8);
typedef void (__attribute__((ms_abi)) *S26IESetCamera)(void*,const float*);
static i32 s26ie_room_apply(const float d[3]){
    void* player=h5755ax_current_player();
    if(!player||!h20_mem_readable((u8*)player+0x170,8))return 0;
    u8* c=*(u8**)((u8*)player+0x170);
    if(!c||!h20_mem_readable(c,0x7a0))return 0;
    void* camera=*(void**)(c+0x1b0);
    if(!camera||camera!=p2_camera_obj()||!h20_mem_readable(camera,0x710))return 0;
    u8* base=(u8*)ext_GetModuleHandleA(0);
    u8* set=base+0x2413c0;u8* setCamera=base+0x277430;
    static const u8 sig[]={0x48,0x89,0x5c,0x24,8,0x57,0x48,0x83,0xec,0x20,0x8b,2,0x48,0x8b,0xf9,0x41};
    static const u8 csig[]={0x8b,2,0x4c,0x8d,0x41,0x10,0x48,0x81,0xc1,0x38,2,0,0};
    if(!h20_mem_executable(set)||!h20_mem_executable(setCamera)||!h20_mem_readable(set,sizeof(sig))||!h20_mem_readable(setCamera,sizeof(csig)))return 0;
    for(u32 k=0;k<sizeof(sig);k++)if(set[k]!=sig[k])return 0;
    for(u32 k=0;k<sizeof(csig);k++)if(setCamera[k]!=csig[k])return 0;
    void** vt=*(void***)c;if(!h20_mem_readable(vt,0x60)||vt[11]!=set)return 0;
    // Validate both native world-position history lists completely BEFORE writing.
    // No allocation, deletion or retained pointers; native owns their lifetimes.
    float* points[256];u32 count=0;
    const u32 lists[2]={0x1d0,0x288};
    for(i32 list=0;list<2;list++){
        u32 o=lists[list];u8* sentinel=*(u8**)(c+o);u64 size=*(u64*)(c+o+8);
        if(size>128||!sentinel||!h20_mem_readable(sentinel,16))return 0;
        u8* node=*(u8**)sentinel;u8* prev=sentinel;
        for(u64 n=0;n<size;n++){
            if(node==sentinel||!h20_mem_readable(node,28)||*(u8**)(node+8)!=prev)return 0;
            float* v=(float*)(node+16);for(i32 k=0;k<3;k++)if(!h9_good(v[k],1000000.0f))return 0;
            points[count++]=v;prev=node;node=*(u8**)node;
        }
        if(node!=sentinel||*(u8**)(sentinel+8)!=prev)return 0;
    }
    float position[3],cam[3],previous[3];
    for(i32 k=0;k<3;k++){
        float v=((float*)(c+0x6c))[k],cv=((float*)((u8*)camera+0x10))[k];
        if(!h9_good(v,1000000.0f)||!h9_good(cv,1000000.0f))return 0;
        float pv=((float*)(c+0x78))[k];
        if(!h9_good(pv,1000000.0f))return 0;
        previous[k]=pv+d[k];
        position[k]=v+d[k];cam[k]=cv+d[k];
    }
    for(u32 n=0;n<count;n++)for(i32 k=0;k<3;k++)points[n][k]+=d[k];
    // Verified synchronous SetPosition path updates body/model with camera detached.
    // No yield or physics step occurs in this scope; restore before returning.
    *(void**)(c+0x1b0)=0;
    ((S26IESetPosition)(void*)set)(c,position,1);
    // SetPosition is also a teleport reset of previous position. Translate
    // that sample equally so native walking velocity survives this rebase.
    for(i32 k=0;k<3;k++)((float*)(c+0x78))[k]=previous[k];
    *(void**)(c+0x1b0)=camera;
    ((S26IESetCamera)(void*)setCamera)(camera,cam);
    return 1;
}
