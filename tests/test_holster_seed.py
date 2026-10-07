"""Verify the production pose seed is restricted to its hand and owning thread."""
from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1];B=R/'build';s=(R/'source/s26n.c').read_text()
a=s.index('static u32 g_s26efHolsterSeed[2]');b=s.index('static float g_s26efHolsterCurl',a)
code='typedef unsigned u32;typedef int i32;\n'+s[a:b]+'''
static u32 tid=101;static u32 thread(void){return tid;}
int main(void){
 if(s26ef_holster_seed_active(0)||s26ef_holster_seed_active(1))return 1;
 p_s26efGripThread=thread;g_s26efHolsterSeed[0]=101;
 if(!s26ef_holster_seed_active(0)||s26ef_holster_seed_active(1))return 2;
 tid=202;if(s26ef_holster_seed_active(0))return 3;
 g_s26efHolsterSeed[1]=202;if(!s26ef_holster_seed_active(1))return 4;
 g_s26efHolsterSeed[0]=g_s26efHolsterSeed[1]=0;
 if(s26ef_holster_seed_active(0)||s26ef_holster_seed_active(1))return 5;
 return 0;
}
'''
p=B/'holster_seed_test.c';p.write_text(code);exe=B/'holster_seed_test.exe'
subprocess.run([sys.argv[1],'cc','-target','x86_64-windows-gnu','-O2',str(p),'-o',str(exe)],check=True)
subprocess.run([str(exe)],check=True);print('PASS: pose seed is isolated by hand and thread, then cleared')
