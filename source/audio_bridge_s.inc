typedef void (__attribute__((ms_abi)) *S26SAudioUpdate)(void*);
typedef i32 (__attribute__((ms_abi)) *S26SListener)(void*,i32,const float*,const float*,const float*,const float*);
typedef i32 (__attribute__((ms_abi)) *S26SEventUpdate)(void*);
typedef i32 (__attribute__((ms_abi)) *S26SAudioTick)(void*,const float*,i32);
typedef void (__attribute__((ms_abi)) *S26SAudioEnd)(void*);
static S26SAudioUpdate o_s26sAudioUpdate,o_s26sAudioDestroy;
static S26SListener p_s26sListener;
static S26SEventUpdate p_s26sEventUpdate;
static S26SAudioTick p_s26sAudioTick;
static S26SAudioEnd p_s26sAudioEnd;
static volatile u32 g_s26sAudioMode=1; /* off / head tracked / binaural headphones */
static u8 g_s26sAudioHooked,g_s26sAudioTried,g_s26sAudioLoadTried;
static i32 g_s26sAudioVoices;
static u32 g_s26sAudioLogs;
static void s26s_load_audio(void){
    if(g_s26sAudioLoadTried)return;g_s26sAudioLoadTried=1;
    char path[1024];u32 n=ext_GetModuleFileNameA(0,path,sizeof(path));if(!n||n>=sizeof(path))return;
    i32 cut=-1;for(u32 k=0;k<n;++k)if(path[k]=='\\'||path[k]=='/')cut=(i32)k;
    const char tail[]="vr_audio_s\\hpl3vr_audio_s.dll";if(cut<0||(u32)cut+1+sizeof(tail)>sizeof(path))return;
    for(u32 k=0;k<sizeof(tail);++k)path[cut+1+(i32)k]=tail[k];
    typedef void* (__attribute__((ms_abi)) *Load)(const char*,void*,u32);
    Load load=(Load)ext_GetProcAddress(ext_GetModuleHandleA("kernel32.dll"),"LoadLibraryExA");
    void* dll=load?load(path,0,8u):0;if(!dll){ext_Log(">>> S26S binaural adapter unavailable; native sound retained");return;}
    p_s26sAudioTick=(S26SAudioTick)ext_GetProcAddress(dll,"S26AudioTick");p_s26sAudioEnd=(S26SAudioEnd)ext_GetProcAddress(dll,"S26AudioEnd");
    if(!p_s26sAudioTick||!p_s26sAudioEnd){p_s26sAudioTick=0;p_s26sAudioEnd=0;}
}
static void __attribute__((ms_abi)) s26s_audio_update(void* self){
    float head[12],forward[3],up[3];u32 mode=__atomic_load_n(&g_s26sAudioMode,__ATOMIC_RELAXED);
    if(!self||!h20_mem_readable(self,0xe0)||!mode||!s26s_view_frame(head,head+3)){
        if(self&&p_s26sAudioTick&&h20_mem_readable((u8*)self+0xd0,8))p_s26sAudioTick(*(void**)((u8*)self+0xd0),0,0);
        g_s26sAudioVoices=0;if(o_s26sAudioUpdate)o_s26sAudioUpdate(self);return;
    }
    for(i32 k=0;k<3;++k){forward[k]=-head[3+k*3+2];up[k]=-head[3+k*3+1];}
    /* Verified original negates native camera back/up for FMOD's left-handed
       listener convention. Position is unchanged world coordinates. */
    void* event=*(void**)((u8*)self+0xd8);void* system=*(void**)((u8*)self+0xd0);
    if(!event||!system){if(system&&p_s26sAudioTick)p_s26sAudioTick(system,0,0);g_s26sAudioVoices=0;if(o_s26sAudioUpdate)o_s26sAudioUpdate(self);return;}
    const float* velocity=(const float*)((u8*)self+0x80);float safeVelocity[3]={0,0,0};
    for(i32 k=0;k<3;++k)if(velocity[k]>-100&&velocity[k]<100)safeVelocity[k]=velocity[k];
    if(p_s26sListener(event,0,head,safeVelocity,forward,up)!=0){if(p_s26sAudioTick)p_s26sAudioTick(system,0,0);g_s26sAudioVoices=0;if(o_s26sAudioUpdate)o_s26sAudioUpdate(self);return;}
    if(mode==2u)s26s_load_audio();
    g_s26sAudioVoices=p_s26sAudioTick?p_s26sAudioTick(system,head,mode==2u):0;
    if(g_s26sAudioLogs<8u&&(g_s26sAudioLogs==0||g_s26sAudioVoices>0||g_s26sAudioVoices<0)){
        ++g_s26sAudioLogs;ext_Log(">>> S26S VR audio: mode %u binaural voices %d; HMD listener, authored FMOD events retained",mode,g_s26sAudioVoices);
    }
    p_s26sEventUpdate(event);
}
static void __attribute__((ms_abi)) s26s_audio_destroy(void* self){
    if(self&&p_s26sAudioEnd&&h20_mem_readable((u8*)self+0xd0,8))p_s26sAudioEnd(*(void**)((u8*)self+0xd0));
    if(o_s26sAudioDestroy)o_s26sAudioDestroy(self);
}
static i32 s26s_install_audio(void){
    if(g_s26sAudioTried)return g_s26sAudioHooked;g_s26sAudioTried=1;
    u8* b=(u8*)ext_GetModuleHandleA(0);if(!b)return 0;
    static const u32 rvas[2]={0x28f5f0,0x28ef70};
    static const u8 signatures[2][12]={S26S_AUDIO_SIGNATURE,S26S_AUDIO_DESTROY_SIGNATURE};
    for(i32 i=0;i<2;++i){if(!h20_mem_readable(b+rvas[i],12))return 0;for(i32 k=0;k<12;++k)if(b[rvas[i]+k]!=signatures[i][k])return 0;}
    p_s26sListener=(S26SListener)(void*)(b+0x625908);p_s26sEventUpdate=(S26SEventUpdate)(void*)(b+0x625902);
    if(!h20_mem_executable((void*)p_s26sListener)||!h20_mem_executable((void*)p_s26sEventUpdate))return 0;
    if(ext_MH_CreateHook(b+rvas[1],(void*)s26s_audio_destroy,(void**)&o_s26sAudioDestroy)||ext_MH_EnableHook(b+rvas[1]))return 0;
    if(ext_MH_CreateHook(b+rvas[0],(void*)s26s_audio_update,(void**)&o_s26sAudioUpdate)||ext_MH_EnableHook(b+rvas[0]))return 0;
    g_s26sAudioHooked=1;return 1;
}
static u64 s26s_audio_token(const H5730TString* cls,const H5730TString* fn){
    (void)cls;
    if(h5748t_sso_eq(fn,"ACTIVE",6u))return g_s26sAudioVoices>0;
    if(fn&&fn->size==1u&&fn->capacity<=15u){u32 mode=fn->storage[0]-'0';if(mode<3u){
        __atomic_store_n(&g_s26sAudioMode,mode,__ATOMIC_RELAXED);if(mode)s26s_install_audio();return 1;
    }}return 0;
}
