/* Persist next-launch selection only. Never alter the active timer/multiplier. */
static i32 s26ge_supported(void){
    const u8* b=(const u8*)ext_GetModuleHandleA(0);if(!b)return 0;
    u32 n=*(const u32*)(b+0x3c);
    return n>=0x40&&n<=0x1000&&*(const u32*)(b+n)==0x4550&&
        *(const u32*)(b+n+8)==0x6151d1cau&&*(const u32*)(b+n+24+56)==0x8fb000u;
}
static i32 s26ge_save_rate(i32 enabled){
    if(enabled&&!s26ge_supported())return 0;
    char path[512],temp[512];
    if(!make_sibling_path(path,sizeof(path),"hpl3vr_simulation_rate.txt")||
       !make_sibling_path(temp,sizeof(temp),"hpl3vr_simulation_rate.txt.pending"))return 0;
    typedef i32 (__attribute__((ms_abi)) *Move)(const char*,const char*,u32);
    typedef i32 (__attribute__((ms_abi)) *Delete)(const char*);
    void* kernel=ext_GetModuleHandleA("kernel32.dll");
    Move move=(Move)ext_GetProcAddress(kernel,"MoveFileExA");
    Delete remove=(Delete)ext_GetProcAddress(kernel,"DeleteFileA");
    if(!move||!remove)return 0;
    void* f=ext_fopen(temp,"wb");if(!f)return 0;
    const char* value=enabled?"120\n":"60\n";u64 size=enabled?4u:3u;
    u64 written=ext_fwrite(value,1,size,f);i32 closed=ext_fclose(f);
    if(written!=size||closed!=0){remove(temp);return 0;}
    if(!move(temp,path,9u)){remove(temp);return 0;} // replace + write-through
    ext_Log(">>> S26GE SIMULATION SELECTION SAVED: next launch %u Hz; active %u Hz unchanged; manual restart required",enabled?120u:60u,60u*g_s26gdRateMultiplier);
    return 1;
}
static u64 s26ge_rate_token(const void* command){
    if(h5748t_sso_eq(command,"GET",3u))return s26gd_requested();
    if(h5748t_sso_eq(command,"SUPPORTED",9u))return s26ge_supported();
    if(h5748t_sso_eq(command,"ON",2u))return s26ge_save_rate(1);
    if(h5748t_sso_eq(command,"OFF",3u))return s26ge_save_rate(0);
    return 0;
}
