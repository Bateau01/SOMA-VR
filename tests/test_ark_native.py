from pathlib import Path
import xml.etree.ElementTree as ET
import subprocess, math, argparse, json
p=argparse.ArgumentParser();p.add_argument('--game',type=Path,required=True);p.add_argument('--zig',required=True);args=p.parse_args()
R=Path(__file__).resolve().parents[1];A=R/'build/native_ark';A.mkdir(parents=True,exist_ok=True)
s=(R/'tests/ark_query_ct_test.c').read_text()
s=s[:s.index('static void __attribute__((ms_abi)) bounds')]
s='#include <windows.h>\n'+s
s+=r'''
static int pairIndex; static void* (*makeworld)(void);
static void (*destroyworld)(void*);
static void* (*makebox)(void*,float,float,float,int,const float*);
static void* (*makesphere)(void*,float,float,float,int,const float*);
static void* (*makecapsule)(void*,float,float,int,const float*);
static void* (*makecylinder)(void*,float,float,int,const float*);
static int (*collide)(void*,int,void*,const float*,void*,const float*,float*,float*,float*,int);
static void (*getbounds)(const void*,const float*,float*,float*);
static void transpose(const float* a,float* b){for(int r=0;r<4;r++)for(int c=0;c<4;c++)b[r*4+c]=a[c*4+r];}
static void __attribute__((ms_abi)) bounds(const void* p,const float* m,float* lo,float* hi){boundsCalls++;getbounds(p,m,lo,hi);}
static u8 original(void* world,void* av,const float* am,void* bv,const float* bm,void* dv,int limit,u8 correct,int thread){
    Shape *a=av,*b=bv;H508CollideData* d=dv;d->count=0;
    int na=a->type==7?a->count:1,nb=b->type==7?b->count:1;
    float an[16],bn[16];transpose(am,an);transpose(bm,bn);
    for(int i=0;i<na&&d->count<limit;i++)for(int j=0;j<nb&&d->count<limit;j++){
        Shape* ca=a->type==7?a->children[i]:a;Shape* cb=b->type==7?b->children[j]:b;primitiveCalls++;
        float pts[96],norms[96],deps[32];
        pairIndex=j; int n=collide(world,limit-d->count,ca->collision,an,cb->collision,bn,pts,norms,deps,thread);
        for(int k=0;k<n;k++){
            H508Contact* c=&d->begin[d->count++];memset(c,0,sizeof(*c));c->depth=deps[k];
            memcpy(c->point,pts+k*3,12);memcpy(c->normal,norms+k*3,12);
        }
    }
    if(correct&&a->flip)for(int i=0;i<d->count;i++){
        H508Contact* c=d->begin+i;float v[3]={c->point[0]-am[3],c->point[1]-am[7],c->point[2]-am[11]};
        if(h10_dot(v,c->normal)>0)for(int k=0;k<3;k++)c->normal[k]=-c->normal[k];
    }
    return d->count>0;
}
#define p_h508CheckShapeCollision original
#include "repo/source/ark_query_ct.inc"
static void* vt[9];static Shape target,source,items[168];
static double now(void){LARGE_INTEGER c,f;QueryPerformanceCounter(&c);QueryPerformanceFrequency(&f);return (double)c.QuadPart/f.QuadPart;}
static LONG WINAPI crash(EXCEPTION_POINTERS* e){printf("FAULT pair %d %p Newton RVA %llx address %llx\n",pairIndex,(void*)e->ContextRecord->Rip,(unsigned long long)e->ContextRecord->Rip-(unsigned long long)GetModuleHandleA("Newton.dll"),(unsigned long long)e->ExceptionRecord->ExceptionInformation[1]);return EXCEPTION_CONTINUE_SEARCH;}
int main(void){ AddVectoredExceptionHandler(1,crash); setbuf(stdout,0); puts("start");
    HMODULE dll=LoadLibraryA("D:\\SteamLibrary\\steamapps\\common\\SOMA\\Newton.dll");if(!dll)return 10;
    makeworld=(void*)GetProcAddress(dll,"NewtonCreate");destroyworld=(void*)GetProcAddress(dll,"NewtonDestroy");
    makebox=(void*)GetProcAddress(dll,"NewtonCreateBox");makesphere=(void*)GetProcAddress(dll,"NewtonCreateSphere");
    makecapsule=(void*)GetProcAddress(dll,"NewtonCreateCapsule");makecylinder=(void*)GetProcAddress(dll,"NewtonCreateCylinder");
    collide=(void*)GetProcAddress(dll,"NewtonCollisionCollide");getbounds=(void*)GetProcAddress(dll,"NewtonCollisionCalculateAABB");
    void* world=makeworld();if(!world)return 11; puts("world created");
    vt[7]=(void*)child;vt[8]=(void*)count;g_ctShapeBounds=bounds; g_ctShapeSupport=(CTShapeSupport)GetProcAddress(dll,"NewtonCollisionSupportVertex");g_ctShapeInfo=(CTShapeInfo)GetProcAddress(dll,"NewtonCollisionGetInfo");
    target.vt=source.vt=vt;target.type=7;target.count=168;source.collision=makecapsule(world,.009f,.04f,1000,0);
'''
shapes=ET.parse(args.game/'entities/station/tech/ark/ark_tool.ent').findall('.//Shapes/Shape')
assert len(shapes)==168
# Fixture uses authored local translations and Euler XYZ rotations. This is a
# native Newton narrowphase comparison, not a replay of a captured hand pose.
for i,e in enumerate(shapes):
    xyz=list(map(float,e.get('RelativeTranslation').split()))
    rx,ry,rz=map(float,e.get('RelativeRotation').split())
    cx,sx,cy,sy,cz,sz=math.cos(rx),math.sin(rx),math.cos(ry),math.sin(ry),math.cos(rz),math.sin(rz)
    m=[cz*cy,sz*cy,-sy,0,cz*sy*sx-sz*cx,sz*sy*sx+cz*cx,cy*sx,0,cz*sy*cx+sz*sx,sz*sy*cx-cz*sx,cy*cx,0,*xyz,1]
    scale=list(map(float,e.get('Scale').split()))
    typ=e.get('ShapeType')
    shape_args=scale if typ=='Box' else [scale[0]]*3 if typ=='Sphere' else [scale[0],scale[1]]
    fn={'Box':'makebox','Sphere':'makesphere','Cylinder':'makecylinder'}[typ]
    f=lambda v:format(v,'.9g')+'f' if '.' in format(v,'.9g') or 'e' in format(v,'.9g') else format(v,'.9g')+'.0f'
    s+='{float m[16]={'+','.join(map(f,m))+'}; items['+str(i)+'].collision='+fn+'(world,'+','.join(map(f,shape_args))+','+str(i)+',m); target.children['+str(i)+']=items+'+str(i)+';}\n'
