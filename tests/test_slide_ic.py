from pathlib import Path
import subprocess,sys,json
r=Path(__file__).resolve().parents[1]
s=(r/'runtime/script/helpers/helper_vr_roomscale_hr.hps').read_text().replace('iCharacterBody@','iCharacterBody*').replace('&in','&').replace('body is null','body==nullptr').replace('body.','body->')
prefix=r'''
#include <cmath>
#include <cstdio>
struct cVector3f {float x=0,y=0,z=0; cVector3f(){} cVector3f(float a,float b,float c):x(a),y(b),z(c){} float Length()const{return sqrtf(x*x+y*y+z*z);} cVector3f operator+(cVector3f b)const{return {x+b.x,y+b.y,z+b.z};} cVector3f operator-(cVector3f b)const{return {x-b.x,y-b.y,z-b.z};} cVector3f operator*(float b)const{return {x*b,y*b,z*b};} cVector3f operator/(float b)const{return *this*(1/b);} };
cVector3f cVector3f_Zero;float cMath_Abs(float x){return fabsf(x);}float cMath_Vector3Dist(cVector3f a,cVector3f b){return (a-b).Length();}
struct iCharacterBody {cVector3f p,n;int calls=0;bool CheckCharacterFits(cVector3f q,bool,int,cVector3f& push){calls++;float d=q.x*n.x+q.z*n.z;push=n*(-d);return d<=1e-7f;} cVector3f GetPosition(){return p;}void SetPosition(cVector3f v,bool){p=v;}};
'''
main=r'''
int main(){int errors=0;for(int i=0;i<360;i++){float a=i*.01745329252f;iCharacterBody b;b.n={cosf(a),0,sinf(a)};cVector3f t={-sinf(a),0,cosf(a)};cVector3f d=b.n*.03f+t*.04f;auto v=HPL3VR_RoomscaleMove(&b,d);if((v-t*.04f).Length()>.0001f||b.calls>34||fabsf(v.y)>1e-7f)errors++;}iCharacterBody b;b.n={1,0,0};b.p={.1f,0,0};if(HPL3VR_RoomscaleMove(&b,{-.05f,0,0}).Length()!=0)errors++;if(HPL3VR_RoomscaleMove(&b,{0,.05f,0}).Length()!=0)errors++;printf("rotated wall cases=360; overlap/vertical guards; errors=%d\n",errors);return errors?1:0;}
'''
p=r/'build/slide_ic.cpp';p.write_text(prefix+s+main)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
t=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True);print(t.stdout)
(r/'docs/v109-evidence/slide_ic.json').write_text(json.dumps({'scope':'production script translated to C++ with synthetic planar collision queries; not Newton','exit':t.returncode,'output':t.stdout},indent=2));assert t.returncode==0
