static void c37_report(C37Context*c){
 unsigned held=(g_h14GripBody[0]!=0)|((g_h14GripBody[1]!=0)<<1),detail=c->requested|(c->n<<4)|(held<<8);
 c37Counts[c->n==8?3:c->n==4?2:c->n==2?1:0]++;
 cpu14_event(53,detail,c->start,c->joined,c->count);
 if(c->n){cpu14_event(54,detail,c->start,c->queued,c->count);cpu14_event(55,detail,c->queued,c->joined,c->count);for(unsigned i=0;i<c->n;i++)cpu14_event(56,detail|(i<<16),c->begin[i],c->end[i],c->count);}
}
static void c37_install(void){static u32 once;if(once)return;once=1;u8*m=ext_GetModuleHandleA("Newton.dll");if(!m)return;
 const u8 sig[]={0x48,0x89,0x5c,0x24,0x10,0x48,0x89,0x6c,0x24,0x18,0x48,0x89,0x74,0x24,0x20};
 for(u32 i=0;i<sizeof(sig);i++)if(m[0x1bf50+i]!=sig[i])return;
 c37Queue=(void*)(m+0x8aa0);c37Join=(void*)(m+0x8e40);i32 a=ext_MH_CreateHook(m+0x1bf50,(void*)c37_job,(void**)&c37Execute),b=a?a:ext_MH_EnableHook(m+0x1bf50);ext_Log(">>> CPU37 paired collision schedule create %d enable %d",a,b);
}
