"""Read actual OpenGL foveation capability from a hidden compatibility context."""
from pathlib import Path
import subprocess,sys,json
R=Path(__file__).resolve().parents[1];B=R/'build';B.mkdir(exist_ok=True)
c=r'''
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <GL/gl.h>
#include <stdio.h>
#include <string.h>
int main(void){
 HMODULE s=LoadLibraryA("D:\\SteamLibrary\\steamapps\\common\\SOMA\\SDL2.dll");if(!s)return 1;
 int (*init)(unsigned)=(void*)GetProcAddress(s,"SDL_Init");
 int (*attr)(int,int)=(void*)GetProcAddress(s,"SDL_GL_SetAttribute");
 void* (*win)(const char*,int,int,int,int,unsigned)=(void*)GetProcAddress(s,"SDL_CreateWindow");
 void* (*ctx)(void*)=(void*)GetProcAddress(s,"SDL_GL_CreateContext");
 if(init(0x20))return 2;attr(17,3);attr(18,3);attr(21,2);
 void*w=win("SOMA VR capability probe",0,0,64,64,2|8|0x10);if(!w||!ctx(w))return 3;
 const char* ex=(const char*)glGetString(GL_EXTENSIONS);
 printf("GPU: %s\nOpenGL: %s\n",glGetString(GL_RENDERER),glGetString(GL_VERSION));
 int have=ex&&strstr(ex,"GL_NV_shading_rate_image ")!=0;
 printf("NV_shading_rate_image: %d\n",have);
 if(have){int w=0,h=0,n=0;glGetIntegerv(0x955c,&w);glGetIntegerv(0x955d,&h);glGetIntegerv(0x955e,&n);printf("Tiles: %dx%d; palette: %d\n",w,h,n);}
 printf("GL error: %u\n",glGetError());return 0;
}
'''
p=B/'probe_foveation.c';p.write_text(c);exe=p.with_suffix('.exe')
subprocess.run([sys.argv[1],'cc',str(p),'-lopengl32','-o',str(exe)],check=True)
r=subprocess.run([str(exe)],capture_output=True,text=True);print(r.stdout+r.stderr)
(B/'foveation_capability.json').write_text(json.dumps({'exit':r.returncode,'output':r.stdout,'scope':'Local GPU/driver only, hidden compatibility GL context.'},indent=2));raise SystemExit(r.returncode)
