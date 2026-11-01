/* Experimental same-job hand/scene zero-result reuse. Newton SHA256 and both
   entry points are verified before installation. All native pairs survive.
   See docs/CPU43.md for offsets, parity evidence and remaining limitations. */
#ifndef CPU_HAND_MESH
#define CPU_HAND_MESH 0
#endif
#if CPU_HAND_MESH
static u32 (*c44ThreadId)(void);
static i32 (*c44Counter)(u64*);
static u64 c44Frequency;
static u32 c44Owner,c44Depth,c44Ready;
static const void*c44World;
static void(*c44Execute)(void*);
static u64 c44_now(void){u64 n=0;c44Counter(&n);return n;}
#define C43_MAIN() (c44ThreadId() == __atomic_load_n(&c44Owner,__ATOMIC_ACQUIRE) && c44Depth == 1u)
#define C43_NOW() c44_now()
#define C43_TARGET(a,b) ((a)==g_h34HandNewton[0]||(a)==g_h34HandNewton[1]||(b)==g_h34HandNewton[0]||(b)==g_h34HandNewton[1])
#define C43_MIN_TICKS (c44Frequency/10000u)
#define C43_SHADOW 0
#include "cpu_hand_mesh_core.inc"
#include "cpu_leaf_filter.inc"
typedef struct {void**vt;int index,pad,stride,limit,mode;float dt;void*world;} C44Job;
static void c44_job(void*p){
    C44Job*j=p;
    if(C43_MAIN()&&c43Active){c43Active=0;c44Execute(p);c43_begin(0);return;}
    if(!c44Ready||!C43_MAIN()||j->world!=c44World||j->mode!=1||j->index||j->stride!=1){c44Execute(p);return;}
    c43_begin(1);c44Execute(p);c43Active=0;
}
/* Hash the actual loaded module's file with Windows CNG; Unicode paths retained.
   Missing APIs, unexpected files or failed reads leave original Newton active. */
