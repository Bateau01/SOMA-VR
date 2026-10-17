/* Desktop-only binocular composition. Input eye textures are read-only.
   Align projection tangents at infinity; preserve left-eye near-field dominance.
   This is a spectator approximation, not a depth-correct third camera. */
static const char s26hq_vs[]="#version 330 core\nout vec2 uv;void main(){vec2 p=vec2((gl_VertexID<<1)&2,gl_VertexID&2);uv=p;gl_Position=vec4(p*2.-1.,0,1);}";
static const char s26hq_fs[]="#version 330 core\nin vec2 uv;out vec4 color;uniform sampler2D eyeL,eyeR;uniform int singleEye;uniform vec4 boundsL,boundsR,viewBox;\n"
"void main(){vec2 t=mix(viewBox.xy,viewBox.zw,uv);vec2 l=(t-boundsL.xy)/(boundsL.zw-boundsL.xy);vec2 r=(t-boundsR.xy)/(boundsR.zw-boundsR.xy);"
"if(singleEye!=0){color=vec4(texture(eyeL,clamp(l,vec2(0),vec2(1))).rgb,1);return;}"
"float lo=max(boundsL.x,boundsR.x),hi=min(boundsL.z,boundsR.z);float a=smoothstep(mix(lo,hi,.80),mix(lo,hi,.94),t.x);"
"if(l.x<0.||l.x>1.)a=1.;if(r.x<0.||r.x>1.)a=0.;"
"color=vec4(mix(texture(eyeL,clamp(l,vec2(0),vec2(1))).rgb,texture(eyeR,clamp(r,vec2(0),vec2(1))).rgb,a),1.);}";
static i32 s26hq_box(const float l[4],const float r[4],i32 w,i32 h,float box[4]){
    if(w<1||h<1)return 0;
    for(i32 k=0;k<4;k++)if(!(l[k]>-100&&l[k]<100&&r[k]>-100&&r[k]<100))return 0;
    if(l[2]<=l[0]||r[2]<=r[0]||l[3]<=l[1]||r[3]<=r[1])return 0;
    float left=l[0]<r[0]?l[0]:r[0],right=l[2]>r[2]?l[2]:r[2];
    float bottom=l[1]>r[1]?l[1]:r[1],top=l[3]<r[3]?l[3]:r[3];
    float overlap=(l[2]<r[2]?l[2]:r[2])-(l[0]>r[0]?l[0]:r[0]);
    if(top-bottom<.01f||overlap<.01f)return 0;
    float width=right-left,height=top-bottom,aspect=(float)w/h;
    if(width/height>aspect)width=height*aspect;else height=width/aspect;
    float cx=(left+right)*.5f,cy=(bottom+top)*.5f;
    box[0]=cx-width*.5f;box[1]=cy-height*.5f;box[2]=cx+width*.5f;box[3]=cy+height*.5f;return 1;
}
typedef void (__attribute__((ms_abi)) *HQGen)(i32,u32*);
typedef void (__attribute__((ms_abi)) *HQBindSampler)(u32,u32);
typedef void (__attribute__((ms_abi)) *HQSamplerParam)(u32,u32,i32);
typedef void (__attribute__((ms_abi)) *HQViewport)(i32,i32,i32,i32);
typedef void (__attribute__((ms_abi)) *HQPolygon)(u32,u32);
typedef void* (__attribute__((ms_abi)) *HQContext)(void);
static struct {
 S26CreateShader shader;S26ShaderSource source;S26ShaderOp compile,deleteShader,link,deleteProgram;
 S26ShaderStatus shaderStatus,programStatus;S26CreateProgram program;S26AttachShader attach;
 S26UniformLocation location;PFN_Uniform1iH9 u1;PFN_Uniform4fH10 u4;
 HQGen genVao,genSampler;PFN_BindVertexArrayH9 bindVao;PFN_UseProgramH9 use;
 PFN_ActiveTextureH10 active;HQBindSampler bindSampler;HQSamplerParam samplerParam;
 HQViewport viewport;HQPolygon polygon;u32 prog,vao,sampler;i32 loc[6],tried;void* context;
} s26hq;
static i32 s26hq_init(void){
 void* gl=ext_GetModuleHandleA("opengl32.dll");if(!gl)return 0;
 HQContext current=(HQContext)ext_GetProcAddress(gl,"wglGetCurrentContext");void* ctx=current?current():0;if(!ctx)return 0;
 if(s26hq.context!=ctx){zero_bytes(&s26hq,sizeof(s26hq));s26hq.context=ctx;}
 if(s26hq.tried)return s26hq.prog!=0;s26hq.tried=1;
 PFN_H5750A_WglGetProcAddress wg=(PFN_H5750A_WglGetProcAddress)ext_GetProcAddress(gl,"wglGetProcAddress");
#define HQ(field,type,name) s26hq.field=(type)s26_gl_proc(gl,wg,name);if(!s26hq.field)return 0
 HQ(shader,S26CreateShader,"glCreateShader");HQ(source,S26ShaderSource,"glShaderSource");HQ(compile,S26ShaderOp,"glCompileShader");HQ(deleteShader,S26ShaderOp,"glDeleteShader");
 HQ(link,S26ShaderOp,"glLinkProgram");HQ(deleteProgram,S26ShaderOp,"glDeleteProgram");HQ(shaderStatus,S26ShaderStatus,"glGetShaderiv");HQ(programStatus,S26ShaderStatus,"glGetProgramiv");
 HQ(program,S26CreateProgram,"glCreateProgram");HQ(attach,S26AttachShader,"glAttachShader");HQ(location,S26UniformLocation,"glGetUniformLocation");
 HQ(u1,PFN_Uniform1iH9,"glUniform1i");HQ(u4,PFN_Uniform4fH10,"glUniform4f");HQ(genVao,HQGen,"glGenVertexArrays");HQ(bindVao,PFN_BindVertexArrayH9,"glBindVertexArray");HQ(use,PFN_UseProgramH9,"glUseProgram");
 HQ(active,PFN_ActiveTextureH10,"glActiveTexture");HQ(genSampler,HQGen,"glGenSamplers");HQ(bindSampler,HQBindSampler,"glBindSampler");HQ(samplerParam,HQSamplerParam,"glSamplerParameteri");HQ(viewport,HQViewport,"glViewport");HQ(polygon,HQPolygon,"glPolygonMode");
#undef HQ
 u32 shaders[2]={s26hq.shader(0x8b31),s26hq.shader(0x8b30)};i32 ok=0;
 if(!shaders[0]||!shaders[1])goto fail;
 const char* vs=s26hq_vs;const char* fs=s26hq_fs;
 s26hq.source(shaders[0],1,&vs,0);s26hq.source(shaders[1],1,&fs,0);
 for(i32 k=0;k<2;k++){s26hq.compile(shaders[k]);s26hq.shaderStatus(shaders[k],0x8b81,&ok);if(!ok)goto fail;}
 s26hq.prog=s26hq.program();if(!s26hq.prog)goto fail;
 for(i32 k=0;k<2;k++)s26hq.attach(s26hq.prog,shaders[k]);
 s26hq.link(s26hq.prog);s26hq.programStatus(s26hq.prog,0x8b82,&ok);if(!ok)goto fail;
 s26hq.loc[0]=s26hq.location(s26hq.prog,"eyeL");
 s26hq.loc[1]=s26hq.location(s26hq.prog,"eyeR");
 s26hq.loc[2]=s26hq.location(s26hq.prog,"boundsL");
 s26hq.loc[3]=s26hq.location(s26hq.prog,"boundsR");
 s26hq.loc[4]=s26hq.location(s26hq.prog,"viewBox");
 s26hq.loc[5]=s26hq.location(s26hq.prog,"singleEye");
 for(i32 k=0;k<6;k++)if(s26hq.loc[k]<0)goto fail;
 s26hq.genVao(1,&s26hq.vao);s26hq.genSampler(1,&s26hq.sampler);if(!s26hq.vao||!s26hq.sampler)goto fail;
 s26hq.samplerParam(s26hq.sampler,0x2801,0x2601);s26hq.samplerParam(s26hq.sampler,0x2800,0x2601);
 s26hq.samplerParam(s26hq.sampler,0x2802,0x812f);s26hq.samplerParam(s26hq.sampler,0x2803,0x812f);
 for(i32 k=0;k<2;k++)s26hq.deleteShader(shaders[k]);
 ext_Log(">>> S26HQ COMBINED MIRROR READY: desktop-only projection-aligned left-dominant blend; eye textures read-only");return 1;
fail:
 for(i32 k=0;k<2;k++)if(shaders[k])s26hq.deleteShader(shaders[k]);
 if(s26hq.prog)s26hq.deleteProgram(s26hq.prog);s26hq.prog=0;
 ext_Log(">>> S26HQ COMBINED MIRROR unavailable; preserving full left-eye fallback");return 0;
}
/* Caller saves compatibility GL attributes and default framebuffer ownership. */
static void s26hq_draw(const float l[4],const float r[4],const float box[4],const i32 rect[4],i32 combined){
 i32 program=0,vao=0,active=0,tex[2],sampler[2];
 ext_glGetIntegerv(0x8b8d,&program);ext_glGetIntegerv(0x85b5,&vao);ext_glGetIntegerv(0x84e0,&active);
 for(i32 k=0;k<2;k++){s26hq.active(0x84c0+k);ext_glGetIntegerv(0x8069,&tex[k]);ext_glGetIntegerv(0x8919,&sampler[k]);
     ext_glBindTexture(0x0de1,g_h5750yResolveTex[k]);s26hq.bindSampler(k,s26hq.sampler);}
 const u32 caps[]={0x0b71,0x0b44,0x0c11,0x0b90,0x0be2,0x0bc0,0x8db9,0x8c89,0x809e,0x80a0,0x8e51};
 u8 enabled[17];
 for(i32 k=0;k<11;k++){enabled[k]=ext_glIsEnabled(caps[k]);ext_glDisable(caps[k]);}
 for(i32 k=0;k<6;k++){enabled[11+k]=ext_glIsEnabled(0x3000+k);ext_glDisable(0x3000+k);}
 s26hq.polygon(0x0408,0x1b02);s26hq.viewport(rect[0],rect[1],rect[2]-rect[0],rect[3]-rect[1]);
 s26hq.use(s26hq.prog);s26hq.bindVao(s26hq.vao);s26hq.u1(s26hq.loc[0],0);s26hq.u1(s26hq.loc[1],1);s26hq.u1(s26hq.loc[5],!combined);
 const float* values[3]={l,r,box};for(i32 k=0;k<3;k++)s26hq.u4(s26hq.loc[k+2],values[k][0],values[k][1],values[k][2],values[k][3]);
 ext_glDrawArrays(0x0004,0,3);
 s26hq.bindVao(vao);s26hq.use(program);
 for(i32 k=0;k<2;k++){s26hq.active(0x84c0+k);ext_glBindTexture(0x0de1,tex[k]);s26hq.bindSampler(k,sampler[k]);}
 s26hq.active(active);
 for(i32 k=0;k<11;k++){if(enabled[k])ext_glEnable(caps[k]);else ext_glDisable(caps[k]);}
 for(i32 k=0;k<6;k++){if(enabled[11+k])ext_glEnable(0x3000+k);else ext_glDisable(0x3000+k);}
}
