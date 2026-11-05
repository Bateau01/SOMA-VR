"""Exact release collision core against native Newton; not an HPL progression test."""
from pathlib import Path
import argparse,subprocess,hashlib,json
r=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--zig',required=True);p.add_argument('--newton',required=True,type=Path);p.add_argument('--case');p.add_argument('--through-scene',type=int);p.add_argument('--native-control',action='store_true');p.add_argument('--threads',type=int,default=1);p.add_argument('--no-filter',action='store_true');p.add_argument('--shadow',action='store_true');p.add_argument('--side-effects',action='store_true');a=p.parse_args()
assert hashlib.sha256(a.newton.read_bytes()).hexdigest()=='1be451fb2e250aded9ddf3771418cee21990e4ef07fa0fefe0a8cfaf55766b74'
b=r/'build/cpu56-release-test';b.mkdir(parents=True,exist_ok=True)
core='#define CPU_LEAF_FILTER 1\n'+(r/'source/cpu_leaf_filter.inc').read_text()
if a.no_filter:core=core.replace('int empty=c56_empty(p);','int empty=0;')
if a.shadow:
 core=core.replace('if(empty){*(u32*)((u8*)p+0xd0)&=~2u;return 0;}return c56Leaf(w,p);','int result=c56Leaf(w,p);if(empty&&result){printf(\"MISSED CONTACT %d\\n\",result);exit(77);}return result;')
if a.side_effects:
 core=core.replace('int result=c56Leaf(w,p);', 'u8 before[0xd4];memcpy(before,p,sizeof(before));unsigned mx0;__asm__ volatile("stmxcsr %0":"=m"(mx0));int result=c56Leaf(w,p);unsigned mx1;__asm__ volatile("stmxcsr %0":"=m"(mx1));if(empty){static unsigned seen[53],fp;for(int k=0;k<53;k++)if(k!=48&&((u32*)before)[k]!=((u32*)p)[k]&&seen[k]++<3)printf("SIDE %x %x -> %x result=%d\\n",k*4,((u32*)before)[k],((u32*)p)[k],result);if(mx0!=mx1&&fp++<3)printf("FP %x -> %x\\n",mx0,mx1);}')
s=(r/'tests/cpu56_fixture.c.in').read_text().replace('/* CPU56_RELEASE_CORE */',core)
assert a.threads in (1,2,4,8)
s=s.replace('threads(w,8);',f'threads(w,{a.threads});')
if a.native_control:s=s.replace('c41Observe=mode;', 'c41Observe=0;')
if a.through_scene is not None:s=s.replace('scene<7',f'scene<{a.through_scene+1}')
if a.case:
 scene,rate=map(int,a.case.split(':'));assert 0<=scene<=6 and rate in (60,120)
 s=s.replace('double timings[2]={0};',f'if(scene!={scene}||rate!={rate})continue;double timings[2]={{0}};')
s=s.replace('if(delta>maxdelta)maxdelta=delta;', 'if(delta>0.0001&&maxdelta<=0.0001)printf(\"FIRST_DIFF scene=%d hz=%d step=%d body=%d component=%d old=%.9g new=%.9g\\n\",scene,rate,i,j,k,reference[i][j][k],out[k]);if(delta>maxdelta)maxdelta=delta;')
(b/'test.c').write_text(s)
subprocess.run([a.zig,'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe'),str(a.newton.resolve())],capture_output=True,text=True,timeout=360)
(b/('result-t'+str(a.threads)+('-native-control' if a.native_control else '')+('-through'+str(a.through_scene) if a.through_scene is not None else '')+('-'+a.case.replace(':','_') if a.case else '')+('-effects' if a.side_effects else '')+('-no-filter' if a.no_filter else '-shadow' if a.shadow else '')+'.json')).write_text(json.dumps(dict(exit=x.returncode,output=x.stdout+x.stderr,source_sha256=hashlib.sha256(s.encode()).hexdigest()),indent=2));print(x.stdout+x.stderr);raise SystemExit(x.returncode)
