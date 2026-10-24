"""Generate a test-only GLSL conversion from the user's legally installed native FXAA shader; never distribute that shader."""
from pathlib import Path
import sys,re,json
r=Path(__file__).resolve().parents[1]
s=Path(sys.argv[1]).read_text()
for a,b in [('cVector4f','vec4'),('cVector3f','vec3'),('cVector2f','vec2'),('cTexture2D','sampler2D'),('sample(','texture('),('lerp(','mix('),('@','#')]:s=s.replace(a,b)
s=s.replace('uniform sampler2D tex : 0;','uniform sampler2D tex;')
s=re.sub(r'void main\(.*?\)\s*(?=\{)','in vec2 uv;out vec4 out_vColor0;\nvoid main() \n',s,flags=re.S)
s=s.replace('px_vTexCoord0.xy','uv')
s='#version 330 compatibility\n#define AccelerateSearch 1\n'+s
p=r/'build/native_fxaa_iu.inc';p.parent.mkdir(exist_ok=True);p.write_text('static const char fxaaShader[]=\n'+''.join(json.dumps(x)+'\n' for x in s.splitlines(True))+';\n')
