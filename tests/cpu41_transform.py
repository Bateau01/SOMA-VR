from pathlib import Path

def transform(code,root,metadata=False):
 prefix='#define C41_MAIN() C37_MAIN()\n#define C41_NOW() c37_now()\n'+(root/'tests/cpu41_pair.inc').read_text()
 marker='/* Private synchronous native-job scheduling.'
 assert marker in code;code=code.replace(marker,prefix+'\n'+marker,1)
 code=code.replace('#define C37_MODE(j) c37_mode()','#define C37_MODE(j) 0u')
 needle='C37Context c={0};';assert code.count(needle)==1
 code=code.replace(needle,'c41Count=c41Overflow=0;c41Active=(g_h14PhysicsSteps%8u)==0u;'+needle)
 needle='static void c37_report(C37Context*c){';assert code.count(needle)==1
 code=code.replace(needle,needle+'''c41Active=0;
 for(unsigned i=0;i<c41Count;i++){C41Pair*q=c41Pairs+i;unsigned hands=(h35_is_hand_proxy_body(q->body0)?1u:0u)|(h35_is_hand_proxy_body(q->body1)?2u:0u);unsigned held=(q->body0==g_h14GripBody[0]||q->body0==g_h14GripBody[1]?1u:0u)|(q->body1==g_h14GripBody[0]||q->body1==g_h14GripBody[1]?2u:0u);unsigned detail=(q->type0&31u)|((q->type1&31u)<<5)|(hands<<10)|(held<<12)|(q->contacts<<16);cpu14_event(57,detail,q->a,q->b,(u64)q->body0);cpu14_event(58,detail,q->a,q->b,(u64)q->body1);}
 if(c41Overflow)cpu14_event(59,c41Overflow,c->start,c->joined,c->count);
 ''')
 needle='c37Queue=(void*)(m+0x8aa0);';assert code.count(needle)==1
 code=code.replace(needle,'''const u8 ks[]={0x4c,0x8b,0xdc,0x49,0x89,0x5b,0x08,0x49,0x89,0x6b,0x10,0x49,0x89,0x73,0x18};for(u32 k=0;k<sizeof(ks);k++)if(m[0x39a00+k]!=ks[k])return;
 i32 ka=ext_MH_CreateHook(m+0x39a00,(void*)c41_pair,(void**)&c41Kernel),kb=ka?ka:ext_MH_EnableHook(m+0x39a00);ext_Log(">>> CPU41 pair observer create %d enable %d",ka,kb);if(kb)return;
 '''+needle)
 if metadata:
  marker='static void c37_report(C37Context*c){'
  helper=(root/'tests/cpu41_names.inc').read_text()
  code=code.replace(marker,helper+'\n'+marker,1)
  needle='cpu14_event(58,detail,q->a,q->b,(u64)q->body1);'
  code=code.replace(needle,needle+'if(q->b-q->a>=cpuFreq/10000u){cpu14_event(60,detail,q->a,q->b,(u64)q->pair);cpu14_event(61,detail,q->a,q->b,(u64)q->raw10);cpu14_event(62,detail,q->a,q->b,(u64)q->raw18);c41_name(q->body0);c41_name(q->body1);}')
 return code
