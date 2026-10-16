from pathlib import Path
import ctypes as c,re,json
from ctypes import wintypes as w
R=Path(__file__).resolve().parents[1]
u=c.WinDLL('user32');g=c.WinDLL('gdi32');gl=c.WinDLL('opengl32')
u.CreateWindowExW.argtypes=[w.DWORD,w.LPCWSTR,w.LPCWSTR,w.DWORD,c.c_int,c.c_int,c.c_int,c.c_int,w.HWND,w.HMENU,w.HINSTANCE,c.c_void_p];u.CreateWindowExW.restype=w.HWND
u.GetDC.argtypes=[w.HWND];u.GetDC.restype=w.HDC
hw=u.CreateWindowExW(0,'STATIC','Shader test',0,0,0,16,16,None,None,None,None);assert hw
hd=u.GetDC(hw)
class PFD(c.Structure):
 _fields_=[('size',w.WORD),('version',w.WORD),('flags',w.DWORD),('pixelType',c.c_ubyte),('color',c.c_ubyte),('red',c.c_ubyte),('rs',c.c_ubyte),('green',c.c_ubyte),('gs',c.c_ubyte),('blue',c.c_ubyte),('bs',c.c_ubyte),('alpha',c.c_ubyte),('as_',c.c_ubyte),('accum',c.c_ubyte),('ar',c.c_ubyte),('ag',c.c_ubyte),('ab',c.c_ubyte),('aa',c.c_ubyte),('depth',c.c_ubyte),('stencil',c.c_ubyte),('aux',c.c_ubyte),('layer',c.c_ubyte),('reserved',c.c_ubyte),('lm',w.DWORD),('vm',w.DWORD),('dm',w.DWORD)]
p=PFD();p.size=c.sizeof(p);p.version=1;p.flags=0x24;p.color=24
for name,rest,args in [('ChoosePixelFormat',c.c_int,[w.HDC,c.POINTER(PFD)]),('SetPixelFormat',w.BOOL,[w.HDC,c.c_int,c.POINTER(PFD)])]:
 fn=getattr(g,name);fn.restype=rest;fn.argtypes=args
assert g.SetPixelFormat(hd,g.ChoosePixelFormat(hd,c.byref(p)),c.byref(p))
gl.wglCreateContext.argtypes=[w.HDC];gl.wglCreateContext.restype=c.c_void_p;ctx=gl.wglCreateContext(hd);assert ctx
gl.wglMakeCurrent.argtypes=[w.HDC,c.c_void_p];assert gl.wglMakeCurrent(hd,ctx)
gl.wglGetProcAddress.argtypes=[c.c_char_p];gl.wglGetProcAddress.restype=c.c_void_p
def api(n,res,*args):
 addr=gl.wglGetProcAddress(n.encode());assert addr and addr not in (1,2,3,-1);return c.WINFUNCTYPE(res,*args)(addr)
create=api('glCreateShader',c.c_uint,c.c_uint);source=api('glShaderSource',None,c.c_uint,c.c_int,c.POINTER(c.c_char_p),c.c_void_p);compile=api('glCompileShader',None,c.c_uint);status=api('glGetShaderiv',None,c.c_uint,c.c_uint,c.POINTER(c.c_int));log=api('glGetShaderInfoLog',None,c.c_uint,c.c_int,c.c_void_p,c.c_char_p)
s=(R/'runtime/core/shaders/hpsl/game_edge_glow.hpsl').read_text();body=s[s.index('{',s.index('void main(')):]
body=body.replace('cVector4f','vec4').replace('sample(','texture2D(').replace('out_vColor','gl_FragColor')
prefix='''#version 120
uniform vec4 aColor;uniform float afAlpha,afLightLevel,afLightLimit,afEdgeThickness;uniform sampler2D aDiffuseMap;
const vec3 px_vNormal=vec3(1,0,0);const vec3 px_vVertexPos=vec3(0,0,-1);const vec4 px_vTexCoord0=vec4(0,0,0,0);
void main()
'''
shader=create(0x8b30);src=c.c_char_p((prefix+body).encode());source(shader,1,c.byref(src),None);compile(shader);ok=c.c_int();status(shader,0x8b81,c.byref(ok));buf=c.create_string_buffer(8192);log(shader,len(buf),None,buf);assert ok.value,buf.value

