typedef u32 (__attribute__((ms_abi)) *S26CreateShader)(u32);
typedef void (__attribute__((ms_abi)) *S26ShaderSource)(u32,i32,const char* const*,const i32*);
typedef void (__attribute__((ms_abi)) *S26ShaderOp)(u32);
typedef void (__attribute__((ms_abi)) *S26ShaderStatus)(u32,u32,i32*);
typedef u32 (__attribute__((ms_abi)) *S26CreateProgram)(void);
typedef void (__attribute__((ms_abi)) *S26AttachShader)(u32,u32);
typedef i32 (__attribute__((ms_abi)) *S26UniformLocation)(u32,const char*);
typedef void (__attribute__((ms_abi)) *S26Uniform2f)(i32,float,float);
typedef void (__attribute__((ms_abi)) *S26BlendFunc)(u32,u32,u32,u32);
typedef void (__attribute__((ms_abi)) *S26BlendEquation)(u32,u32);
typedef void (__attribute__((ms_abi)) *S26GetBoolean)(u32,u8*);
typedef void (__attribute__((ms_abi)) *S26ColorMask)(u8,u8,u8,u8);
static S26CreateShader p_s26CreateShader;static S26ShaderSource p_s26ShaderSource;
static S26ShaderOp p_s26CompileShader,p_s26DeleteShader,p_s26LinkProgram,p_s26DeleteProgram;
static S26ShaderStatus p_s26GetShaderiv,p_s26GetProgramiv;
static S26CreateProgram p_s26CreateProgram;static S26AttachShader p_s26AttachShader;
static S26UniformLocation p_s26UniformLocation;static S26Uniform2f p_s26Uniform2f;
static S26BlendFunc p_s26BlendFunc;static S26BlendEquation p_s26BlendEquation;
static S26GetBoolean p_s26GetBoolean;static S26ColorMask p_s26ColorMask;
static u32 g_s26VignetteProgram,g_s26VignetteVao,g_s26VignetteFrame=0xffffffffu;
static i32 g_s26VignetteTried,g_s26VignetteUniform=-1;
static volatile u32 g_s26VignetteMode;
static float g_s26VignetteAmount;static i64 g_s26VignetteTime;
static void* s26_gl_proc(void* ogl,PFN_H5750A_WglGetProcAddress wg,const char* name){
    void* p=wg?wg(name):0;if((u64)p<=3u||(u64)p==~(u64)0)p=ext_GetProcAddress(ogl,name);return p;
}
static i32 s26_vignette_init(void){
    if(g_s26VignetteTried)return g_s26VignetteProgram!=0;g_s26VignetteTried=1;
    void* ogl=ext_GetModuleHandleA("opengl32.dll");if(!ogl)return 0;
    PFN_H5750A_WglGetProcAddress wg=(PFN_H5750A_WglGetProcAddress)ext_GetProcAddress(ogl,"wglGetProcAddress");
#define S26_GL(dst,type,name) dst=(type)s26_gl_proc(ogl,wg,name);if(!dst)return 0
    S26_GL(p_s26CreateShader,S26CreateShader,"glCreateShader");S26_GL(p_s26ShaderSource,S26ShaderSource,"glShaderSource");
    S26_GL(p_s26CompileShader,S26ShaderOp,"glCompileShader");S26_GL(p_s26DeleteShader,S26ShaderOp,"glDeleteShader");
    S26_GL(p_s26GetShaderiv,S26ShaderStatus,"glGetShaderiv");S26_GL(p_s26GetProgramiv,S26ShaderStatus,"glGetProgramiv");
    S26_GL(p_s26CreateProgram,S26CreateProgram,"glCreateProgram");S26_GL(p_s26AttachShader,S26AttachShader,"glAttachShader");
    S26_GL(p_s26LinkProgram,S26ShaderOp,"glLinkProgram");S26_GL(p_s26DeleteProgram,S26ShaderOp,"glDeleteProgram");
    S26_GL(p_s26UniformLocation,S26UniformLocation,"glGetUniformLocation");S26_GL(p_s26Uniform2f,S26Uniform2f,"glUniform2f");
    S26_GL(p_s26BlendFunc,S26BlendFunc,"glBlendFuncSeparate");S26_GL(p_s26BlendEquation,S26BlendEquation,"glBlendEquationSeparate");
    S26_GL(p_s26GetBoolean,S26GetBoolean,"glGetBooleanv");S26_GL(p_s26ColorMask,S26ColorMask,"glColorMask");
#undef S26_GL
    if(!p2_gen_vaos()||!p2_bind_vao()||!p2_use_program())return 0;
    const char* vs="#version 330 core\n out vec2 uv; void main(){ const vec2 p[3]=vec2[3](vec2(-1,-1),vec2(3,-1),vec2(-1,3)); uv=p[gl_VertexID]; gl_Position=vec4(uv,0,1); }";
    const char* fs="#version 330 core\n in vec2 uv; uniform vec2 comfort; out vec4 color; void main(){ color=vec4(0,0,0,smoothstep(comfort.x,1.0,length(uv))*comfort.y); }";
    u32 shaders[2]={p_s26CreateShader(0x8b31u),p_s26CreateShader(0x8b30u)};i32 ok=0;
    if(!shaders[0]||!shaders[1])goto fail;
    p_s26ShaderSource(shaders[0],1,&vs,0);p_s26ShaderSource(shaders[1],1,&fs,0);
    for(i32 i=0;i<2;++i){p_s26CompileShader(shaders[i]);p_s26GetShaderiv(shaders[i],0x8b81u,&ok);if(!ok)goto fail;}
    g_s26VignetteProgram=p_s26CreateProgram();if(!g_s26VignetteProgram)goto fail;
    for(i32 i=0;i<2;++i)p_s26AttachShader(g_s26VignetteProgram,shaders[i]);
    p_s26LinkProgram(g_s26VignetteProgram);p_s26GetProgramiv(g_s26VignetteProgram,0x8b82u,&ok);if(!ok)goto fail;
    g_s26VignetteUniform=p_s26UniformLocation(g_s26VignetteProgram,"comfort");if(g_s26VignetteUniform<0)goto fail;
    p2_gen_vaos()(1,&g_s26VignetteVao);if(!g_s26VignetteVao)goto fail;
    for(i32 i=0;i<2;++i)p_s26DeleteShader(shaders[i]);
    ext_Log(">>> S26F VIGNETTE READY: per-eye radial comfort mask; movement fade; native GUI excluded");return 1;
fail:
    for(i32 i=0;i<2;++i)if(shaders[i])p_s26DeleteShader(shaders[i]);
    if(g_s26VignetteProgram)p_s26DeleteProgram(g_s26VignetteProgram);g_s26VignetteProgram=0;
    ext_Log(">>> S26F VIGNETTE UNAVAILABLE: shader/program initialization failed; scene remains unchanged");return 0;
}
static float s26_vignette_fade(float amount,float goal,float dt){
    if(!(dt>0.0f))return amount;if(dt>0.1f)dt=0.1f;
    float step=dt*(goal>amount?6.0f:3.0f);
    if(goal>amount){amount+=step;if(amount>goal)amount=goal;}
    else{amount-=step;if(amount<goal)amount=goal;}
    return amount;
}
static void s26_draw_vignette(void){
    if(!g_s26VignetteMode||!p2_xr_on()||!p2_xr_running()||g_h576mScriptRuntimePublished!=1||
       g_s26CutsceneHandsHidden||g_h576bfMapTransitionActive||h5754h_pause_active()){
        g_s26VignetteAmount=0;g_s26VignetteTime=0;return;
    }
    if(h5755bq_should_suppress_aux_hand(0))return;
    if(g_s26VignetteFrame!=g_frameCounter){
        g_s26VignetteFrame=g_frameCounter;u8* xr=(u8*)p2_xr_obj();i64 now=xr?*(i64*)(xr+0xe8):0;
        float dt=g_s26VignetteTime&&now>g_s26VignetteTime?(float)((double)(now-g_s26VignetteTime)*1e-9):0.01f;
        g_s26VignetteTime=now;
        i32 move=(g_lastStickXActive[0]&&h9_abs(g_lastStickX[0])>.18f)||(g_lastStickYActive[0]&&h9_abs(g_lastStickY[0])>.18f);
        i32 turn=g_s26TurnMode==0&&g_lastStickXActive[1]&&h9_abs(g_lastStickX[1])>.18f;
        float goal=(g_s26VignetteMode==3||move||turn)?1.0f:0.0f;
        g_s26VignetteAmount=s26_vignette_fade(g_s26VignetteAmount,goal,dt);
    }
    if(g_s26VignetteAmount<=0.001f||!s26_vignette_init())return;
    i32 program=0,vao=0,srcRGB=0,dstRGB=0,srcA=0,dstA=0,eqRGB=0,eqA=0;
    ext_glGetIntegerv(0x8b8du,&program);ext_glGetIntegerv(0x85b5u,&vao);
    ext_glGetIntegerv(0x80c9u,&srcRGB);ext_glGetIntegerv(0x80c8u,&dstRGB);ext_glGetIntegerv(0x80cbu,&srcA);ext_glGetIntegerv(0x80cau,&dstA);
    ext_glGetIntegerv(0x8009u,&eqRGB);ext_glGetIntegerv(0x883du,&eqA);
    const u32 caps[5]={0x0b71u,0x0b44u,0x0c11u,0x0b90u,0x0be2u};u8 enabled[5],mask[4];
    for(i32 i=0;i<5;++i){enabled[i]=ext_glIsEnabled(caps[i]);if(i<4)ext_glDisable(caps[i]);}
    p_s26GetBoolean(0x0c23u,mask);p_s26ColorMask(1,1,1,1);ext_glEnable(0x0be2u);
    p_s26BlendFunc(0x0302u,0x0303u,0,1);p_s26BlendEquation(0x8006u,0x8006u);
    p2_use_program()(g_s26VignetteProgram);p2_bind_vao()(g_s26VignetteVao);
    p_s26Uniform2f(g_s26VignetteUniform,g_s26VignetteMode==1?.82f:.63f,g_s26VignetteAmount);
    ext_glDrawArrays(0x0004u,0,3);
    p2_bind_vao()((u32)vao);p2_use_program()((u32)program);p_s26BlendFunc(srcRGB,dstRGB,srcA,dstA);p_s26BlendEquation(eqRGB,eqA);p_s26ColorMask(mask[0],mask[1],mask[2],mask[3]);
    for(i32 i=0;i<5;++i){if(enabled[i])ext_glEnable(caps[i]);else ext_glDisable(caps[i]);}
}
