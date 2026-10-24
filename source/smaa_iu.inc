/* SMAA 1x HIGH, current resolved eye only. No tracking/physics/native ownership writes.
   OpenGL resources belong to one current context; context changes invalidate names.
   Caller supplies RGBA8 non-sRGB resolved image. Edge detection and blending use
   gamma-space values as supported by upstream (no extra gamma conversion). */
#include "smaa_shader_iu.inc"
#include "../third_party/smaa/Textures/AreaTex.h"
#include "../third_party/smaa/Textures/SearchTex.h"
static i32 g_s26iuEnabled,g_s26iuArmed,g_s26iuReady;
#define IU_FN(ret,name,args) ret (__attribute__((ms_abi)) *name) args
/* Function table deliberately independent of the hand renderer and DFR. */
static struct {
 void* ctx; i32 tried,w,h,vrs; u32 prog[3],tex[5],fbo[3],vao,sampler; i32 metric[3];
 IU_FN(void,genTex,(i32,u32*));IU_FN(void,delTex,(i32,const u32*));
 IU_FN(void,image,(u32,i32,i32,i32,i32,i32,u32,u32,const void*));
 IU_FN(void,param,(u32,u32,i32));IU_FN(void,genFbo,(i32,u32*));IU_FN(void,delFbo,(i32,const u32*));
 IU_FN(void,bindFbo,(u32,u32));IU_FN(void,attachTex,(u32,u32,u32,u32,i32));IU_FN(u32,checkFbo,(u32));
 IU_FN(u32,shader,(u32));IU_FN(void,source,(u32,i32,const char* const*,const i32*));
 IU_FN(void,compile,(u32));IU_FN(void,delShader,(u32));IU_FN(void,shaderStatus,(u32,u32,i32*));
 IU_FN(void,shaderLog,(u32,i32,i32*,char*));IU_FN(u32,program,(void));IU_FN(void,attach,(u32,u32));
 IU_FN(void,link,(u32));IU_FN(void,programStatus,(u32,u32,i32*));IU_FN(void,delProgram,(u32));
 IU_FN(void,use,(u32));IU_FN(i32,location,(u32,const char*));IU_FN(void,u1,(i32,i32));IU_FN(void,u4,(i32,float,float,float,float));
 IU_FN(void,genVao,(i32,u32*));IU_FN(void,bindVao,(u32));IU_FN(void,genSampler,(i32,u32*));
 IU_FN(void,bindSampler,(u32,u32));IU_FN(void,samplerParam,(u32,u32,i32));IU_FN(void,active,(u32));
 IU_FN(void,viewport,(i32,i32,i32,i32));IU_FN(void,polygon,(u32,u32));IU_FN(void,mask,(u8,u8,u8,u8));
 IU_FN(void,clearColor,(float,float,float,float));IU_FN(void,clear,(u32));IU_FN(void,push,(u32));IU_FN(void,pop,(void));
 IU_FN(void,drawBuffer,(u32));IU_FN(void,readBuffer,(u32));IU_FN(void,blit,(i32,i32,i32,i32,i32,i32,i32,i32,u32,u32));
 IU_FN(void,pixelStore,(u32,i32));IU_FN(void,bindBuffer,(u32,u32));IU_FN(const u8*,string,(u32));
} s26iu;
#undef IU_FN
static i32 s26iu_has_extension(const char* all,const char* wanted){
 if(!all)return 0;for(u32 i=0;all[i];){u32 j=0;while(wanted[j]&&all[i+j]==wanted[j])j++;
 if(!wanted[j]&&(!all[i+j]||all[i+j]==' '))return 1;while(all[i]&&all[i]!=' ')i++;if(all[i])i++;}return 0;
}
static i32 s26iu_api(void){
 void* gl=ext_GetModuleHandleA("opengl32.dll");if(!gl)return 0;
 void* (__attribute__((ms_abi)) *current)(void)=(void*)ext_GetProcAddress(gl,"wglGetCurrentContext");
 void* ctx=current?current():0;if(!ctx)return 0;
 if(s26iu.ctx!=ctx){zero_bytes(&s26iu,sizeof(s26iu));s26iu.ctx=ctx;g_s26iuReady=0;}
 if(s26iu.tried)return s26iu.tried==1;
 s26iu.tried=-1;
 PFN_H5750A_WglGetProcAddress wg=(void*)ext_GetProcAddress(gl,"wglGetProcAddress");
#define IU(field,name) s26iu.field=(void*)s26_gl_proc(gl,wg,name);if(!s26iu.field)return 0
 IU(genTex,"glGenTextures");IU(delTex,"glDeleteTextures");IU(image,"glTexImage2D");IU(param,"glTexParameteri");
 IU(genFbo,"glGenFramebuffers");IU(delFbo,"glDeleteFramebuffers");IU(bindFbo,"glBindFramebuffer");IU(attachTex,"glFramebufferTexture2D");IU(checkFbo,"glCheckFramebufferStatus");
 IU(shader,"glCreateShader");IU(source,"glShaderSource");IU(compile,"glCompileShader");IU(delShader,"glDeleteShader");IU(shaderStatus,"glGetShaderiv");IU(shaderLog,"glGetShaderInfoLog");
 IU(program,"glCreateProgram");IU(attach,"glAttachShader");IU(link,"glLinkProgram");IU(programStatus,"glGetProgramiv");IU(delProgram,"glDeleteProgram");IU(use,"glUseProgram");IU(location,"glGetUniformLocation");IU(u1,"glUniform1i");IU(u4,"glUniform4f");
 IU(genVao,"glGenVertexArrays");IU(bindVao,"glBindVertexArray");IU(genSampler,"glGenSamplers");IU(bindSampler,"glBindSampler");IU(samplerParam,"glSamplerParameteri");IU(active,"glActiveTexture");
 IU(viewport,"glViewport");IU(polygon,"glPolygonMode");IU(mask,"glColorMask");IU(clearColor,"glClearColor");IU(clear,"glClear");IU(push,"glPushAttrib");IU(pop,"glPopAttrib");
 IU(drawBuffer,"glDrawBuffer");IU(readBuffer,"glReadBuffer");IU(blit,"glBlitFramebuffer");IU(pixelStore,"glPixelStorei");IU(bindBuffer,"glBindBuffer");IU(string,"glGetString");
#undef IU
 s26iu.vrs=s26iu_has_extension((const char*)s26iu.string(0x1f03),"GL_NV_shading_rate_image");s26iu.tried=1;return 1;
}
typedef struct {i32 read,draw,readBuffer,drawBuffer,program,vao,active,tex[3],sampler[3],unpack,alignment,row,skipRows,skipPixels;u8 vrs,discard;} S26IUState;
static void s26iu_save(S26IUState* s){
 ext_glGetIntegerv(0x8caa,&s->read);ext_glGetIntegerv(0x8ca6,&s->draw);ext_glGetIntegerv(0x0c02,&s->readBuffer);ext_glGetIntegerv(0x0c01,&s->drawBuffer);
 ext_glGetIntegerv(0x8b8d,&s->program);ext_glGetIntegerv(0x85b5,&s->vao);ext_glGetIntegerv(0x84e0,&s->active);
 ext_glGetIntegerv(0x88ef,&s->unpack);ext_glGetIntegerv(0x0cf5,&s->alignment);ext_glGetIntegerv(0x0cf2,&s->row);ext_glGetIntegerv(0x0cf3,&s->skipRows);ext_glGetIntegerv(0x0cf4,&s->skipPixels);
 for(i32 k=0;k<3;k++){s26iu.active(0x84c0+k);ext_glGetIntegerv(0x8069,&s->tex[k]);ext_glGetIntegerv(0x8919,&s->sampler[k]);}
 s->discard=ext_glIsEnabled(0x8c89);s26iu.push(0x000fffff);s->vrs=s26iu.vrs?ext_glIsEnabled(0x9563):0;if(s->vrs)ext_glDisable(0x9563);
 const u32 caps[]={0x0b71,0x0b44,0x0c11,0x0b90,0x0be2,0x0bc0,0x8db9,0x8c89,0x809e,0x80a0,0x8e51,0x0bf2};
 for(i32 k=0;k<12;k++)ext_glDisable(caps[k]);for(i32 k=0;k<6;k++)ext_glDisable(0x3000+k);
 s26iu.polygon(0x0408,0x1b02);s26iu.mask(1,1,1,1);s26iu.bindBuffer(0x88ec,0);
 s26iu.pixelStore(0x0cf5,1);s26iu.pixelStore(0x0cf2,0);s26iu.pixelStore(0x0cf3,0);s26iu.pixelStore(0x0cf4,0);
}
static void s26iu_restore(const S26IUState* s){
 s26iu.bindFbo(0x8ca8,s->read);s26iu.bindFbo(0x8ca9,s->draw);s26iu.pop();
 s26iu.readBuffer(s->readBuffer);s26iu.drawBuffer(s->drawBuffer);
 s26iu.use(s->program);s26iu.bindVao(s->vao);
 for(i32 k=0;k<3;k++){s26iu.active(0x84c0+k);ext_glBindTexture(0x0de1,s->tex[k]);s26iu.bindSampler(k,s->sampler[k]);}s26iu.active(s->active);
 s26iu.bindBuffer(0x88ec,s->unpack);s26iu.pixelStore(0x0cf5,s->alignment);s26iu.pixelStore(0x0cf2,s->row);s26iu.pixelStore(0x0cf3,s->skipRows);s26iu.pixelStore(0x0cf4,s->skipPixels);
 if(s->discard)ext_glEnable(0x8c89);else ext_glDisable(0x8c89);
 if(s26iu.vrs){if(s->vrs)ext_glEnable(0x9563);else ext_glDisable(0x9563);}
}
static const char* s26iu_vsmain[3]={
 "out vec2 uv;out vec4 off[3];void main(){uv=vec2((gl_VertexID<<1)&2,gl_VertexID&2);gl_Position=vec4(uv*2.-1.,0,1);SMAAEdgeDetectionVS(uv,off);}",
 "out vec2 uv;out vec2 pix;out vec4 off[3];void main(){uv=vec2((gl_VertexID<<1)&2,gl_VertexID&2);gl_Position=vec4(uv*2.-1.,0,1);SMAABlendingWeightCalculationVS(uv,pix,off);}",
 "out vec2 uv;out vec4 off;void main(){uv=vec2((gl_VertexID<<1)&2,gl_VertexID&2);gl_Position=vec4(uv*2.-1.,0,1);SMAANeighborhoodBlendingVS(uv,off);}"
};
static const char* s26iu_psmain[3]={
 "in vec2 uv;in vec4 off[3];uniform sampler2D image0;out vec4 color;void main(){color=vec4(SMAALumaEdgeDetectionPS(uv,off,image0),0,0);}",
 "in vec2 uv;in vec2 pix;in vec4 off[3];uniform sampler2D image0,image1,image2;out vec4 color;void main(){color=SMAABlendingWeightCalculationPS(uv,pix,off,image0,image1,image2,vec4(0));}",
 "in vec2 uv;in vec4 off;uniform sampler2D image0,image1;out vec4 color;void main(){color=SMAANeighborhoodBlendingPS(uv,off,image0,image1);}"
};
static i32 s26iu_programs(void){
 if(s26iu.prog[0]&&s26iu.prog[1]&&s26iu.prog[2])return 1;
 for(i32 pass=0;pass<3;pass++){
  u32 shaders[2]={0,0};i32 ok=1;
  for(i32 k=0;k<2;k++){
   shaders[k]=s26iu.shader(k?0x8b30:0x8b31);
   const char* parts[]={k?"#version 330 compatibility\n#define SMAA_INCLUDE_VS 0\n#define SMAA_INCLUDE_PS 1\n":"#version 330 compatibility\n#define SMAA_INCLUDE_VS 1\n#define SMAA_INCLUDE_PS 0\n",
    "#define SMAA_GLSL_3 1\n#define SMAA_PRESET_HIGH 1\nuniform vec4 metrics;\n#define SMAA_RT_METRICS metrics\n",s26iu_shader,k?s26iu_psmain[pass]:s26iu_vsmain[pass]};
   s26iu.source(shaders[k],4,parts,0);s26iu.compile(shaders[k]);i32 compiled=0;s26iu.shaderStatus(shaders[k],0x8b81,&compiled);
   if(!compiled){char log[1024];i32 n=0;s26iu.shaderLog(shaders[k],1023,&n,log);log[n>=0&&n<1024?n:0]=0;ext_Log(">>> SMAA shader rejected: %s",log);ok=0;}
  }
  if(ok){s26iu.prog[pass]=s26iu.program();s26iu.attach(s26iu.prog[pass],shaders[0]);s26iu.attach(s26iu.prog[pass],shaders[1]);s26iu.link(s26iu.prog[pass]);s26iu.programStatus(s26iu.prog[pass],0x8b82,&ok);}
  for(i32 k=0;k<2;k++)if(shaders[k])s26iu.delShader(shaders[k]);
  if(!ok){for(i32 k=0;k<3;k++){if(s26iu.prog[k])s26iu.delProgram(s26iu.prog[k]);s26iu.prog[k]=0;}s26iu.tried=-1;return 0;}
  s26iu.metric[pass]=s26iu.location(s26iu.prog[pass],"metrics");s26iu.use(s26iu.prog[pass]);
  s26iu.u1(s26iu.location(s26iu.prog[pass],"image0"),0);s26iu.u1(s26iu.location(s26iu.prog[pass],"image1"),1);s26iu.u1(s26iu.location(s26iu.prog[pass],"image2"),2);
 }
 s26iu.genVao(1,&s26iu.vao);s26iu.genSampler(1,&s26iu.sampler);
 s26iu.samplerParam(s26iu.sampler,0x2801,0x2601);s26iu.samplerParam(s26iu.sampler,0x2800,0x2601);s26iu.samplerParam(s26iu.sampler,0x2802,0x812f);s26iu.samplerParam(s26iu.sampler,0x2803,0x812f);
 return s26iu.vao&&s26iu.sampler;
}
static void s26iu_texture(u32 id,i32 format,i32 w,i32 h,u32 channels,const void* data){
 ext_glBindTexture(0x0de1,id);s26iu.image(0x0de1,0,format,w,h,0,channels,0x1401,data);
 s26iu.param(0x0de1,0x2801,0x2601);s26iu.param(0x0de1,0x2800,0x2601);s26iu.param(0x0de1,0x2802,0x812f);s26iu.param(0x0de1,0x2803,0x812f);
}
static i32 s26iu_targets(i32 w,i32 h){
 if(s26iu.w==w&&s26iu.h==h&&s26iu.fbo[2])return 1;
 i32 max=0;ext_glGetIntegerv(0x0d33,&max);if(w<1||h<1||w>max||h>max)return 0;
 s26iu.delTex(5,s26iu.tex);s26iu.delFbo(3,s26iu.fbo);zero_bytes(s26iu.tex,sizeof(s26iu.tex));zero_bytes(s26iu.fbo,sizeof(s26iu.fbo));s26iu.w=s26iu.h=0;
 s26iu.genTex(5,s26iu.tex);s26iu.genFbo(3,s26iu.fbo);s26iu.active(0x84c0);
 for(i32 k=0;k<3;k++){
  s26iu_texture(s26iu.tex[k],0x8058,w,h,0x1908,0);s26iu.bindFbo(0x8d40,s26iu.fbo[k]);s26iu.attachTex(0x8d40,0x8ce0,0x0de1,s26iu.tex[k],0);s26iu.drawBuffer(0x8ce0);
  if(s26iu.checkFbo(0x8d40)!=0x8cd5)return 0;
 }
 s26iu_texture(s26iu.tex[3],0x822b,AREATEX_WIDTH,AREATEX_HEIGHT,0x8227,areaTexBytes);
 s26iu_texture(s26iu.tex[4],0x8229,SEARCHTEX_WIDTH,SEARCHTEX_HEIGHT,0x1903,searchTexBytes);
 s26iu.w=w;s26iu.h=h;ext_Log(">>> SMAA 1x HIGH ready: %dx%d per eye; no temporal history",w,h);return 1;
}
/* Returns 1 only after output is committed; source never sampled while attached for writing. */
static i32 s26iu_process(u32 input,u32 output,i32 w,i32 h,i32 apply){
 if(!s26iu_api()){g_s26iuReady=0;return 0;}S26IUState state;s26iu_save(&state);
 i32 ok=s26iu_programs()&&s26iu_targets(w,h);g_s26iuReady=ok;
 if(ok&&apply){
  s26iu.viewport(0,0,w,h);s26iu.bindVao(s26iu.vao);
  for(i32 pass=0;pass<3;pass++){
   u32 textures[3]={pass==1?s26iu.tex[0]:input,pass==1?s26iu.tex[3]:s26iu.tex[1],s26iu.tex[4]};
   for(i32 k=0;k<3;k++){s26iu.active(0x84c0+k);ext_glBindTexture(0x0de1,textures[k]);s26iu.bindSampler(k,s26iu.sampler);}
   s26iu.bindFbo(0x8ca9,s26iu.fbo[pass]);s26iu.drawBuffer(0x8ce0);s26iu.clearColor(0,0,0,0);s26iu.clear(0x4000);
   s26iu.use(s26iu.prog[pass]);s26iu.u4(s26iu.metric[pass],1.f/w,1.f/h,(float)w,(float)h);ext_glDrawArrays(4,0,3);
  }
  s26iu.bindFbo(0x8ca8,s26iu.fbo[2]);s26iu.readBuffer(0x8ce0);s26iu.bindFbo(0x8ca9,output);s26iu.drawBuffer(0x8ce0);s26iu.blit(0,0,w,h,0,0,w,h,0x4000,0x2600);
 }
 s26iu_restore(&state);return ok&&apply;
}
static i32 s26iu_should_process(i32 enabled,i32 eye,i32 gameplay,i32 menu,i32 pause,i32 transition,i32 resolved){
 return enabled&&eye>=0&&eye<2&&gameplay&&!menu&&!pause&&!transition&&resolved;
}