s+=r'''
    puts("shapes created"); float am[16]={1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1},bm[16];memcpy(bm,am,64);
    float lo[4],hi[4]; getbounds(items[0].collision,bm,lo,hi);printf("box bounds %g,%g,%g .. %g,%g,%g\n",lo[0],lo[1],lo[2],hi[0],hi[1],hi[2]); getbounds(source.collision,bm,lo,hi);printf("finger bounds %g,%g,%g .. %g,%g,%g\n",lo[0],lo[1],lo[2],hi[0],hi[1],hi[2]); double rt=0,ot=0;unsigned rcalls=0,ocalls=0,hits=0;int failures=0;
    for(int step=0;step<50000;step++){
        g_h14PhysicsSteps=step/100+1; if(step<10)printf("step %d\n",step);
        am[3]=((step*97)%101-50)*.011f;am[7]=((step*37)%71-35)*.011f;am[11]=((step*17)%53-26)*.011f;
        float angle=(step%47)*.137f,c=cosf(angle),sn=sinf(angle); am[0]=c;am[2]=sn;am[8]=-sn;am[10]=c; angle=(step/100%37)*.163f;c=cosf(angle);sn=sinf(angle);bm[0]=c;bm[1]=-sn;bm[4]=sn;bm[5]=c;
        H508Contact rp[32]={0},op[32]={0};H508CollideData rd={0},od={0};rd.begin=rp;rd.end=rd.cap=rp+32;od.begin=op;od.end=od.cap=op+32;
        if(step==0)puts("reference start"); primitiveCalls=0;double t=now();int r=original(world,&source,am,&target,bm,&rd,1,0,0);rt+=now()-t;rcalls+=primitiveCalls;
        if(step==0)puts("optimized start"); primitiveCalls=0;t=now();int o=ct_check_shape_collision(world,&source,am,&target,bm,&od,1,0,0);ot+=now()-t;ocalls+=primitiveCalls;
        if(step==0)puts("queries done"); int same=r==o&&rd.count==od.count;
        if(same)for(int j=0;j<rd.count;j++)for(int k=0;k<7;k++)if(fabsf((&rp[j].point[0])[k]-(&op[j].point[0])[k])>1e-5f)same=0;
        if(!same){if(failures<10)printf("MISMATCH %d counts %d/%d\n",step,rd.count,od.count);failures++;}hits+=r!=0;
    }
    printf("Native Newton 2.36: 50000 cases, hits %u, mismatches %d; primitive calls %u -> %u; time %.3f -> %.3f ms; per query %.4f -> %.4f ms\n",hits,failures,rcalls,ocalls,rt*1000,ot*1000,rt*.02,ot*.02);
    destroyworld(world);return failures?1:0;
}
'''
s=s.replace('\"repo/source/ark_query_ct.inc\"',json.dumps(str(R/'source/ark_query_ct.inc')))
s=s.replace(r'"D:\\SteamLibrary\\steamapps\\common\\SOMA\\Newton.dll"',json.dumps(str(args.game/'Newton.dll')))
(A/'native_bench.c').write_text(s)
subprocess.run([args.zig,'cc','-O2',str(A/'native_bench.c'),'-o',str(A/'native_bench.exe')],check=True)
subprocess.run([str(A/'native_bench.exe')],check=True)








