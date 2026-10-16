/* Native step-over eligibility compares per-update displacement squared.
   Keep the native 0.6 m/s eligibility floor when the simulation is doubled.
   Only this verified instruction gets a private literal; the shared engine
   constant and all step geometry, fit tests and climb velocity stay unchanged. */
static float* g_s26ghStepThreshold;

static i32 s26gh_prepare_step_threshold(u8* b){
    static const u8 sig[]={0x0f,0x2f,0x15};
    u8* instruction=b+0x57c8ff;
    for(u32 i=0;i<sizeof(sig);++i)if(instruction[i]!=sig[i])return 0;
    i32 originalRelative=*(i32*)(instruction+3);
    if(instruction+7+originalRelative!=b+0x68ea40)return 0;
    if(*(float*)(b+0x68ea40)!=0.0001f)return 0;
    if(b[0x57c959]!=0x83||b[0x57c95a]!=0xe8||b[0x57c95b]!=4)return 0;
    typedef void* (__attribute__((ms_abi)) *Alloc)(void*,u64,u32,u32);
    typedef i32 (__attribute__((ms_abi)) *Protect)(void*,u64,u32,u32*);
    typedef i32 (__attribute__((ms_abi)) *Free)(void*,u64,u32);
    typedef i32 (__attribute__((ms_abi)) *Flush)(void*,const void*,u64);
    void* kernel=ext_GetModuleHandleA("kernel32.dll");if(!kernel)return 0;
    Alloc alloc=(Alloc)ext_GetProcAddress(kernel,"VirtualAlloc");
    Protect protect=(Protect)ext_GetProcAddress(kernel,"VirtualProtect");
    Free release=(Free)ext_GetProcAddress(kernel,"VirtualFree");
    Flush flush=(Flush)ext_GetProcAddress(kernel,"FlushInstructionCache");
    if(!alloc||!protect||!release||!flush)return 0;
    void* page=0;u64 origin=((u64)b+0x900000u+0xffffu)&~(u64)0xffffu;
    for(u64 offset=0;offset<0x20000000u;offset+=0x10000u){
        page=alloc((void*)(origin+offset),0x1000,0x3000,0x04);if(page)break;
    }
    if(!page)return 0;
    i64 relative=(i64)(u64)page-(i64)(u64)(instruction+7);
    if(relative<-2147483647LL||relative>2147483647LL){release(page,0,0x8000);return 0;}
    *(float*)page=0.0001f; /* Remains native unless the 120 Hz timer is created. */
    u32 oldProtect=0,ignored=0;
    if(!protect(instruction,7,0x40,&oldProtect)){release(page,0,0x8000);return 0;}
    *(i32*)(instruction+3)=(i32)relative;
    if(!flush((void*)(i64)-1,instruction,7)||!protect(instruction,7,oldProtect,&ignored)){
        *(i32*)(instruction+3)=originalRelative;
        flush((void*)(i64)-1,instruction,7);protect(instruction,7,oldProtect,&ignored);
        release(page,0,0x8000);return 0;
    }
    g_s26ghStepThreshold=(float*)page;

    ext_Log(">>> S26GH STEP ELIGIBILITY READY: isolated native comparison literal; no collision or step-height change");
    return 1;
}
/* The step routine only reads max-ground count to choose ground/air step
   height; its collision queries do not execute script callbacks. Adjust that
   local decision window, restore the authored field immediately, and retain
   custom counter settings. No change to the actual ground counter or forces. */
