"""Observation-only function wrappers; original bodies and calls are preserved."""
def augment(s,prof):
    from pathlib import Path
    s=s.replace('#include "rocker_y.inc"', (Path(__file__).resolve().parents[1]/"source/rocker_y.inc").read_text())
    specs=[('h540_nonphysical_area_body','const void* body','body'),('h5755ct_noncharacter_body_eligible','i32 hand,const void* body','hand,body'),('s26y_rocker_body','const void* body','body'),('h530_hand_index_for_body','const void* body','body'),('h540_segment_slot_for_body','const void* body,i32* outHand','body,outHand')]
    s='static unsigned long long cpu30_begin_helper(unsigned);static void cpu30_end_helper(unsigned,unsigned long long);\n'+s
    for kind,(name,args,call) in enumerate(specs,3):
        needle='static i32 '+name+'('+args+')'
        start=s.index(needle+'{');brace=s.index('{',start);depth=1;end=brace+1
        while depth:
            depth+=(s[end]=='{')-(s[end]=='}');end+=1
        original=s[start:end];renamed=original.replace(needle,'static i32 cpu30_original_'+name+'('+args+')',1)
        wrapper='\n'+needle+'{u64 t=cpu30_begin_helper('+str(kind)+');i32 result=cpu30_original_'+name+'('+call+');cpu30_end_helper('+str(kind)+',t);return result;}\n'
        s=s[:start]+renamed+wrapper+s[end:]
    prof=prof.replace('cpu26Slots[64][3]','cpu26Slots[64][8]').replace('k<3;k++','k<8;k++')
    prof+='\nstatic u64 cpu30_begin_helper(u32 kind){if(kind!=3+(cpu26Sequence/4)%5)return 0;return cpu26_begin_callback(0);}\nstatic void cpu30_end_helper(u32 kind,u64 t){cpu26_end_callback(kind,0,t); }\n'
    s=s.replace('cpu14Events[600000]','cpu14Events[800000]').replace('cpu14Count>=600000','cpu14Count>=800000')
    return s,prof
