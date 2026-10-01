from pathlib import Path
import subprocess,sys
r=Path(__file__).resolve().parents[1]
s=(r/"source/s26n.c").read_text(encoding="utf-8")
a=s.index("static i32 s26cq_copy_menu_backbuffer(");end=s.index("\n}",a)+2
h='#include <stdio.h>\n#include <stdlib.h>\ntypedef unsigned u32;typedef int i32;typedef unsigned char u8;\nstatic i32 rb=4,db=8,back=0x404,scissor=1,copies=0;\nstatic void bind(u32 t,u32 v){if(t==0x8ca8)rb=v;else if(t==0x8ca9)db=v;else abort();}\nstatic void blit(i32 a,i32 b,i32 c,i32 d,i32 e,i32 f,i32 g,i32 h,u32 mask,u32 filter){if(rb!=0||db!=77||back!=0x405||scissor||a||b||e||f||c!=3440||d!=1440||g!=2912||h!=3112||mask!=0x4000||filter!=0x2601)abort();copies++;}\nstatic void readbuf(u32 v){back=v;}\ntypedef void (*PFN_H5750V_BindFramebuffer)(u32,u32);\ntypedef void (*PFN_H5750V_BlitFramebuffer)(i32,i32,i32,i32,i32,i32,i32,i32,u32,u32);\nstatic PFN_H5750V_BindFramebuffer h5750v_bind_fbo(void){return bind;}\nstatic PFN_H5750V_BlitFramebuffer h5750v_blit(void){return blit;}\nstatic void h5750v_resolve_read_buffer(void){}\nstatic void (*p_h5750vReadBuffer)(u32)=readbuf;\nstatic void ext_glGetIntegerv(u32 p,i32*v){if(p==0x8caa)*v=rb;else if(p==0x8ca6)*v=db;else if(p==0xc02)*v=back;else abort();}\nstatic u8 ext_glIsEnabled(u32 p){return scissor;}\nstatic void ext_glDisable(u32 p){scissor=0;}\nstatic void ext_glEnable(u32 p){scissor=1;}\n'
b='\nint main(void){for(int s=0;s<2;s++){scissor=s;if(!s26cq_copy_menu_backbuffer(77,3440,1440,2912,3112))abort();if(rb!=4||db!=8||back!=0x404||scissor!=s)abort();}if(s26cq_copy_menu_backbuffer(0,3440,1440,2912,3112)||copies!=2)abort();puts("PASS: extracted blit copies whole image, disables scissor and restores read/draw framebuffer, read buffer and scissor states");}\n'
p=r/"build/menu_gl_state.c";p.write_text(h+s[a:end]+b)
subprocess.run([sys.argv[1],"cc",str(p),"-o",str(p.with_suffix(".exe"))],check=True)
subprocess.run([str(p.with_suffix(".exe"))],check=True)
