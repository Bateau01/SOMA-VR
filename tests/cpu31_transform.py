from pathlib import Path
import re

def function(s,name):
 m=re.search(r'static i32 '+name+r'\([^;{]*\)\s*\{',s);assert m,name
 a=m.start();i=m.end();depth=1
 while depth:
  depth+=(s[i]=='{')-(s[i]=='}');i+=1
 return a,i,s[a:i]

def transform(s,paired=True):
 r=Path(__file__).resolve().parents[1]
 s=s.replace('#include "rocker_y.inc"',(r/'source/rocker_y.inc').read_text())
 common=(r/'tests/cpu31_local.inc').read_text()
 marker='static i32 h20_mem_writable';s=s.replace(marker,common+'\n'+marker,1)
 for name,new in [('s26y_body_slot','cpu31_slot'),('h540_nonphysical_area_body','cpu31_area'),('h5755ct_noncharacter_body_eligible','cpu31_eligible')]:
  a,b,body=function(s,name)
  clone=body.replace('static i32 '+name+'(','static i32 '+new+'(',1)
  i=clone.index('){');clone=clone[:i]+',CPU31View* view'+clone[i:]
  clone=re.sub(r'h20_mem_readable\((\(u8\*\)w\+0x[0-9a-f]+|w),([^)]*)\)',r'cpu31_readable(view,w,\1,\2)',clone)
  assert 'cpu31_readable' in clone
  s=s[:b]+'\n'+clone+'\n'+s[b:]
 s+='\nstatic i32 cpu31_rocker(const void*body,CPU31View*view){return cpu31_slot(body,view)>=0;}\n'
 a,b,body=function(s,'h530_hand_overlap_filter') if False else (0,0,'')
 # The original filter carries an explicit ABI attribute.
 marker='static i32 __attribute__((ms_abi)) h530_hand_overlap_filter('
 a=s.index(marker);i=s.index('{',a)+1;depth=1;b=i
 while depth:
  depth+=(s[b]=='{')-(s[b]=='}');b+=1
 body=s[a:b]
 select='((g_h14PhysicsSteps/120u)%4u==1u||(g_h14PhysicsSteps/120u)%4u==2u)' if paired else '1'
 body=body[:body.index('{')+1]+'CPU31View view={0};i32 reuse='+select+';'+body[body.index('{')+1:]
 body=body.replace('s26y_rocker_body(other)','(reuse?cpu31_rocker(other,&view):s26y_rocker_body(other))')
 body=body.replace('h540_nonphysical_area_body(other)','(reuse?cpu31_area(other,&view):h540_nonphysical_area_body(other))')
 body=body.replace('h5755ct_noncharacter_body_eligible(h,other)','(reuse?cpu31_eligible(h,other,&view):h5755ct_noncharacter_body_eligible(h,other))')
 return s[:a]+body+s[b:]
