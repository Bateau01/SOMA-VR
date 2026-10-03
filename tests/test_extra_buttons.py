"""Run production assignment/listening logic against all fourteen input sources."""
from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1];s=(R/'source/s26n.c').read_text()
code=s[s.index('/* S26N button remapping.'):s.index('static void s26n_apply_button_bindings')]
header=r'''
#include <stdio.h>
#include <string.h>
typedef unsigned u32;typedef int i32;typedef unsigned char u8;typedef unsigned long long XrPath;typedef void* Handle;
#define ext_Log(...) ((void)0)
#define C(x) do{++checks;if(!(x)){printf("FAIL %d %s\n",__LINE__,#x);return 1;}}while(0)
'''
body=r'''
int main(void){int checks=0;
 u8 raw[14]={0},active[14],out[6],oa[6];memset(active,1,sizeof(active));
 for(unsigned role=0;role<6;role++)for(unsigned src=0;src<14;src++){
  g_s26nButtonMap=0x543210u;g_s26nBindSuppress=0;g_s26nBindCommand=-2;g_s26nBindListening=-1;
  s26n_binding_swap(role,src);C(s26n_binding_source(role)==src);
  for(unsigned i=0;i<6;i++)for(unsigned j=i+1;j<6;j++)C(s26n_binding_source(i)!=s26n_binding_source(j));
  memset(raw,0,sizeof(raw));s26n_buttons_update(raw,active,out,oa);
  raw[src]=1;s26n_buttons_update(raw,active,out,oa);C(out[role]&&oa[role]);
  for(unsigned i=0;i<6;i++)if(i!=role)C(!out[i]);
  active[src]=0;s26n_buttons_update(raw,active,out,oa);C(!out[role]&&!oa[role]);active[src]=1;
 }
 // Every extra button requires release followed by one unambiguous press.
 for(unsigned src=6;src<14;src++){
  memset(raw,0,sizeof(raw));raw[src]=1;g_s26nButtonMap=0x543210u;g_s26nBindCommand=2;
  s26n_buttons_update(raw,active,out,oa);C(g_s26nBindListening==2);
  raw[src]=0;s26n_buttons_update(raw,active,out,oa);C(g_s26nBindListening==2);
  raw[src]=1;s26n_buttons_update(raw,active,out,oa);C(g_s26nBindListening==-1&&s26n_binding_source(2)==src);
  for(int i=0;i<6;i++)C(!out[i]);
  s26n_buttons_update(raw,active,out,oa);C(!out[2]);
  raw[src]=0;s26n_buttons_update(raw,active,out,oa);
  raw[src]=1;s26n_buttons_update(raw,active,out,oa);C(out[2]);
 }
 // Persisted settings contain source IDs, not the internal packed representation.
 unsigned saved[6]={13,12,11,10,9,8};g_s26nButtonMap=0x543210u;
 for(unsigned i=0;i<6;i++)s26n_binding_swap(i,saved[i]);
 for(unsigned i=0;i<6;i++)C(s26n_binding_source(i)==saved[i]);
 for(unsigned i=0;i<6;i++)s26n_binding_swap(i,i);
 C(g_s26nButtonMap==0x543210u);
 unsigned old=g_s26nButtonMap;s26n_binding_swap(6,0);s26n_binding_swap(0,14);C(g_s26nButtonMap==old);
 printf("PASS %d extended remapping checks\n",checks);return 0;
}
'''
p=R/'build/extra_buttons.c';p.write_text(header+code+body)
subprocess.run([sys.argv[1],'cc','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
subprocess.run([str(p.with_suffix('.exe'))],check=True)
