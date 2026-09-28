/* SOMA FMOD Ex adapter. Steam Audio supplies HRTF only: authored attenuation,
   occlusion, reverb, event automation and non-positional audio remain FMOD-owned. */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include "../reference/fmod.h"
#include "../reference/fmod_dsp.h"
#include "../reference/steamaudio/include/phonon.h"
#include "../reference/steamaudio/include/phonon_version.h"
#define FMOD_FUNCTIONS(X) \
 X(System_GetVersion) X(System_GetSoftwareFormat) X(System_GetChannel) X(System_LockDSP) X(System_UnlockDSP) \
 X(System_CreateDSP) X(Channel_IsPlaying) X(Channel_IsVirtual) X(Channel_GetCurrentSound) X(Channel_GetMode) \
 X(Channel_Get3DAttributes) X(Channel_Get3DPanLevel) X(Channel_Set3DPanLevel) X(Channel_AddDSP) \
 X(Sound_GetFormat) X(DSP_Remove) X(DSP_Release) X(DSP_GetUserData) X(DSP_SetActive)
/* A private child bus provides a stereo processing point AFTER the mono voice's
   native panner, retaining its original parent bus and all authored automation. */
#define GROUP_FUNCTIONS(X) X(System_CreateChannelGroup) X(Channel_GetChannelGroup) X(Channel_SetChannelGroup) X(ChannelGroup_Release) X(ChannelGroup_AddGroup) X(ChannelGroup_GetParentGroup) X(ChannelGroup_AddDSP)
#define DECL_F(n) static __typeof__(&FMOD_##n) f_##n;
FMOD_FUNCTIONS(DECL_F)
GROUP_FUNCTIONS(DECL_F)
#define IPL_FUNCTIONS(X) X(ContextCreate) X(ContextRelease) X(HRTFCreate) X(HRTFRelease) X(BinauralEffectCreate) X(BinauralEffectRelease) X(BinauralEffectApply) X(BinauralEffectReset)
#define DECL_I(n) static __typeof__(&ipl##n) a_##n;
IPL_FUNCTIONS(DECL_I)
#define BLOCK 128
#define VOICES 64
typedef struct Voice {
    FMOD_CHANNEL* channel;FMOD_SOUND* sound;FMOD_DSP* dsp;FMOD_CHANNELGROUP* group;
    IPLBinauralEffect effect;float originalPan;int channelId;
    volatile LONG direction[3],unsupported;
    float input[BLOCK],left[BLOCK],right[BLOCK];int fill,read,available;
#ifdef S26S_AUDIO_TEST
    float peakInput,peakOutput;unsigned calls;
#endif
} Voice;
static Voice* voices[VOICES];
static IPLContext context;static IPLHRTF hrtf;static IPLAudioSettings audio;
static FMOD_SYSTEM* owner;static HMODULE phonon;static int ready,attempted,cursor;
/* Cache expensive initialization failure for this exact mixer format. A format
   change, explicit disable, or system shutdown permits another attempt. */