typedef void (__attribute__((ms_abi)) *S26GHStep)(void*,float*,char,float*,float);
static S26GHStep o_s26ghStep;
static void __attribute__((ms_abi)) s26gh_step(void* self,float* move,char collided,float* correction,float dt){
    i32* maximum=(i32*)((u8*)self+0xe0);i32 saved=*maximum;
    if(g_s26gdRateMultiplier!=2u||(saved!=12&&saved!=24)||*(i32*)((u8*)self+0xdc)<=0){
        o_s26ghStep(self,move,collided,correction,dt);return;
    }
    *maximum=saved-4; /* native max-4 comparison now represents eight 120-Hz updates */
    o_s26ghStep(self,move,collided,correction,dt);
    *maximum=saved;
}
static i32 s26gh_prepare_ground_window(u8* b){
    static const u8 sig[]={0x48,0x8b,0xc4,0x55,0x53,0x48,0x8d,0xa8,0x08,0xff,0xff,0xff,0x48,0x81,0xec,0xe8,1,0,0};
    for(u32 i=0;i<sizeof(sig);++i)if(b[0x57c8b0+i]!=sig[i])return 0;
    if(ext_MH_CreateHook(b+0x57c8b0,(void*)s26gh_step,(void**)&o_s26ghStep)||ext_MH_EnableHook(b+0x57c8b0))return 0;
    return 1;
}
/* Edition-specific addresses and signatures are selected at build time.
   Unknown executable layouts retain native timing. No live retiming. */
typedef void* (__attribute__((ms_abi)) *S26GDCreateTimer)(void*,i32);
static S26GDCreateTimer o_s26gdCreateTimer;
typedef void (__attribute__((ms_abi)) *S26GDDamping)(void*);
static S26GDDamping o_s26gdDamping;
static void __attribute__((ms_abi)) s26gd_damping(void* body){
    if(g_s26gdRateMultiplier!=2u){o_s26gdDamping(body);return;}
    /* Verified Newton 2.36 ApplyDamping: no user callbacks, only local vector
       arithmetic. The solver owns this body during the call. Preserve authored
       damping fields and save serialization, including anisotropic rotation. */
    float* d=(float*)((u8*)body+0x1c0);float saved[4];
    for(u32 i=0;i<4;++i){saved[i]=d[i];d[i]=s26gd_half_damping(d[i]);}
    o_s26gdDamping(body);
    for(u32 i=0;i<4;++i)d[i]=saved[i];
}
static i32 s26gd_prepare_damping(void){
    u8* b=(u8*)ext_GetModuleHandleA("Newton.dll");if(!b)return 0;
    u32 n=*(u32*)(b+0x3c);if(n<0x40||n>0x1000||*(u32*)(b+n)!=0x4550||
        *(u32*)(b+n+8)!=0x54bcf792u||*(u32*)(b+n+24+56)!=0xe9000u)return 0;
    static const u8 sig[]={0x48,0x89,0x5c,0x24,8,0x57,0x48,0x81,0xec,0x80,0,0,0,0xf3,0x0f,0x10,0x91,0xcc,1,0,0};
    u8* target=b+0x1f150;for(u32 i=0;i<sizeof(sig);++i)if(target[i]!=sig[i])return 0;
    if(ext_MH_CreateHook(target,(void*)s26gd_damping,(void**)&o_s26gdDamping)||ext_MH_EnableHook(target))return 0;
    ext_Log(">>> S26GD DAMPING READY: verified Newton ApplyDamping; linear/angular decay preserves native 60 Hz duration; authored fields restored after each call");return 1;
}
/* S26GF: preserve the native half-second enemy displacement history.
   Constructor and vector resize verified in Steam 2021-09-27. This transient
   history is not serialized; use the engine allocator and keep native ownership. */
