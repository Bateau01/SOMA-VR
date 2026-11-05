from pathlib import Path
def augment(s,prof):
    r=Path(__file__).resolve().parents[1]
    prof='static void cpu32_reset(void);static void cpu32_pair(u64,u64,const void*,const void*,i32);static void cpu32_after(u64,u64);\n'+prof+'\n'+(r/'tests/cpu32_pairs.inc').read_text()
    needle='cpu26Invalid=0;__atomic_store_n(&cpu26Active,1,__ATOMIC_RELEASE);'
    assert prof.count(needle)==1
    prof=prof.replace(needle,'cpu32_reset();'+needle)
    needle='cpu26_after(cpu6NT0,cpu6NT1);'
    assert s.count(needle)==1
    s=s.replace(needle,'u32 cpu32Sampled=cpu26Active;'+needle+'if(cpu32Sampled)cpu32_after(cpu6NT0,cpu6NT1);')
    needle='cpu26_end_callback(2,thread,t);return result;'
    assert s.count(needle)==1
    # End timestamp is shared with pair accounting to avoid a third clock read.
    replacement='if(t){u64 end=0;cpuCounter(&end);CPU26Slot*z=&cpu26Slots[t&63][2];u64 dt=end-(t>>6);z->calls++;z->ticks+=dt;if(dt>z->max)z->max=dt;cpu32_pair(t,end,a,b,result);}return result;'
    s=s.replace(needle,replacement)
    return s,prof
