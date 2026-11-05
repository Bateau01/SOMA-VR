"""Actual OpenXR native Look dispatch; injected input, not physical gamepad."""
from pathlib import Path
import sys,re,json
r=Path(__file__).resolve().parents[1];s=(r/'tests/test_native_input_capture.py').read_text()
needle='LogNewLine("IU_STAGE|"+phase'
s=s.replace(needle,'if(phase==0 || phase==1)cScript_RunGlobalFunc("NITEST","","LOOK");'+needle)
ns={'__file__':str(r/'tests/test_native_input_capture.py'),'__name__':'__main__'}
exec(compile(s,str(r/'tests/test_native_input_capture.py'),'exec'),ns)
out=ns['out'];vr=(out/'hpl3vr.log').read_text(errors='replace')
rows=re.findall(r'IZ_LOOK mode (\d+) gameplay 1 pitch ([\d.e+-]+)->([\d.e+-]+) yaw ([\d.e+-]+)->([\d.e+-]+)',vr)
assert rows,'Actual camera dispatch was not observed'
for mode,p0,p1,y0,y1 in rows:
 assert abs(float(p1)-float(p0))>1e-4,(p0,p1)
(out/'iz-camera.json').write_text(json.dumps({'passed':True,'rows':rows,'scope':__doc__},indent=2))
print('IZ camera accepted',rows)
