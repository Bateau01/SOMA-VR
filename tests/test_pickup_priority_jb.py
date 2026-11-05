"""Extracted fresh-grip pickup arbitration; mocked permissions/mesh, not gameplay proof."""
from pathlib import Path
import subprocess,sys
r=Path(__file__).resolve().parents[1]
s=(r/'source/s26n.c').read_text()
fn=(r/'audit/jb-pickup-priority-unconfirmed.inc').read_text()
head=r"""
#include <assert.h>
#include <stdio.h>
typedef int i32;
typedef struct {const void* nativeNow;int nativeNowPoint,nativeNowJointed;float nativeNowGap,nativeNowContact[3];}H14Scan;
static int joint,permitted,icon,rawMatch,queued,queueCalls;static const float* actualHand;static const void* candidate;
static const void* h568_first_external_joint(const void*b){return joint?b:0;}
static void* h482_body_owner(const void*b,void**w){*w=(void*)b;return(void*)b;}
static int h576ad_target_can_interact(void*w,void*o,const void**raw,int*i){*raw=rawMatch?o:0;*i=icon;return permitted;}
static int h25_queue_native_interact(int h,const void*b,const float*m,const float*p,float gap,int j){assert(h==1&&b==candidate&&m==actualHand&&j==0&&gap<=.012f);queueCalls++;return queued;}
"""
main=r"""
int main(void){int token=0;float hand[16]={0};actualHand=hand;candidate=&token;
H14Scan s={&token,0,0,.005f,{0}};permitted=rawMatch=queued=1;icon=14;
assert(s26jb_queue_nearest_pickup(1,&s,hand)==1&&queueCalls==1);
queueCalls=0;assert(!s26jb_queue_nearest_pickup(1,0,hand));assert(!s26jb_queue_nearest_pickup(1,&s,0));
s.nativeNow=0;assert(!s26jb_queue_nearest_pickup(1,&s,hand));s.nativeNow=&token;
s.nativeNowPoint=-1;assert(!s26jb_queue_nearest_pickup(1,&s,hand));s.nativeNowPoint=0;
s.nativeNowJointed=1;assert(!s26jb_queue_nearest_pickup(1,&s,hand));s.nativeNowJointed=0;
s.nativeNowGap=.0121f;assert(!s26jb_queue_nearest_pickup(1,&s,hand));s.nativeNowGap=.005f;
joint=1;assert(!s26jb_queue_nearest_pickup(1,&s,hand));joint=0;
permitted=0;assert(!s26jb_queue_nearest_pickup(1,&s,hand));permitted=1;
rawMatch=0;assert(!s26jb_queue_nearest_pickup(1,&s,hand));rawMatch=1;
for(int i=0;i<32;i++){if(i==14)continue;icon=i;assert(!s26jb_queue_nearest_pickup(1,&s,hand));}icon=14;
assert(queueCalls==0);queued=0;assert(!s26jb_queue_nearest_pickup(1,&s,hand)&&queueCalls==1);
printf("PASS pickup admission rejects invalid/contact/permission/body/joint/icon cases; preserves failed queue\n");return 0;}
"""
b=r/'build/jb-pickup-priority';b.mkdir(exist_ok=True)
f=b/'test.c';f.write_text(head+fn+main)
subprocess.run([sys.argv[1],'cc','-O2',str(f),'-o',str(b/'test.exe')],check=True)
subprocess.run([str(b/'test.exe')],check=True)
print('Private rejected candidate only: not integrated or gameplay-validated')
