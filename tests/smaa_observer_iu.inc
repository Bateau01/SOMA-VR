/* Test build only: bounded GPU query/capture observer. Never shipped enabled. */
static i32 g_s26iuTestMode=-1;
static u32 iuQuery[8],iuPending[8],iuQueryMode[8],iuNext,iuActive,iuCaptured[10][2];
static unsigned long long iuTotal[10];static u32 iuSamples[10];
static void (__attribute__((ms_abi)) *iuGenQ)(i32,u32*);
static void (__attribute__((ms_abi)) *iuBeginQ)(u32,u32);
static void (__attribute__((ms_abi)) *iuEndQ)(u32);
static void (__attribute__((ms_abi)) *iuGetQ)(u32,u32,u32*);
static void (__attribute__((ms_abi)) *iuResultQ)(u32,u32,unsigned long long*);
static void (__attribute__((ms_abi)) *iuCurrentQ)(u32,u32,i32*);
static void s26iu_test_begin(void){
 if(g_s26iuTestMode<0||g_s26iuTestMode>9||!s26iu_api())return;
 if(!iuGenQ){void* gl=ext_GetModuleHandleA("opengl32.dll");PFN_H5750A_WglGetProcAddress wg=(void*)ext_GetProcAddress(gl,"wglGetProcAddress");
 iuGenQ=(void*)s26_gl_proc(gl,wg,"glGenQueries");iuBeginQ=(void*)s26_gl_proc(gl,wg,"glBeginQuery");iuEndQ=(void*)s26_gl_proc(gl,wg,"glEndQuery");iuGetQ=(void*)s26_gl_proc(gl,wg,"glGetQueryObjectuiv");iuResultQ=(void*)s26_gl_proc(gl,wg,"glGetQueryObjectui64v");iuCurrentQ=(void*)s26_gl_proc(gl,wg,"glGetQueryiv");
 if(!iuGenQ||!iuBeginQ||!iuEndQ||!iuGetQ||!iuResultQ||!iuCurrentQ)return;iuGenQ(8,iuQuery);}
 for(i32 k=0;k<8;k++)if(iuPending[k]){u32 available=0;iuGetQ(iuQuery[k],0x8867,&available);if(available){unsigned long long ns=0;iuResultQ(iuQuery[k],0x8866,&ns);u32 mode=iuQueryMode[k];iuTotal[mode]+=ns;iuSamples[mode]++;iuPending[k]=0;
 if(iuSamples[mode]==64||iuSamples[mode]==128)ext_Log(">>> IU_GPU phase %u samples %u stereo-post-gpu-ms %.5f",mode,iuSamples[mode],(double)iuTotal[mode]/iuSamples[mode]/1000000.);}}
 if(iuSamples[g_s26iuTestMode]>=128)return;
 i32 current=0;iuCurrentQ(0x88bf,0x8865,&current);if(current)return;
 u32 i=iuNext++%8;if(iuPending[i])return;iuQueryMode[i]=g_s26iuTestMode;iuBeginQ(0x88bf,iuQuery[i]);iuActive=i+1;
}
static void s26iu_test_end(void){if(iuActive){iuEndQ(0x88bf);iuPending[iuActive-1]=1;iuActive=0;}}
static void s26iu_test_eye(i32 eye,u32 target,i32 w,i32 h){
 i32 m=g_s26iuTestMode;if(m<0||m>9||eye<0||eye>1||iuSamples[m]<20||iuCaptured[m][eye]||!s26iu_api())return;

 iuCaptured[m][eye]=1;
 S26IUState state;s26iu_save(&state);u32 t=0,f=0;s26iu.genTex(1,&t);s26iu.genFbo(1,&f);s26iu.active(0x84c0);s26iu_texture(t,0x8058,512,512,0x1908,0);s26iu.bindFbo(0x8ca9,f);s26iu.attachTex(0x8ca9,0x8ce0,0x0de1,t,0);s26iu.drawBuffer(0x8ce0);
 s26iu.bindFbo(0x8ca8,target);s26iu.readBuffer(0x8ce0);s26iu.blit(0,0,w,h,0,0,512,512,0x4000,0x2601);
 s26iu.bindFbo(0x8ca8,f);s26iu.readBuffer(0x8ce0);
 static u8 px[512*512*4];i32 pack=0,align=0,row=0,skipR=0,skipP=0;
 ext_glGetIntegerv(0x88ed,&pack);ext_glGetIntegerv(0x0d05,&align);ext_glGetIntegerv(0x0d02,&row);ext_glGetIntegerv(0x0d03,&skipR);ext_glGetIntegerv(0x0d04,&skipP);
 s26iu.bindBuffer(0x88eb,0);s26iu.pixelStore(0x0d05,1);s26iu.pixelStore(0x0d02,0);s26iu.pixelStore(0x0d03,0);s26iu.pixelStore(0x0d04,0);
 void (__attribute__((ms_abi)) *read)(i32,i32,i32,i32,u32,u32,void*)=(void*)ext_GetProcAddress(ext_GetModuleHandleA("opengl32.dll"),"glReadPixels");if(read)read(0,0,512,512,0x1908,0x1401,px);
 char name[]="iu_eye_0_0.rgba";name[7]='0'+m;name[9]='0'+eye;void* file=ext_fopen(name,"wb");if(file){ext_fwrite(px,1,sizeof(px),file);ext_fclose(file);}
 s26iu.bindBuffer(0x88eb,pack);s26iu.pixelStore(0x0d05,align);s26iu.pixelStore(0x0d02,row);s26iu.pixelStore(0x0d03,skipR);s26iu.pixelStore(0x0d04,skipP);
 s26iu_restore(&state);s26iu.delTex(1,&t);s26iu.delFbo(1,&f);
 ext_Log(">>> IU_EYE phase %d eye %d %dx%d SMAA requested %d ready %d armed %d",m,eye,w,h,g_s26iuEnabled,g_s26iuReady,g_s26iuArmed);
}
