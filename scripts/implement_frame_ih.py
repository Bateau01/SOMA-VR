from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'source/s26n.c';s=p.read_text()
def replace(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b,1)
replace('u8 __attribute__((ms_abi)) s6_h11_begin_wrapper(void* self);','''static u64 s26ih_now(void);
static void s26ih_event(u32,u32,u64,u64,const float*,const float*);
static void s26ih_hand(u32,const float*);
u8 __attribute__((ms_abi)) s6_h11_begin_wrapper(void* self);''')
replace('static void capture_calib(H9Calib* c){','#include "frame_timing_ih.inc"\nstatic void capture_calib(H9Calib* c){')
replace('static void h5755eq_call_original_drender(', '#include "frame_gpu_ih.inc"\nstatic void h5755eq_call_original_drender(')
replace('    if(o_h5750aRender)o_h5750aRender(a,b,c,d,e,f,g,h);','    u64 ih=s26ih_now();i32 gpu=s26ih_gpu_begin();\n    if(o_h5750aRender)o_h5750aRender(a,b,c,d,e,f,g,h);\n    s26ih_gpu_end(gpu);s26ih_event(2,g_h5750vPrimeWrapperActive,ih,s26ih_now(),0,0);')
replace('    u8 ret=ext_OrigBegin(self);','    s26ih_begin_capture();s26ih_flush();u64 ih=s26ih_now();\n    u8 ret=ext_OrigBegin(self);\n    s26ih_event(1,ret,ih,s26ih_now(),0,0);')
replace('    if(p)p(sess,eye,tex,srcW,srcH);','    u64 ih=s26ih_now();if(p)p(sess,eye,tex,srcW,srcH);s26ih_event(3,(u32)eye,ih,s26ih_now(),0,0);')
replace('    if(eye==1&&g_s26cqStageReady)s26cq_restore_desktop_menu();','    ih=s26ih_now();\n    if(eye==1&&g_s26cqStageReady)s26cq_restore_desktop_menu();')
replace('    else if(eye==1)s26fi_desktop_mirror();','    else if(eye==1)s26fi_desktop_mirror();\n    if(eye==1)s26ih_event(4,0,ih,s26ih_now(),0,0);')
# Time exactly the original EndFrame call, with unmodified args/result on every branch.
marker='static i32 __attribute__((ms_abi)) h5754d_xr_end_frame'
# helper must precede implementation containing orig calls, find function start by nearest static
idx=s.index('    PFN_H5754D_XrEndFrame orig=g_h5754dOrigEndFrame;')
fn=s.rfind('\nstatic ',0,idx)
helper='''\nstatic i32 s26ih_end_call(PFN_H5754D_XrEndFrame orig,Handle session,const XrFrameEndInfo* info){
    u64 t=s26ih_now();i32 result=orig(session,info);s26ih_event(5,(u32)result,t,s26ih_now(),0,0);return result;
}
'''
s=s[:fn]+helper+s[fn:]
s=s.replace('orig(session,in)','s26ih_end_call(orig,session,in)').replace('orig(session,&out)','s26ih_end_call(orig,session,&out)')
replace('        p_s26MeshMatrix(g_s26NativeMesh[h],hm);','        s26ih_hand((u32)h,M);p_s26MeshMatrix(g_s26NativeMesh[h],hm);')
replace('    p_s26MeshMatrix(mesh,hm);p_s26MeshReset(mesh);','    s26ih_hand((u32)h,M);p_s26MeshMatrix(mesh,hm);p_s26MeshReset(mesh);')
replace('    eg0=h5755eg_tick();o_h14NewtonUpdate(world,timestep);','    u64 ihNewton=s26ih_now();\n    eg0=h5755eg_tick();o_h14NewtonUpdate(world,timestep);s26ih_event(8,0,ihNewton,s26ih_now(),0,0);')
s=s.replace('1.0.9-S26IG','1.0.9-S26IH');p.write_text(s)
