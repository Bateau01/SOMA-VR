"""Native triangle-mesh contacts and rejected-overlap parity; not authored gameplay."""
from pathlib import Path
import subprocess,sys,json,hashlib
r=Path(__file__).resolve().parents[1];b=r/'build/cpu40-tree';b.mkdir(exist_ok=True)
s=(r/'build/cpu40-native/test.c').read_text()
s=s.replace('static void contact(', 'static unsigned rejects;static int overlap(const void*m,const void*a,const void*b,int thread){unsigned long long x=(unsigned long long)getUD(a),y=(unsigned long long)getUD(b);if((x&&x<=4)||(y&&y<=4)){__atomic_fetch_add(&rejects,1,__ATOMIC_RELAXED);return 0;}return 1;}\nstatic void contact(')
s=s.replace('static unsigned rc[240],rf[240];','static unsigned rc[240],rf[240],rr[240];')
s=s.replace('body(w,box(w,40,1,40,0,0),mat);',r'''void*(*tree)(void*,int)=(void*)GetProcAddress(m,"NewtonCreateTreeCollision");void(*begin)(void*)=(void*)GetProcAddress(m,"NewtonTreeCollisionBeginBuild");void(*face)(void*,int,const float*,int,int)=(void*)GetProcAddress(m,"NewtonTreeCollisionAddFace");void(*end)(void*,int)=(void*)GetProcAddress(m,"NewtonTreeCollisionEndBuild");C(tree&&begin&&face&&end);void*floor=tree(w,0);begin(floor);float triangles[18]={-20,.5f,-20,20,.5f,20,20,.5f,-20,-20,.5f,-20,-20,.5f,20,20,.5f,20};face(floor,3,triangles,12,0);face(floor,3,triangles+9,12,0);end(floor,1);body(w,floor,mat);''')
s=s.replace('mc(w,0,0,0,0,contact);contacts=forces=0;','mc(w,0,0,0,overlap,contact);contacts=forces=rejects=0;')
s=s.replace('rf[i]=forces;','rf[i]=forces;rr[i]=rejects;').replace('rc[i]!=contacts||rf[i]!=forces','rc[i]!=contacts||rf[i]!=forces||rr[i]!=rejects')
s=s.replace('*job=old;destroy(w);','if(scene==4)C(rejects>0);*job=old;destroy(w);')
(b/'test.c').write_text(s);subprocess.run([sys.argv[1],'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe')],capture_output=True,text=True,timeout=180)
(r/'audit/cpu40-tree.json').write_text(json.dumps(dict(scope=__doc__,exit=x.returncode,output=x.stdout+x.stderr,source_sha256=hashlib.sha256(s.encode()).hexdigest()),indent=2));print(x.stdout+x.stderr);raise SystemExit(x.returncode)
