"""Extract actual queue implementation. No GUI engine or headset simulation claimed."""
from pathlib import Path
import argparse, subprocess, json
p=argparse.ArgumentParser()
p.add_argument('--zig',required=True)
p.add_argument('--source',type=Path)
p.add_argument('--baseline',action='store_true')
a=p.parse_args(); root=Path(__file__).resolve().parents[1]
s=(a.source or root/'source/s26n.c').read_text(encoding='utf-8')
def function(name,kind='i32'):
    start=s.index('static '+kind+' '+name+'(')
    opening=s.index('{',start); depth=1; end=opening+1
    while depth:
        depth+=(s[end]=='{')-(s[end]=='}');end+=1
    return s[start:end]
start=s.rfind('typedef struct',0,s.index('S26GuiQueue;'))
typedef=s[start:s.index('S26GuiQueue;',start)+len('S26GuiQueue;')]
extra='' if a.baseline else function('s26hr_gui_cancel','void')
c='''#include <stdio.h>
#include <string.h>
typedef int i32;
'''+typedef+'\n'+function('s26_gui_enqueue')+'\n'+function('s26_gui_consume')+'\n'+extra+r'''
int main(void){
 S26GuiQueue q={0};float pos[2];int got[4],accepted;
 s26_gui_enqueue(&q,1,10,20);s26_gui_enqueue(&q,0,10,20);
 accepted=s26_gui_enqueue(&q,1,30,40);s26_gui_enqueue(&q,0,30,40);
 for(int i=0;i<4;i++)got[i]=s26_gui_consume(&q,pos);
 printf("second tap accepted=%d edges=%d,%d,%d,%d\n",accepted,got[0],got[1],got[2],got[3]);
 if(!accepted||got[0]!=1||got[1]!=2||got[2]!=1||got[3]!=2)return 1;
 if(pos[0]!=30||pos[1]!=40||q.held)return 2;
 memset(&q,0,sizeof(q));
 if(!s26_gui_enqueue(&q,1,12,13)||s26_gui_consume(&q,pos)!=1)return 3;
 q.pos[0]=55;q.pos[1]=66;
 if(s26_gui_consume(&q,pos)!=3||pos[0]!=55||pos[1]!=66)return 4;
 if(s26_gui_enqueue(&q,1,99,99))return 5;
 if(!s26_gui_enqueue(&q,0,55,66)||s26_gui_consume(&q,pos)!=2||s26_gui_consume(&q,pos)!=0)return 6;
 puts("PASS: repeated fast tap edges, coordinates, held drag, duplicate down and final release");
 EXTRA_TESTS
 return 0;
}
'''
c=c.replace('EXTRA_TESTS','' if a.baseline else r'''
 memset(&q,0,sizeof(q));
 for(int cycle=0;cycle<100;cycle++){
   for(int tap=0;tap<4;tap++){
     if(!s26_gui_enqueue(&q,1,tap,cycle)||!s26_gui_enqueue(&q,0,tap,cycle))return 7;
   }
   if(s26_gui_enqueue(&q,1,999,999))return 8;
   for(int edge=0;edge<8;edge++){
     if(s26_gui_consume(&q,pos)!=(edge%2?2:1)||pos[0]!=edge/2||pos[1]!=cycle)return 9;
   }
   if(q.held||q.inputDown||s26_gui_consume(&q,pos))return 10;
 }
 /* Cancellation before presentation must never invent a click. */
 s26_gui_enqueue(&q,1,1,2);s26_gui_enqueue(&q,0,1,2);
 s26hr_gui_cancel(&q);if(s26_gui_consume(&q,pos))return 11;
 /* A presented held press must get exactly one release, with pending taps discarded. */
 s26_gui_enqueue(&q,1,1,2);s26_gui_consume(&q,pos);
 s26_gui_enqueue(&q,0,1,2);s26_gui_enqueue(&q,1,3,4);
 s26hr_gui_cancel(&q);s26hr_gui_cancel(&q);
 if(s26_gui_consume(&q,pos)!=2||s26_gui_consume(&q,pos)||q.held||q.inputDown)return 12;
 /* Force the ring to wrap from a partially drained state. */
 for(int i=0;i<100;i++){
   if(!s26_gui_enqueue(&q,1,i,0)||s26_gui_consume(&q,pos)!=1)return 13;
   if(!s26_gui_enqueue(&q,0,i,0)||s26_gui_consume(&q,pos)!=2)return 14;
 }
 puts("PASS: saturation, release reservation, ring wrap, pending/held cancellation and recovery");
 /* Mode may change before rendering: queue retains the originating channel. */
 s26_gui_enqueue(&q,1,1,2);q.edges[(q.read+q.count-1)&7].direct=1;
 s26_gui_enqueue(&q,0,1,2);s26_gui_enqueue(&q,1,3,4);
 if(s26_gui_consume(&q,pos)!=1||!q.heldDirect)return 15;
 if(s26_gui_consume(&q,pos)!=2||q.heldDirect)return 16;
 if(s26_gui_consume(&q,pos)!=1||q.heldDirect)return 17;
 if(s26_gui_consume(&q,pos)!=3||q.heldDirect)return 18;
 puts("PASS: physical/laser origin survives deferred presentation and release");
''')
b=root/'build';b.mkdir(exist_ok=True)
name='terminal_queue_baseline' if a.baseline else 'terminal_queue_candidate'
(b/(name+'.c')).write_text(c)
subprocess.run([a.zig,'cc','-O2',str(b/(name+'.c')),'-o',str(b/(name+'.exe'))],check=True)
r=subprocess.run([str(b/(name+'.exe'))],capture_output=True,text=True)
e=root/'docs/v109-evidence';e.mkdir(exist_ok=True)
(e/(name+'.json')).write_text(json.dumps({'scope':'Extracted production queue, synthetic events; not native GUI/headset proof','exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2))
print(r.stdout);raise SystemExit(r.returncode)