static FMOD_SYSTEM* failedSystem;static int failedRate,failedOutputs;
static volatile LONG activeCount,unsupportedCount;
/* Remember unsupported layouts for this playback, without retry allocation. */
static struct {FMOD_CHANNEL* channel;FMOD_SOUND* sound;} rejected[1000];
static float finite_sample(float v){return isfinite(v)?v:0;}
static void store_float(volatile LONG* p,float x){LONG bits;memcpy(&bits,&x,4);InterlockedExchange(p,bits);}
static float load_float(volatile LONG* p){LONG bits=InterlockedCompareExchange(p,0,0);float x;memcpy(&x,&bits,4);return x;}
static void dry_copy(const float* in,float* out,unsigned length,int ni,int no){
    for(unsigned i=0;i<length;++i)for(int c=0;c<no;++c)out[i*(unsigned)no+(unsigned)c]=ni>0?finite_sample(in[i*(unsigned)ni+(unsigned)(c<ni?c:0)]):0;
}
static FMOD_RESULT F_CALLBACK create_voice(FMOD_DSP_STATE* state){void* v=0;if(f_DSP_GetUserData(state->instance,&v)!=FMOD_OK||!v)return FMOD_ERR_INTERNAL;state->plugindata=v;return FMOD_OK;}
static FMOD_RESULT F_CALLBACK reset_voice(FMOD_DSP_STATE* state){Voice* v=state->plugindata;if(v){v->fill=v->read=v->available=0;a_BinauralEffectReset(v->effect);}return FMOD_OK;}
static FMOD_RESULT F_CALLBACK read_voice(FMOD_DSP_STATE* state,float* in,float* out,unsigned length,int ni,int no){
    Voice* v=state->plugindata;
#ifdef S26S_AUDIO_TEST
    if(v)++v->calls;
#endif
    if(!v||(ni!=1&&ni!=2)||no!=2){if(v)InterlockedExchange(&v->unsupported,1+ni*16+no);dry_copy(in,out,length,ni,no);return FMOD_OK;}
    IPLBinauralEffectParams params={0};
    params.direction.x=load_float(&v->direction[0]);params.direction.y=load_float(&v->direction[1]);params.direction.z=load_float(&v->direction[2]);
    float n=sqrtf(params.direction.x*params.direction.x+params.direction.y*params.direction.y+params.direction.z*params.direction.z);
    if(!isfinite(n)||n<.1f){params.direction.x=0;params.direction.y=0;params.direction.z=-1;}else {params.direction.x/=n;params.direction.y/=n;params.direction.z/=n;}
    params.interpolation=IPL_HRTFINTERPOLATION_BILINEAR;params.spatialBlend=1;params.hrtf=hrtf;
    float* inputs[]={v->input};float* outputs[]={v->left,v->right};
    IPLAudioBuffer input={1,BLOCK,inputs},output={2,BLOCK,outputs};
    for(unsigned i=0;i<length;++i){
        /* Only mono source assets enter this private stereo bus. Reconstruct
           their signed amplitude while preserving the panner's total energy.
           Distance/occlusion/voice gain remain in the signal; native pan itself
           need not be disabled or guessed, and stereo assets are never folded. */
        float l=finite_sample(in[i*(unsigned)ni]),r=ni==2?finite_sample(in[2*i+1]):0;
        float sample=copysignf(sqrtf(l*l+r*r),l+r);
#ifdef S26S_AUDIO_TEST
        if(fabsf(sample)>v->peakInput)v->peakInput=fabsf(sample);
#endif
        out[2*i]=v->available?finite_sample(v->left[v->read]):0;
        out[2*i+1]=v->available?finite_sample(v->right[v->read]):0;
        if(v->available){--v->available;++v->read;}
        v->input[v->fill++]=sample;
        if(v->fill==BLOCK){a_BinauralEffectApply(v->effect,&params,&input,&output);v->fill=0;v->read=0;v->available=BLOCK;}
#ifdef S26S_AUDIO_TEST
        if(fabsf(out[2*i])>v->peakOutput)v->peakOutput=fabsf(out[2*i]);
#endif
    }
    return FMOD_OK;
}
static void remove_voice(int i){
    Voice* v=voices[i];if(!v)return;voices[i]=0;
    if(v->dsp){f_DSP_Remove(v->dsp);f_DSP_Release(v->dsp);}
    FMOD_SOUND* current=0;
    FMOD_CHANNELGROUP* group=0,*parent=0;
    if(v->group&&f_Channel_GetCurrentSound(v->channel,&current)==FMOD_OK&&current==v->sound&&
       f_Channel_GetChannelGroup(v->channel,&group)==FMOD_OK&&group==v->group&&
       f_ChannelGroup_GetParentGroup(v->group,&parent)==FMOD_OK&&parent)f_Channel_SetChannelGroup(v->channel,parent);
    if(v->group)f_ChannelGroup_Release(v->group);
    if(v->effect)a_BinauralEffectRelease(&v->effect);free(v);
}
static int load_apis(void){
    HMODULE fmod=GetModuleHandleA("fmodex64.dll");if(!fmod)return 0;
    #define LOAD_F(n) f_##n=(__typeof__(f_##n))(void*)GetProcAddress(fmod,"FMOD_"#n);if(!f_##n)return 0;
    FMOD_FUNCTIONS(LOAD_F)
    GROUP_FUNCTIONS(LOAD_F)
    char path[1024];HMODULE self=0;
    if(!GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,(const char*)(void*)&load_apis,&self))return 0;
    DWORD n=GetModuleFileNameA(self,path,sizeof(path));if(!n||n>=sizeof(path))return 0;
    char* slash=strrchr(path,'\\');if(!slash)return 0;strcpy(slash+1,"phonon.dll");
    phonon=LoadLibraryExA(path,0,LOAD_WITH_ALTERED_SEARCH_PATH);if(!phonon)return 0;
    #define LOAD_I(n) a_##n=(__typeof__(a_##n))(void*)GetProcAddress(phonon,"ipl"#n);if(!a_##n)return 0;
    IPL_FUNCTIONS(LOAD_I)
    return 1;
}
static int initialize(FMOD_SYSTEM* system){
    if(!ready){if(attempted)return 0;attempted=1;if(!load_apis())return 0;ready=1;}
    unsigned version=0;if(f_System_GetVersion(system,&version)!=FMOD_OK||version<0x44400||version>=0x44500)return 0;
    int rate=0,outputs=0;FMOD_SOUND_FORMAT format;
    if(f_System_GetSoftwareFormat(system,&rate,&format,&outputs,0,0,0)!=FMOD_OK||rate<22050||rate>192000||outputs!=2)return 0;
    if(owner&&owner!=system)return 0;
    if(owner&&audio.samplingRate!=rate)return 0;
    if(!owner){
        if(failedSystem==system&&failedRate==rate&&failedOutputs==outputs)return 0;
        failedSystem=system;failedRate=rate;failedOutputs=outputs;
        IPLContextSettings settings={0};settings.version=STEAMAUDIO_VERSION;settings.simdLevel=IPL_SIMDLEVEL_SSE2;
        if(a_ContextCreate(&settings,&context)!=IPL_STATUS_SUCCESS)return 0;
        audio.samplingRate=rate;audio.frameSize=BLOCK;
        IPLHRTFSettings hs={0};hs.type=IPL_HRTFTYPE_DEFAULT;hs.volume=1;hs.normType=IPL_HRTFNORMTYPE_RMS;
        if(a_HRTFCreate(context,&audio,&hs,&hrtf)!=IPL_STATUS_SUCCESS){a_ContextRelease(&context);return 0;}
        owner=system;
        failedSystem=0;
    }
    return 1;
}
static int detach_all(FMOD_SYSTEM* system){
    if(owner!=system)return 1;
    if(f_System_LockDSP(system)!=FMOD_OK)return 0;
    for(int i=0;i<VOICES;++i)remove_voice(i);
    f_System_UnlockDSP(system);InterlockedExchange(&activeCount,0);return 1;
}
static void direction(Voice* v,const FMOD_VECTOR* pos,const float head[12]){
    float delta[3]={pos->x-head[0],pos->y-head[1],pos->z-head[2]};
    for(int k=0;k<3;++k)store_float(&v->direction[k],delta[0]*head[3+k]+delta[1]*head[6+k]+delta[2]*head[9+k]);
}
/* Called on SOMA's audio-update/game thread. A bounded 128-channel discovery
   slice complements immediate maintenance of the maximum 64 owned voices. */
