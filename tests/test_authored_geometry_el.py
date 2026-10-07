from pathlib import Path
import ast,subprocess,sys,ctypes as c,json,math
R=Path(__file__).resolve().parents[1];B=R/'build';tree=ast.parse((R/'tests/test_holster_native.py').read_text());literals={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ['head','tail']};head=literals['head'];tail=literals['tail']
head=head.replace('static int s26ej_grip_override(int h,int k,const char*n,float*r,float*f){return 0;}','static int s26ej_grip_override(int h,int k,const char*n,float*r,float*f);')
defs='''typedef struct {char name[96];i32 hand,kind;float rotation[9],fraction[3],joint[5][4];} S26EJGrip;
#include "authored_grips_el.inc"
static int s26ej_grip_override(int h,int k,const char*n,float*r,float*f){const S26EJGrip*e=s26el_default_grip(h,k,n);if(!e)return 0;memcpy(r,e->rotation,36);memcpy(f,e->fraction,12);return 1;}
'''
tail='static float lastLo[4],lastHi[4];\n__declspec(dllexport) void last_bounds(float*lo,float*hi){memcpy(lo,lastLo,12);memcpy(hi,lastHi,12);}\n'+tail;tail=tail.replace('release(g_h14NewtonWorld,col);return ok;','p_s26efBounds(col,id,lastLo,lastHi);release(g_h14NewtonWorld,col);return ok;')
p=B/'authored_geometry_el.c';p.write_text(head+defs+(R/'source/holster_grip_ef.inc').read_text()+(R/'source/holster_runtime_ef.inc').read_text()+tail);dll=B/'authored_geometry_el.dll'
subprocess.run([sys.argv[1],'cc','-shared','-O2','-I',str(R/'source'),str(p),'-o',str(dll)],check=True)
lib=c.CDLL(str(dll));F=c.c_float;P=c.POINTER(F);lib.setup.argtypes=[c.c_char_p];assert lib.setup(b'D:/SteamLibrary/steamapps/common/SOMA/Newton.dll');lib.prepare.argtypes=[c.c_int,c.c_int,c.c_char_p,P,P,P,F,c.c_int]
entries=json.loads((R/'reference/authored_grips/poses.json').read_text());checks=0
for e in entries:
 for scale in [.5,.7,1,1.25,2]:
  for angle in [0,1.2,math.pi,-2.1]:
   co,si=math.cos(angle),math.sin(angle);h=[co,si,0,0,-si,co,0,0,0,0,1,0,3,2,1,1];hm=(F*16)(*h);gc=(F*3)(3.04,2.07,.98);out=(F*16)()
   assert lib.prepare(['left','right'].index(e['hand']),e['kind'],e['profile'].encode(),hm,gc,out,scale,1)
   lo=(F*3)();hi=(F*3)();lib.last_bounds(lo,hi);a=[lo[i]+(hi[i]-lo[i])*e['normalized_body_contact'][i] for i in range(3)]
   for row in range(3):assert abs(sum(out[col*4+row]*a[col] for col in range(3))+out[12+row]-gc[row])<2e-5,(e["profile"],e["hand"],scale,angle,row,list(out),list(gc),a)
   rot=e['controller_relative_rotation']
   for col in range(3):
    for row in range(3):assert abs(out[col*4+row]-sum(h[k*4+row]*rot[col*3+k] for k in range(3)))<2e-5
   checks+=1
lib.close_world();result={'passed':True,'authored_profile_hands':52,'native_newton_cases':checks,'relative_item_scales':[.5,.7,1,1.25,2],'checks':['authored contact follows current collision bounds','controller-relative orientation including inverted controllers','no object scaling introduced'],'limit':'Transform tests do not establish anatomical finger fit at different world scales.'};(B/'authored_geometry_results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))