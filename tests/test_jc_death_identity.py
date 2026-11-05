from pathlib import Path
import subprocess,sys,json
r=Path(__file__).resolve().parents[1];s=(r/'source/s26n.c').read_bytes().decode('cp1252')
a=s.index('    if(h5748t_sso_eq(objectName,"VRKEYHELD",9u))');b=s.index('    if(h5748t_sso_eq(objectName,"VROMNISTOW"',a)
code=r"""
#include <cstring>
#include <cstdio>
#include <cassert>
struct H5730TString{const char*text;};struct H576AAInvItem{int stowed;void*raw;}item;
int mode,g_h576bfMapTransitionActive,lookups;void*g_h14GripBody[2];
int ni_native_input(){return mode;}int h5748t_sso_eq(const H5730TString*p,const char*s,unsigned){return p&&strcmp(p->text,s)==0;}
int h5748n_copy_tstring(void*p,char*s,unsigned n){if(!p)return 0;strncpy(s,((H5730TString*)p)->text,n);return 1;}
H576AAInvItem*h576aa_inv_find_logical(const char*s){lookups++;return strcmp(s,"BrokenRobotBrain")==0?&item:nullptr;}
unsigned query(const H5730TString*objectName,const H5730TString*className){
"""+s[a:b]+r"""return 0;}
int main(){int checks=0;H5730TString token={"VRKEYHELD"},name={"BrokenRobotBrain"},wrong={"NotOwned"};
for(int h=0;h<2;h++)for(int c=0;c<8;c++){
 mode=c==4;g_h576bfMapTransitionActive=c==5;item.stowed=c==1;item.raw=c==2?nullptr:(void*)42;
 g_h14GripBody[0]=g_h14GripBody[1]=nullptr;g_h14GripBody[h]=c==3?(void*)43:(void*)42;
 lookups=0;unsigned v=query(&token,c==6?&wrong:c==7?nullptr:&name);
 assert(v==(c==0));if(c==4||c==5||c==7)assert(lookups==0);assert(item.raw==(c==2?nullptr:(void*)42));checks++;
}printf("PASS %d read-only death identity cases; no native geometry/physical ownership proof\n",checks);}
"""
b=r/'build/jc-death-identity.cpp';b.write_text(code);subprocess.run([sys.argv[1],'c++','-O2',str(b),'-o',str(b.with_suffix('.exe'))],check=True)
v=subprocess.run([str(b.with_suffix('.exe'))],capture_output=True,text=True);print(v.stdout+v.stderr);(r/'audit/jc-death-recovery/identity-test.json').write_text(json.dumps(dict(exit=v.returncode,output=v.stdout+v.stderr),indent=2));raise SystemExit(v.returncode)
