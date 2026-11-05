static void c36_install(void){
 static u32 attempted;if(attempted)return;attempted=1;
 u8*m=ext_GetModuleHandleA("Newton.dll");if(!m)return;
 const u8 a[]={0x48,0x89,0x5c,0x24,0x10,0x48,0x89,0x6c,0x24,0x18,0x48,0x89,0x74,0x24,0x20};
 for(u32 i=0;i<sizeof(a);i++)if(m[0x1bf50+i]!=a[i])return;
 c36Queue=(void*)(m+0x8aa0);c36Join=(void*)(m+0x8e40);
 i32 h=ext_MH_CreateHook(m+0x1bf50,(void*)c36_job,(void**)&c36Execute),e=h?h:ext_MH_EnableHook(m+0x1bf50);
 ext_Log(">>> CPU36 private SSE job dispatch create %d enable %d",h,e);
}