# Render the production fragment to a texture using an opaque black input.
# This verifies fragment behavior, not SOMA's native depth/queue integration.
vertex=create(0x8b31);vs=c.c_char_p(b'#version 120\nvoid main(){gl_Position=gl_Vertex;}');source(vertex,1,c.byref(vs),None);compile(vertex)
make_program=api('glCreateProgram',c.c_uint);attach=api('glAttachShader',None,c.c_uint,c.c_uint);link=api('glLinkProgram',None,c.c_uint);use=api('glUseProgram',None,c.c_uint)
program=make_program();attach(program,vertex);attach(program,shader);link(program);use(program)
loc=api('glGetUniformLocation',c.c_int,c.c_uint,c.c_char_p);uniform4=api('glUniform4f',None,c.c_int,c.c_float,c.c_float,c.c_float,c.c_float);uniform1=api('glUniform1f',None,c.c_int,c.c_float)
for name,value in [('afAlpha',.45),('afLightLevel',0),('afLightLimit',100),('afEdgeThickness',.30)]:uniform1(loc(program,name.encode()),value)
gen=api('glGenFramebuffers',None,c.c_int,c.POINTER(c.c_uint));bind=api('glBindFramebuffer',None,c.c_uint,c.c_uint);fbo=c.c_uint();gen(1,c.byref(fbo));bind(0x8d40,fbo)
gl.glGenTextures.argtypes=[c.c_int,c.POINTER(c.c_uint)];gl.glBindTexture.argtypes=[c.c_uint,c.c_uint];gl.glTexImage2D.argtypes=[c.c_uint,c.c_int,c.c_int,c.c_int,c.c_int,c.c_int,c.c_uint,c.c_uint,c.c_void_p]
tex=c.c_uint();gl.glGenTextures(1,c.byref(tex));gl.glBindTexture(0xde1,tex);gl.glTexImage2D(0xde1,0,0x8058,16,16,0,0x1908,0x1401,None)
api('glFramebufferTexture2D',None,c.c_uint,c.c_uint,c.c_uint,c.c_uint,c.c_int)(0x8d40,0x8ce0,0xde1,tex,0)
assert api('glCheckFramebufferStatus',c.c_uint,c.c_uint)(0x8d40)==0x8cd5
black=c.c_uint();gl.glGenTextures(1,c.byref(black));gl.glBindTexture(0xde1,black)
pixel=(c.c_ubyte*4)(0,0,0,255);gl.glTexImage2D(0xde1,0,0x8058,1,1,0,0x1908,0x1401,pixel)
gl.glTexParameteri(0xde1,0x2801,0x2600);gl.glTexParameteri(0xde1,0x2800,0x2600)
gl.glViewport(0,0,16,16);gl.glDrawBuffer(0x8ce0);gl.glReadBuffer(0x8ce0);gl.glDisable(0xb71);gl.glDisable(0xbe2)
gl.glVertex2f.argtypes=[c.c_float,c.c_float];gl.glClearColor.argtypes=[c.c_float]*4
gl.glReadPixels.argtypes=[c.c_int,c.c_int,c.c_int,c.c_int,c.c_uint,c.c_uint,c.c_void_p]
colors=[]
for tag in [1,2]:
 gl.glClearColor(0,0,0,1);gl.glClear(0x4000);uniform4(loc(program,b'aColor'),.2,.75,.9,tag)
 gl.glBegin(7)
 for x,y in [(-1,-1),(1,-1),(1,1),(-1,1)]:gl.glVertex2f(x,y)
 gl.glEnd();gl.glFinish();out=(c.c_ubyte*4)();gl.glReadPixels(8,8,1,1,0x1908,0x1401,out);colors.append(list(out))
assert colors[0][:3]==[0,0,0],colors
assert colors[1][0]>90 and colors[1][1]>240 and colors[1][2]>240,colors
print('PASS opaque black target pixel comparison, stock/tagged:',colors)
bind(0x8d40,0)

# Stock body is unchanged beneath the new tagged branch.
stock=Path(r'D:\SteamLibrary\steamapps\common\SOMA\core\shaders\hpsl\game_edge_glow.hpsl').read_text()
assert s[s.index('\tconst float kGlowEdgeSharpness'):]==stock[stock.index('\tconst float kGlowEdgeSharpness'):]
report={'driver_fragment_compile':'PASS','scope':'Production fragment body mechanically translated from HPSL into GLSL; offscreen driver compile, not native SOMA or headset render.','stock_path_unchanged':True,'texture_independent_remote_branch':True,'opaque_black_pixel_stock_tagged':colors}
(R/'audit/remote_shader_hk.json').write_text(json.dumps(report,indent=2));print(report)
# Compile every patched cached vertex/fragment on the real OpenGL driver.
import xml.etree.ElementTree as ET
fixture=R/'build/cache_fixture_hl/_shadersource';bank=(fixture/'shadersource.hpss').read_bytes();count=0
for e in ET.parse(fixture/'shadercache.xml').iter('Shader'):
 data=bank[int(e.get('SourceStart')):int(e.get('SourceEnd'))]
 if b'SOMA_VR_REMOTE_RIM_HM' not in data:continue
 sh=create(0x8b31 if e.get('ShaderType')=='0' else 0x8b30);ptr=c.c_char_p(data);source(sh,1,c.byref(ptr),None);compile(sh);status(sh,0x8b81,c.byref(ok));log(sh,len(buf),None,buf);assert ok.value,(e.get('Name'),buf.value);count+=1
assert count>=3,count
print('PASS actual cached driver shaders',count)
gl.wglMakeCurrent(hd,None);gl.wglDeleteContext.argtypes=[c.c_void_p];gl.wglDeleteContext(ctx);u.ReleaseDC.argtypes=[w.HWND,w.HDC];u.ReleaseDC(hw,hd);u.DestroyWindow.argtypes=[w.HWND];u.DestroyWindow(hw)