__declspec(dllexport) int S26AudioTick(FMOD_SYSTEM* system,const float head[12],int enabled){
    if(!system)return 0;
    if(!enabled){if(failedSystem==system)failedSystem=0;return detach_all(system)?0:-2;}
    if(!head||!initialize(system)){detach_all(system);return -1;}
    for(int k=0;k<12;++k)if(!isfinite(head[k])){detach_all(system);return -1;}
    if(f_System_LockDSP(system)!=FMOD_OK)return -2;
    int count=0;
    for(int i=0;i<VOICES;++i){Voice* v=voices[i];if(!v)continue;FMOD_BOOL playing=0,virt=0;FMOD_SOUND* sound=0;FMOD_VECTOR pos;FMOD_CHANNELGROUP* group=0;
        if(InterlockedCompareExchange(&v->unsupported,0,0)||f_Channel_IsPlaying(v->channel,&playing)!=FMOD_OK||!playing||f_Channel_IsVirtual(v->channel,&virt)!=FMOD_OK||virt||f_Channel_GetCurrentSound(v->channel,&sound)!=FMOD_OK||sound!=v->sound||f_Channel_GetChannelGroup(v->channel,&group)!=FMOD_OK||group!=v->group||f_Channel_Get3DAttributes(v->channel,&pos,0)!=FMOD_OK){
            if(v->unsupported){InterlockedIncrement(&unsupportedCount);rejected[v->channelId].channel=v->channel;rejected[v->channelId].sound=v->sound;}remove_voice(i);continue;
        }direction(v,&pos,head);++count;
    }
    for(int scan=0;scan<128&&count<VOICES;++scan){
        int id=cursor;cursor=(cursor+1)%1000;
        FMOD_CHANNEL* channel=0;FMOD_SOUND* sound=0;FMOD_BOOL playing=0,virt=0;FMOD_MODE mode=0;int channels=0;FMOD_VECTOR pos;
        if(f_System_GetChannel(system,id,&channel)!=FMOD_OK||!channel)continue;
        int known=0,slot=-1;for(int i=0;i<VOICES;++i){if(voices[i]&&voices[i]->channel==channel)known=1;if(!voices[i]&&slot<0)slot=i;}if(known||slot<0)continue;
        if(f_Channel_IsPlaying(channel,&playing)!=FMOD_OK||!playing||f_Channel_IsVirtual(channel,&virt)!=FMOD_OK||virt||f_Channel_GetMode(channel,&mode)!=FMOD_OK||!(mode&FMOD_3D)||
           (mode&FMOD_3D_HEADRELATIVE)||f_Channel_GetCurrentSound(channel,&sound)!=FMOD_OK||f_Sound_GetFormat(sound,0,0,&channels,0)!=FMOD_OK||channels!=1||f_Channel_Get3DAttributes(channel,&pos,0)!=FMOD_OK)continue;
        if(rejected[id].channel==channel&&rejected[id].sound==sound)continue;rejected[id].channel=0;
        Voice* v=calloc(1,sizeof(*v));if(!v)break;v->channel=channel;v->sound=sound;v->channelId=id;
        if(f_Channel_Get3DPanLevel(channel,&v->originalPan)!=FMOD_OK){free(v);continue;}
        IPLBinauralEffectSettings es={hrtf};if(a_BinauralEffectCreate(context,&audio,&es,&v->effect)!=IPL_STATUS_SUCCESS){free(v);continue;}
        direction(v,&pos,head);
        FMOD_DSP_DESCRIPTION desc={0};strcpy(desc.name,"SOMA VR Binaural");desc.version=0x10000;desc.channels=0;desc.create=create_voice;desc.reset=reset_voice;desc.read=read_voice;desc.userdata=v;
        if(f_System_CreateDSP(system,&desc,&v->dsp)!=FMOD_OK){a_BinauralEffectRelease(&v->effect);free(v);continue;}
        voices[slot]=v;FMOD_CHANNELGROUP* parent=0;
        if(f_Channel_GetChannelGroup(channel,&parent)!=FMOD_OK||!parent||f_System_CreateChannelGroup(system,"SOMA VR source",&v->group)!=FMOD_OK||
           f_ChannelGroup_AddGroup(parent,v->group)!=FMOD_OK||f_ChannelGroup_AddDSP(v->group,v->dsp,0)!=FMOD_OK||
           f_DSP_SetActive(v->dsp,1)!=FMOD_OK||f_Channel_SetChannelGroup(channel,v->group)!=FMOD_OK){remove_voice(slot);continue;}
        ++count;
    }
    f_System_UnlockDSP(system);InterlockedExchange(&activeCount,count);return count;
}
/* Caller invokes before the original FMOD system release. */
__declspec(dllexport) void S26AudioEnd(FMOD_SYSTEM* system){
    if(failedSystem==system)failedSystem=0;
    if(owner!=system)return;
    /* On a failed mixer lock, retain effect dependencies rather than freeing
       storage that the mixer can still access. The original system owns shutdown. */
    if(!detach_all(system))return;
    if(hrtf)a_HRTFRelease(&hrtf);if(context)a_ContextRelease(&context);owner=0;cursor=0;memset(rejected,0,sizeof(rejected));
}
__declspec(dllexport) int S26AudioStatus(void){return (int)InterlockedCompareExchange(&activeCount,0,0);}
