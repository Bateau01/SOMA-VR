from pathlib import Path
import subprocess,sys
r=Path(__file__).resolve().parents[1]
s=(r/"source/desktop_mirror_fi.inc").read_text()
assert "info.work." not in s
assert "info.monitor.bottom-origin.y" in s
body=s[s.index("static i32 s26fi_fit"):s.index("static i32 s26hp_mirror_rect")]
p=r/"build/mirror_geometry.c";p.parent.mkdir(exist_ok=True)
p.write_text('#include <stdio.h>\n#include <stdlib.h>\ntypedef int i32;typedef long long i64;\n'+body+'\n#define C(x) do{if(!(x)){printf("FAIL line %d\\n",__LINE__);return 1;}}while(0)\nint main(){int r[4],n=0;\n C(s26hp_visible_fit(3000,3000,3000,3000,3000,3000,0,0,2560,1440,r));\n C(r[0]==560&&r[1]==1560&&r[2]==2000&&r[3]==3000);\n for(int w=640;w<=7680;w+=160)for(int h=480;h<=4320;h+=240){\n C(s26hp_visible_fit(2800,3000,8192,8192,8192,8192,0,0,w,h,r));\n C(r[0]>=0&&r[2]<=w&&r[1]>=8192-h&&r[3]<=8192);\n C(abs((r[2]-r[0])*3000-(r[3]-r[1])*2800)<=3000);n++;}\n C(s26hp_visible_fit(1000,1000,4000,4000,2000,2000,100,200,1700,1100,r));\n C(r[0]==900&&r[2]==2700&&r[1]==1800&&r[3]==3600);\n C(!s26hp_visible_fit(100,100,3000,3000,3000,3000,4000,0,5000,1000,r));\n C(!s26hp_visible_fit(0,100,3000,3000,3000,3000,0,0,1000,1000,r));\n C(s26hp_visible_fit(2560,1440,2560,1440,2560,1440,0,0,2560,1440,r));\n C(r[0]==0&&r[1]==0&&r[2]==2560&&r[3]==1440);\n printf("PASS %d mirror aspect/bounds cases, DPI scaling, offscreen, unchanged fitting window\\n",n);}\n')
subprocess.run([sys.argv[1],"cc",str(p),"-o",str(p.with_suffix(".exe"))],check=True)
subprocess.run([str(p.with_suffix(".exe"))],check=True)
