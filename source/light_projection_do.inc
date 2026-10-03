/* Deferred light reconstruction must use the projection used for this eye.
   Native 140284720 instead derives these four values from scalar FOV/aspect,
   which can retain the previous eye's values. Matrices here are the native
   transposed cLightArguments layout. Only a full-eye, centered pixel viewport
   is admitted; unusual projections/viewports keep the native result. */
static i32 s26do_light_coefficients(const float* p,float far,i32 w,i32 h,const float* old,float* out){
    if(w<1||h<1||w>32768||h>32768||!(far>0.01f&&far<1000000.0f))return 0;
    for(i32 i=0;i<16;++i)if(!(p[i]>-1000000.0f&&p[i]<1000000.0f))return 0;
    if(!(p[0]>0.01f&&p[0]<100.0f&&p[5]>0.01f&&p[5]<100.0f))return 0;
    if(p[1]!=0||p[2]!=0||p[3]!=0||p[4]!=0||p[6]!=0||p[7]!=0||p[12]!=0||p[13]!=0||p[11]!=-1.0f||p[15]!=0)return 0;
    if(!(p[8]>-2.0f&&p[8]<2.0f&&p[9]>-2.0f&&p[9]<2.0f))return 0;
    for(i32 i=0;i<4;++i)if(!(old[i]>-10000000.0f&&old[i]<10000000.0f))return 0;
    if(!(old[0]>0.0f&&old[1]>0.0f))return 0;
    float cx=-old[2]/old[0],cy=-old[3]/old[1];
    if(!(cx>(float)w*0.5f-0.1f&&cx<(float)w*0.5f+0.1f&&cy>(float)h*0.5f-0.1f&&cy<(float)h*0.5f+0.1f))return 0;
    out[0]=2.0f*far/(p[0]*(float)w);out[1]=2.0f*far/(p[5]*(float)h);
    out[2]=far*(p[8]-1.0f)/p[0];out[3]=far*(p[9]-1.0f)/p[5];return 1;
}

typedef void (__attribute__((ms_abi)) *S26DOLightSetup)(void*);
static S26DOLightSetup o_s26doLightSetup;
static void* g_s26doLightRenderer;
static void* g_s26doLightFrustum;
static u32 g_s26doLightCalls,g_s26doLightApplied,g_s26doLightRejected;
static void __attribute__((ms_abi)) s26do_light_setup(void* renderer){
    if(o_s26doLightSetup)o_s26doLightSetup(renderer);
    if(!renderer||renderer!=g_s26doLightRenderer||!g_s26doLightFrustum)return;
    u8* r=(u8*)renderer;
    if(!h20_mem_readable(r+0x20u,8u)||*(void**)(r+0x20u)!=g_s26doLightFrustum||
       !h20_mem_readable(r+0x40u,8u)||!h20_mem_readable(r+0xaa4u,64u)||
       !h20_mem_readable(r+0xbe4u,4u)||!h20_mem_writable(r+0xbf4u,16u)||!h20_mem_writable(r+0x95cu,16u))return;
    ++g_s26doLightCalls;
    float values[4];const float* old=(const float*)(r+0xbf4u);
    if(!s26do_light_coefficients((const float*)(r+0xaa4u),*(float*)(r+0xbe4u),*(i32*)(r+0x40u),*(i32*)(r+0x44u),old,values)){++g_s26doLightRejected;return;}
    ++g_s26doLightApplied;
    *(float*)(r+0x964u)=values[0];*(float*)(r+0x968u)=values[1];
    *(float*)(r+0x95cu)=values[2];*(float*)(r+0x960u)=values[3];
    for(i32 i=0;i<4;++i)*(float*)(r+0xbf4u+i*4u)=values[i];
}
static void s26do_install_light_setup(void){
    static u8 tried;if(tried)return;tried=1;
    u8* base=(u8*)ext_GetModuleHandleA(0);u8* target=base?base+0x284720u:0;
    const u8 sig[30]={0x48,0x8b,0xc4,0x48,0x89,0x58,0x08,0x48,0x89,0x70,0x10,0x48,0x89,0x78,0x18,0x4c,0x89,0x60,0x20,0x55,0x48,0x8d,0x68,0xa1,0x48,0x81,0xec,0x00,0x01,0x00};
    if(!target||!h20_mem_readable(target,sizeof(sig)))return;
    for(u32 i=0;i<sizeof(sig);++i)if(target[i]!=sig[i]){ext_Log(">>> S26DO LIGHT projection correction unavailable: native signature differs");return;}
    i32 cr=ext_MH_CreateHook(target,(void*)s26do_light_setup,(void**)&o_s26doLightSetup);
    i32 er=cr==0?ext_MH_EnableHook(target):-999;
    ext_Log(">>> S26DO LIGHT projection correction hook create %d enable %d; scoped to main VR eye",cr,er);
}
