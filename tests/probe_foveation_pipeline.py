"""Exercise real NV VRS with fragment invocation counts; no game modification."""
from pathlib import Path
import ctypes as c,json
R=Path(__file__).resolve().parents[1]
s=c.WinDLL('D:/SteamLibrary/steamapps/common/SOMA/SDL2.dll')
s.SDL_Init.argtypes=[c.c_uint];assert s.SDL_Init(32)==0
s.SDL_GL_SetAttribute.argtypes=[c.c_int,c.c_int]
for k,v in [(17,4),(18,5),(21,2)]:assert s.SDL_GL_SetAttribute(k,v)==0
s.SDL_CreateWindow.argtypes=[c.c_char_p,c.c_int,c.c_int,c.c_int,c.c_int,c.c_uint];s.SDL_CreateWindow.restype=c.c_void_p
w=s.SDL_CreateWindow(b'VRS validation',0,0,64,64,2|8|16);assert w
s.SDL_GL_CreateContext.argtypes=[c.c_void_p];s.SDL_GL_CreateContext.restype=c.c_void_p
ctx=s.SDL_GL_CreateContext(w);assert ctx
s.SDL_GL_GetProcAddress.argtypes=[c.c_char_p];s.SDL_GL_GetProcAddress.restype=c.c_void_p
U=c.c_uint;I=c.c_int;P=c.c_void_p;F=c.c_float

def fn(name,result,*args):
 p=s.SDL_GL_GetProcAddress(name.encode());assert p,name
 return c.WINFUNCTYPE(result,*args)(p)
gen=fn('glGenTextures',None,I,c.POINTER(U));bind=fn('glBindTexture',None,U,U)
store=fn('glTexStorage2D',None,U,I,U,I,I);upload=fn('glTexSubImage2D',None,U,I,I,I,I,I,U,U,P)
fgen=fn('glGenFramebuffers',None,I,c.POINTER(U));fbind=fn('glBindFramebuffer',None,U,U)
attach=fn('glFramebufferTexture2D',None,U,U,U,U,I);status=fn('glCheckFramebufferStatus',U,U)
enable=fn('glEnable',None,U);disable=fn('glDisable',None,U);error=fn('glGetError',U)
ratebind=fn('glBindShadingRateImageNV',None,U);palette=fn('glShadingRateImagePaletteNV',None,U,U,I,c.POINTER(U))
create=fn('glCreateShader',U,U);source=fn('glShaderSource',None,U,I,c.POINTER(c.c_char_p),c.POINTER(I));compile_=fn('glCompileShader',None,U)
getshader=fn('glGetShaderiv',None,U,U,c.POINTER(I));shaderlog=fn('glGetShaderInfoLog',None,U,I,c.POINTER(I),P)
program=fn('glCreateProgram',U);attachshader=fn('glAttachShader',None,U,U);link=fn('glLinkProgram',None,U);use=fn('glUseProgram',None,U)

def shader(kind,text):
 sh=create(kind);src=c.c_char_p(text.encode());source(sh,1,c.byref(src),None);compile_(sh);ok=I();getshader(sh,0x8b81,c.byref(ok))
 if not ok.value:
  buf=c.create_string_buffer(4096);shaderlog(sh,4096,None,buf);raise RuntimeError(buf.value)
 return sh
pr=program()
attachshader(pr,shader(0x8b31,'#version 430 compatibility\nvoid main(){gl_Position=gl_Vertex;}'))
attachshader(pr,shader(0x8b30,'#version 430 compatibility\nlayout(std430,binding=0) buffer Counts {uint n;};\nout vec4 color;void main(){atomicAdd(n,1u);color=vec4(1,0,0,1);}'))
link(pr);use(pr)
tex=U();gen(1,c.byref(tex));bind(0xde1,tex);store(0xde1,1,0x8058,64,64)
fbo=U();fgen(1,c.byref(fbo));fbind(0x8d40,fbo);attach(0x8d40,0x8ce0,0xde1,tex,0);assert status(0x8d40)==0x8cd5
rt=U();gen(1,c.byref(rt));bind(0xde1,rt);store(0xde1,1,0x8232,4,4)
fn('glPixelStorei',None,U,I)(0xcf5,1)
palette(0,0,2,(U*2)(0x9565,0x9568));ratebind(rt)
bgen=fn('glGenBuffers',None,I,c.POINTER(U));bbind=fn('glBindBuffer',None,U,U);bdata=fn('glBufferData',None,U,c.c_ssize_t,P,U)
bbase=fn('glBindBufferBase',None,U,U,U);getdata=fn('glGetBufferSubData',None,U,c.c_ssize_t,c.c_ssize_t,P)
buf=U();bgen(1,c.byref(buf));bbind(0x90d2,buf);bbase(0x90d2,0,buf)
viewport=fn('glViewport',None,I,I,I,I);begin=fn('glBegin',None,U);vertex=fn('glVertex2f',None,F,F);end=fn('glEnd',None)
barrier=fn('glMemoryBarrier',None,U);finish=fn('glFinish',None)
viewport(0,0,64,64);disable(0xb71);disable(0xbe2)
results={}
for name,on,mask in [('disabled',False,[1]*16),('full_rate',True,[0]*16),('coarse',True,[1]*16),('left_focus',True,[0,0,1,1]*4),('right_focus',True,[1,1,0,0]*4),('disabled_again',False,[1]*16)]:
 bind(0xde1,rt);upload(0xde1,0,0,0,4,4,0x8d94,0x1401,(c.c_ubyte*16)(*mask))
 zero=U();bdata(0x90d2,4,c.byref(zero),0x88e8)
 (enable if on else disable)(0x9563)
 begin(4)
 for x,y in [(-1,-1),(3,-1),(-1,3)]:vertex(x,y)
 end();barrier(0x2000|0x200);finish();n=U();getdata(0x90d2,0,4,c.byref(n))
 err=error();assert not err,(name,hex(err));results[name]=n.value
assert results['disabled']==results['full_rate']==results['disabled_again']==4096,results
assert results['coarse']==1024,results
assert results['left_focus']==results['right_focus']==2560,results
(R/'build/foveation_pipeline.json').write_text(json.dumps({'passed':True,'fragment_invocations':results},indent=2))
print(json.dumps(results))
s.SDL_Quit()