typedef void* (__attribute__((ms_abi)) *S26GFMoverCtor)(void*,void*,void*,void*);
typedef void (__attribute__((ms_abi)) *S26GFResizeVectors)(void*,u64);
static S26GFMoverCtor o_s26gfMoverCtor;
static S26GFResizeVectors p_s26gfResizeVectors;
static void* __attribute__((ms_abi)) s26gf_mover_ctor(void* self,void* a,void* b,void* c){
    void* result=o_s26gfMoverCtor(self,a,b,c);
    if(result&&g_s26gdRateMultiplier==2u){
        u8* p=(u8*)result;u64* v=(u64*)(p+0x358);
        if(v[0]&&v[1]-v[0]==30u*12u&&*(u64*)(p+0x348)==0&&*(u64*)(p+0x350)==0)
        {
            p_s26gfResizeVectors(v,60u);
            static u32 reported;
            if(!reported++){ext_Log(">>> S26GF ENEMY HISTORY ACTIVE: %u native movement samples",(u32)((v[1]-v[0])/12u));}
        }
    }
    return result;
}
typedef void (__attribute__((ms_abi)) *S26GFPlayerUpdate)(void*,float);
static S26GFPlayerUpdate o_s26gfPlayerUpdate;
static S26GFResizeVectors p_s26gfResizeFloats;
static void __attribute__((ms_abi)) s26gf_player_update(void* self,float dt){
    if(g_s26gdRateMultiplier==2u){
        /* This interface pointer is player+0x110. Only resize empty, native
           startup histories; never rewrite a populated history or save state. */
        u8* p=(u8*)self;u64* speed=(u64*)(p+0x3a8);u64* dir=(u64*)(p+0x3e0);
        if(speed[0]&&dir[0]&&speed[1]-speed[0]==35u*4u&&dir[1]-dir[0]==35u*12u&&
           *(u64*)(p+0x398)==0&&*(u64*)(p+0x3a0)==0&&*(u64*)(p+0x3d0)==0&&*(u64*)(p+0x3d8)==0){
            p_s26gfResizeFloats(speed,70u);p_s26gfResizeVectors(dir,70u);
            ext_Log(">>> S26GF PLAYER HISTORY ACTIVE: %u speed / %u direction samples preserve native averaging duration",(u32)((speed[1]-speed[0])/4u),(u32)((dir[1]-dir[0])/12u));
        }
    }
    o_s26gfPlayerUpdate(self,dt);
}
static i32 s26gf_prepare_mover(u8* b){
    static const u8 ctor[]={0x48,0x8b,0xc4,0x48,0x89,0x48,8,0x55,0x56,0x57,0x41,0x54,0x41,0x55,0x41,0x56,0x41,0x57};
    static const u8 resize[]={0x48,0x89,0x5c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x30};
    for(u32 i=0;i<sizeof(ctor);++i)if(b[0x54540+i]!=ctor[i])return 0;
    for(u32 i=0;i<sizeof(resize);++i)if(b[0x54170+i]!=resize[i])return 0;
    p_s26gfResizeVectors=(S26GFResizeVectors)(b+0x54170);
    if(ext_MH_CreateHook(b+0x54540,(void*)s26gf_mover_ctor,(void**)&o_s26gfMoverCtor)||ext_MH_EnableHook(b+0x54540))return 0;
    static const u8 update[]={0x48,0x8b,0xc4,0x55,0x57,0x41,0x54,0x48,0x8d,0x68,0xa1,0x48,0x81,0xec,0xa0,0,0,0};
    static const u8 floats[]={0x48,0x89,0x5c,0x24,0x10,0x56,0x48,0x83,0xec,0x20,0x4c,0x8b,9,0x48,0x8b,0xda};
    for(u32 i=0;i<sizeof(update);++i)if(b[0x161510+i]!=update[i])return 0;
    for(u32 i=0;i<sizeof(floats);++i)if(b[0xaf5e0+i]!=floats[i])return 0;
    p_s26gfResizeFloats=(S26GFResizeVectors)(b+0xaf5e0);
    if(ext_MH_CreateHook(b+0x161510,(void*)s26gf_player_update,(void**)&o_s26gfPlayerUpdate)||ext_MH_EnableHook(b+0x161510))return 0;
    ext_Log(">>> S26GF ENEMY HISTORY READY: native 30/60 movement samples preserve half-second stuck-detection history at 60/120 Hz");return 1;
}
static u32 g_s26gdInstalled,g_s26gdTimerSeen;
static void* __attribute__((ms_abi)) s26gd_create_timer(void* system,i32 rate){
    /* The engine creates one timer. Leave every unexpected caller untouched. */
    if(g_s26gdTimerSeen++||rate!=60)return o_s26gdCreateTimer(system,rate);
    void* timer=o_s26gdCreateTimer(system,120);
    if(timer){if(g_s26ghStepThreshold)*g_s26ghStepThreshold=0.000025f;g_s26gdRateMultiplier=2u;ext_Log(">>> S26GD EXPERIMENTAL SIMULATION ACTIVE: native logic timer 120 Hz; timestep 1/120 s; startup-only; render/OpenXR pacing unchanged");}
    else{timer=o_s26gdCreateTimer(system,60);}
    return timer;
}
static i32 s26gd_requested(void){
    char path[512],b[96];
    if(!make_sibling_path(path,sizeof(path),"hpl3vr_simulation_rate.txt"))return 0;
    void* f=ext_fopen(path,"rb");if(!f)return 0;
    u64 n=ext_fread(b,1,sizeof(b),f);ext_fclose(f);
    /* Deliberately strict: only 120 and surrounding ASCII whitespace opt in. */
    if(!n||n==sizeof(b))return 0;
    u32 a=0,z=(u32)n;while(a<z&&(b[a]==' '||b[a]=='\r'||b[a]=='\n'||b[a]=='\t'))++a;
    while(z>a&&(b[z-1]==' '||b[z-1]=='\r'||b[z-1]=='\n'||b[z-1]=='\t'))--z;
    return z-a==3&&b[a]=='1'&&b[a+1]=='2'&&b[a+2]=='0';
}
static void s26gd_install(void){
    if(g_s26gdInstalled)return;g_s26gdInstalled=1;
    if(!s26gd_requested()){ext_Log(">>> S26GD SIMULATION: native 60 Hz default; experimental 120 Hz not requested");return;}
    u8* b=(u8*)ext_GetModuleHandleA(0);if(!b)return;
    u32 nt=*(u32*)(b+0x3c);
    if(nt<0x40||nt>0x1000||*(u32*)(b+nt)!=0x4550||
       *(u32*)(b+nt+8)!=0x6151d1cau||*(u32*)(b+nt+24+56)!=0x8fb000u){
        ext_Log(">>> S26GD SIMULATION: unsupported executable for 120 Hz experiment; native timer retained");return;
    }
    u8* target=b+0x364f10;
    static const u8 sig[]={0x48,0x89,0x5c,0x24,8,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0xf9,0xb9,0x50,0,0,0,0x8b,0xda};
    for(u32 i=0;i<sizeof(sig);++i)if(target[i]!=sig[i]){ext_Log(">>> S26GD SIMULATION: timer signature rejected; native rate retained");return;}
    if(!s26gd_prepare_damping()){
        ext_Log(">>> S26GD SIMULATION: required Newton damping correction unavailable; native 60 Hz retained");return;
    }
    if(!s26gf_prepare_mover(b)){
        ext_Log(">>> S26GF SIMULATION: required enemy history correction unavailable; native 60 Hz retained");return;
    }
    if(!s26gh_prepare_step_threshold(b)||!s26gh_prepare_ground_window(b)){
        ext_Log(">>> S26GH SIMULATION: step eligibility correction unavailable; native 60 Hz retained");return;
    }
    if(ext_MH_CreateHook(target,(void*)s26gd_create_timer,(void**)&o_s26gdCreateTimer)||ext_MH_EnableHook(target)){
        ext_Log(">>> S26GD SIMULATION: timer hook unavailable; native rate retained");return;
    }
    ext_Log(">>> S26GD SIMULATION ARMED: 120 Hz requested; waiting for native timer creation (no live timer mutation)");
}
