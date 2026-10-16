
from pathlib import Path
import sys,subprocess,re,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1];A=R/'audit/binding-editor';A.mkdir(parents=True,exist_ok=True)
s=(R/'source/s26n.c').read_text();a=s.index('static u32 g_s26nButtonMap=');b=s.index('static void s26gb_recall_button_sample',a)
head=r"""
#include <stdio.h>
#include <stdint.h>
#include <assert.h>
#include <string.h>
typedef unsigned u32;typedef unsigned char u8;typedef int i32;typedef uint64_t XrPath;typedef void* Handle;
#define ext_Log(...) ((void)0)
"""
tail=r"""
static void reset(void){g_s26nButtonMap=0xE543210;g_s26nBindCommand=-2;g_s26nBindListening=-1;g_s26nBindSuppress=0;g_s26nBindArmMask=0;g_s26nBindChanged=0;s26hc_cancel_proposal();}
static void propose(int role,int src){g_s26hcProposalMap=g_s26nButtonMap;g_s26hcProposalRole=role;g_s26hcProposalSource=src;}
static void unique(void){u32 seen=0;for(int i=0;i<7;i++){u32 v=s26n_binding_source(i);assert(v<=14);if(v<14){assert(!(seen&(1<<v)));seen|=1<<v;}}}
int main(void){
 int tests=0;
 for(int role=0;role<7;role++)for(int src=0;src<14;src++){
  reset();u32 before=g_s26nButtonMap,prior=s26n_binding_source(role);int other=-1;
  for(int i=0;i<7;i++)if(i!=role&&s26n_binding_source(i)==(u32)src)other=i;
  propose(role,src);assert(g_s26nButtonMap==before);assert(s26hc_accept_proposal(role));assert(s26n_binding_source(role)==(u32)src);
  for(int i=0;i<7;i++)if(i!=role)assert(s26n_binding_source(i)==(i==other?prior:((before>>(i*4))&15)));
  unique();assert(!s26hc_accept_proposal(role));tests++;
  reset();before=g_s26nButtonMap;propose(role,src);s26hc_cancel_proposal();assert(!s26hc_accept_proposal(role)&&g_s26nButtonMap==before);tests++;
  reset();propose(role,src);s26n_binding_swap((role+1)%7,13);before=g_s26nButtonMap;assert(!s26hc_accept_proposal(role)&&g_s26nButtonMap==before);tests++;
 }
 for(int role=0;role<7;role++){reset();u32 before=g_s26nButtonMap;s26n_binding_swap(role,14);assert(s26n_binding_source(role)==14);for(int i=0;i<7;i++)if(i!=role)assert(s26n_binding_source(i)==((before>>(i*4))&15));unique();tests++;}
 reset();u8 raw[14]={0},active[14],out[7],oa[7];memset(active,1,14);
 // A held button used to enter the editor cannot be captured until released.
 raw[0]=1;g_s26nBindCommand=6;s26n_buttons_update(raw,active,out,oa);assert(g_s26hcProposalSource==-1);
 raw[0]=0;s26n_buttons_update(raw,active,out,oa);raw[0]=1;s26n_buttons_update(raw,active,out,oa);
 assert(g_s26hcProposalSource==0&&g_s26nButtonMap==0xE543210);for(int i=0;i<7;i++)assert(!out[i]);
 assert(s26hc_accept_proposal(6));assert(s26n_binding_source(0)==14&&s26n_binding_source(6)==0);
 s26n_buttons_update(raw,active,out,oa);for(int i=0;i<7;i++)assert(!out[i]);
 raw[0]=0;s26n_buttons_update(raw,active,out,oa);raw[0]=1;s26n_buttons_update(raw,active,out,oa);assert(out[6]&&!out[0]);
 reset();memset(raw,0,14);g_s26nBindCommand=2;s26n_buttons_update(raw,active,out,oa);
 raw[0]=raw[1]=1;s26n_buttons_update(raw,active,out,oa);assert(g_s26hcProposalSource==-1);
 raw[1]=0;s26n_buttons_update(raw,active,out,oa);assert(g_s26hcProposalSource==-1);
 raw[0]=0;s26n_buttons_update(raw,active,out,oa);raw[0]=1;s26n_buttons_update(raw,active,out,oa);assert(g_s26hcProposalSource==0);
 g_s26nBindCommand=-1;s26n_buttons_update(raw,active,out,oa);assert(g_s26hcProposalSource==-1&&g_s26nButtonMap==0xE543210);
 // Persistence replay: setter order reconstructs saved permutations including unassigned roles.
 for(int role=0;role<7;role++)for(int src=0;src<=14;src++){
  reset();s26n_binding_swap(role,src);u32 desired=g_s26nButtonMap;reset();
  for(int i=0;i<7;i++)s26n_binding_swap(i,(desired>>(4*i))&15);assert(g_s26nButtonMap==desired);tests++;
 }
 printf("PASS %d binding cases plus held-input/release, simultaneous buttons, cancel and output suppression\n",tests);
}
"""
p=A/'test.c';p.write_text(head+s[a:b]+tail)
subprocess.run([sys.argv[1],'cc','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
subprocess.run([str(p.with_suffix('.exe'))],check=True)
m=(R/'runtime/script/modules/MenuHandler.hps').read_text()
assert 'UNBIND RECALL' not in m
assert '"CHANGE BINDING"' in m and '"CLEAR BINDING"' in m
assert 'candidate>=0' in m and '"APPLY"' in m and 'HPL3VR_FinishBinding(false)' in m
assert 'mlVRComfortCategory!=9' in m
strip=re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"','',m,flags=re.S)
for l,r in [('{','}'),('(',')'),('[',']')]:
 n=0
 for ch in strip:
  n+=(ch==l)-(ch==r);assert n>=0
 assert n==0
# Native message box splits the main message at its middle whitespace.
font=ET.parse(r'D:\SteamLibrary\steamapps\common\SOMA\fonts\sansation_large_bold.fnt')
advance={int(c.attrib['id']):int(c.attrib['xadvance']) for c in font.findall('.//char')}
width=lambda text:sum(advance.get(ord(c),18) for c in text)
actions=['JUMP / ACCEPT','RUN / BACK','PAUSE','CENTER CAMERA','CROUCH','HAND REBASE','RECALL OMNI-TOOL']
buttons=['RIGHT STICK CLICK','LEFT SHOULDER','LEFT SECONDARY','UNASSIGNED']
messages=[]
for action in actions:
 for other in actions:
  for button in buttons:
   for prior in buttons:
    consequence=other+(': UNASSIGNED.' if prior=='UNASSIGNED' else ': '+prior+'.')
    messages.append('ASSIGN '+button+' TO '+action+'? '+consequence)
for msg in messages:
 if width(msg)>794:
  mid=len(msg)//2;i=msg.find(' ',mid)
  if i<0:i=msg.rfind(' ',0,mid)
  assert max(width(msg[:i]),width(msg[i+1:]))<=794,msg
print('PASS script structure, submenu/confirm/cancel wiring and native-font conflict-message fit for 1024-wide UI')