static i32 c44_verify(void*module,void*k){
    void*(*load)(const unsigned short*)=(void*)ext_GetProcAddress(k,"LoadLibraryW");
    u32(*path)(void*,unsigned short*,u32)=(void*)ext_GetProcAddress(k,"GetModuleFileNameW");
    void*(*open)(const unsigned short*,u32,u32,void*,u32,u32,void*)=(void*)ext_GetProcAddress(k,"CreateFileW");
    i32(*read)(void*,void*,u32,u32*,void*)=(void*)ext_GetProcAddress(k,"ReadFile");
    i32(*close)(void*)=(void*)ext_GetProcAddress(k,"CloseHandle");
    if(!load||!path||!open||!read||!close)return 0;
    void*cng=load((const unsigned short*)L"bcrypt.dll");if(!cng)return 0;
    i32(*oa)(void**,const unsigned short*,const unsigned short*,u32)=(void*)ext_GetProcAddress(cng,"BCryptOpenAlgorithmProvider");
    i32(*gp)(void*,const unsigned short*,u8*,u32,u32*,u32)=(void*)ext_GetProcAddress(cng,"BCryptGetProperty");
    i32(*ch)(void*,void**,u8*,u32,u8*,u32,u32)=(void*)ext_GetProcAddress(cng,"BCryptCreateHash");
    i32(*hd)(void*,u8*,u32,u32)=(void*)ext_GetProcAddress(cng,"BCryptHashData");
    i32(*fh)(void*,u8*,u32,u32)=(void*)ext_GetProcAddress(cng,"BCryptFinishHash");
    i32(*dh)(void*)=(void*)ext_GetProcAddress(cng,"BCryptDestroyHash");
    i32(*ca)(void*,u32)=(void*)ext_GetProcAddress(cng,"BCryptCloseAlgorithmProvider");
    if(!oa||!gp||!ch||!hd||!fh||!dh||!ca)return 0;
    unsigned short*name=ext_malloc(65536);u8*buffer=ext_malloc(65536),*object=0;
    void*alg=0,*hash=0,*file=(void*)(u64)-1;u32 bytes=0,length=0,got=0;u64 total=0;i32 ok=0;u8 digest[32];
    const u8 expected[32]={0x1b,0xe4,0x51,0xfb,0x2e,0x25,0x0a,0xde,0xd9,0xdd,0xf3,0x77,0x14,0x18,0xce,0xe2,0x19,0x90,0xe4,0xef,0x07,0xfa,0x0f,0xef,0xe0,0xa8,0xcf,0xaf,0x55,0x76,0x6b,0x74};
    if(!name||!buffer)goto done;
    length=path(module,name,32768);if(!length||length>=32768)goto done;
    file=open(name,0x80000000u,7,0,3,0x80,0);if(file==(void*)(u64)-1)goto done;
    if(oa(&alg,(const unsigned short*)L"SHA256",0,0)<0)goto done;
    if(gp(alg,(const unsigned short*)L"ObjectLength",(u8*)&bytes,4,&got,0)<0||got!=4||!bytes||bytes>1048576)goto done;
    object=ext_malloc(bytes);if(!object||ch(alg,&hash,object,bytes,0,0,0)<0)goto done;
    for(;;){got=0;if(!read(file,buffer,65536,&got,0))goto done;if(!got)break;total+=got;if(total>16777216||hd(hash,buffer,got,0)<0)goto done;}
    if(fh(hash,digest,32,0)<0)goto done;
    ok=c43_equal(digest,expected,32);
done:
    if(hash)dh(hash);if(alg)ca(alg,0);if(file!=(void*)(u64)-1)close(file);
    if(object)ext_free(object);if(buffer)ext_free(buffer);if(name)ext_free(name);return ok;
}
static void c44_install(void*module){
    static u32 attempted;if(attempted)return;attempted=1;
    void*k=ext_GetModuleHandleA("kernel32.dll");if(!k||!c44_verify(module,k)){ext_Log(">>> CPU HAND MESH: native fallback (unverified Newton)");return;}
    c44ThreadId=(void*)ext_GetProcAddress(k,"GetCurrentThreadId");c44Counter=(void*)ext_GetProcAddress(k,"QueryPerformanceCounter");
    i32(*freq)(u64*)=(void*)ext_GetProcAddress(k,"QueryPerformanceFrequency");
    if(!c44ThreadId||!c44Counter||!freq||!freq(&c44Frequency)||c44Frequency<10000)return;
    const u8 js[]={0x48,0x89,0x5c,0x24,0x10,0x48,0x89,0x6c,0x24,0x18,0x48,0x89,0x74,0x24,0x20};
    const u8 ks[]={0x4c,0x8b,0xdc,0x49,0x89,0x5b,0x08,0x49,0x89,0x6b,0x10,0x49,0x89,0x73,0x18};
    u8*m=module;if(!c43_equal(m+0x1bf50,js,sizeof(js))||!c43_equal(m+0x39a00,ks,sizeof(ks)))return;
    if(ext_MH_CreateHook(m+0x39a00,(void*)c43_pair,(void**)&c43Kernel)||ext_MH_CreateHook(m+0x1bf50,(void*)c44_job,(void**)&c44Execute))return;
    if(ext_MH_EnableHook(m+0x39a00)||ext_MH_EnableHook(m+0x1bf50))return;
    c56_install(m);c44Ready=1;ext_Log(">>> CPU HAND MESH: verified same-job zero-result reuse enabled");
}
static u32 c44_enter(const void*w,u32 permitted){
    if(!c44Ready)return 0;u32 id=c44ThreadId(),zero=0;__atomic_compare_exchange_n(&c44Owner,&zero,id,0,__ATOMIC_ACQ_REL,__ATOMIC_ACQUIRE);if(id!=__atomic_load_n(&c44Owner,__ATOMIC_ACQUIRE))return 0;
    ++c44Depth;if(c44Depth==1)c44World=permitted?w:0;return 1;
}
static void c44_leave(u32 entered){if(entered){c43Active=0;if(--c44Depth==0)c44World=0;}}
#else
#define c44_install(m) ((void)0)
#define c44_enter(w,p) 0u
#define c44_leave(e) ((void)(e))
#endif
