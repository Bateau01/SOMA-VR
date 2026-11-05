def transform(code,root,shadow=True,invert=False):
 prefix='''#define C43_MAIN() C37_MAIN()
#define C43_NOW() c37_now()
#define C43_TARGET(a,b) ((a)==g_h34HandNewton[0]||(a)==g_h34HandNewton[1]||(b)==g_h34HandNewton[0]||(b)==g_h34HandNewton[1])
#define C43_MIN_TICKS (cpuFreq/10000u)
'''+f'#define C43_SHADOW {int(shadow)}\n'+(root/'tests/cpu43_reuse.inc').read_text()
 marker='/* Private synchronous native-job scheduling.';assert code.count(marker)==1
 code=code.replace(marker,prefix+'\n'+marker)
 code=code.replace('#define C37_MODE(j) c37_mode()','#define C37_MODE(j) 0u')
 enabled='((g_h14PhysicsSteps/97u)%4u==1u||(g_h14PhysicsSteps/97u)%4u==2u)'
 if invert:enabled='(!'+enabled+')'
 code=code.replace('C37Context c={0};','c43_begin('+('1u' if shadow else enabled)+');C37Context c={0};')
 marker='static void c37_report(C37Context*c){';assert code.count(marker)==1
 code=code.replace(marker,marker+'''unsigned active=c43Active;c43Active=0;
 cpu14_event(63,active,c->start,c->joined,c43Hits);cpu14_event(64,active,c->start,c->joined,c43Eligible);cpu14_event(65,active,c->start,c->joined,c43Mismatch);cpu14_event(66,active,c->start,c->joined,c43Saved);
''')
 needle='c37Queue=(void*)(m+0x8aa0);';assert code.count(needle)==1
 code=code.replace(needle,'''const u8 ks[]={0x4c,0x8b,0xdc,0x49,0x89,0x5b,0x08,0x49,0x89,0x6b,0x10,0x49,0x89,0x73,0x18};for(u32 k=0;k<sizeof(ks);k++)if(m[0x39a00+k]!=ks[k])return;
 i32 ka=ext_MH_CreateHook(m+0x39a00,(void*)c43_pair,(void**)&c43Kernel),kb=ka?ka:ext_MH_EnableHook(m+0x39a00);ext_Log(">>> CPU43 narrow zero pair create %d enable %d",ka,kb);if(kb)return;
'''+needle)
 return code
