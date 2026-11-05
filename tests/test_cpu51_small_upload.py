"""Real-driver candidate: extend unchanged immutable upload algorithm to small DDS mips."""
from pathlib import Path
import subprocess,sys,struct,json,os
r=Path(__file__).resolve().parents[1];b=r/'build/cpu51-upload';b.mkdir(exist_ok=True)
s=(r/'tests/texture_upload_gl.c').read_text().replace('cpuTrialMinBytes=65536;','cpuTrialMinBytes=0;').replace('../source/cpu_texture_storage_trial.inc','../../source/cpu_texture_storage_trial.inc')
s=s.replace('if(!memcmp(bytes+84,"DXT5",4))', 'if(!memcmp(bytes+84,"DXT3",4)){fmt=0x83f2;block=16;}if(!memcmp(bytes+84,"DXT5",4))')
# Include remains relative to generated C's build directory.
(b/'test.c').write_text(s)
files=[]
for fourcc,block in [(b'DXT1',8),(b'DXT3',16),(b'DXT5',16),(b'ATI2',16)]:
 for size in [8,16,64,128,256]:
  levels=size.bit_length();header=[0]*31;header[0]=124;header[1]=0x21007;header[2]=header[3]=size;header[4]=max(1,(size+3)//4)**2*block;header[6]=levels;header[18]=32;header[19]=4;header[20]=int.from_bytes(fourcc,'little');header[26]=0x401008
  data=b'DDS '+struct.pack('<31I',*header)
  for level in range(levels):
   n=max(1,size>>level);count=max(1,(n+3)//4)**2
   data+=(bytes.fromhex('ffff0000e4e4e4e4')*(block//8))*count
  p=b/f'small-{fourcc.decode()}-{size}.dds';p.write_bytes(data);files.append(str(p))
zig=str(r.parent/'SOMA_VR_SCALE_INVESTIGATION/tools/ziglang/zig.exe')
subprocess.run([zig,'cc',str(b/'test.c'),'-O2','-lopengl32','-lgdi32','-o',str(b/'test.exe')],check=True)
result=subprocess.run([str(b/'test.exe'),*files],capture_output=True,text=True,timeout=120)
(r/'audit/cpu51-small-upload.txt').write_text(result.stdout+result.stderr)
print(result.stdout);print(result.stderr);assert result.returncode==0

env=os.environ.copy();env['CPU5_LATC']='1'
r2=subprocess.run([str(b/'test.exe'),*[p for p in files if 'ATI2' in p]],capture_output=True,text=True,timeout=120,env=env)
(r/'audit/cpu51-small-latc.txt').write_text(r2.stdout+r2.stderr);assert r2.returncode==0,r2.stdout+r2.stderr
print('PASS small LATC2 exact-format and unsupported-capability fallback')
