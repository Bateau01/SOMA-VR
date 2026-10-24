from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'source/s26n.c';s=p.read_text()
marker='static void h576bo_terminal_pointer_step(void){'
assert s.count(marker)==1 and '#include "terminal_sweep_hr.inc"' not in s
s=s.replace(marker,'#include "terminal_sweep_hr.inc"\n'+marker+'\n    if(h5754h_pause_active()||g_s26hdLaserHand>=0)zero_bytes(g_s26hrTerminalSamples,sizeof(g_s26hrTerminalSamples));')
old='i32 q=h576bo_terminal_tip(h,&tu,&tv,&tp,&tr);if(q<=0)continue;float gap='
new='i32 q=h576bo_terminal_tip(h,&tu,&tv,&tp,&tr);if(q<=0){g_s26hrTerminalSamples[h].valid=0;continue;}if(g_s26hdLaserHand<0&&!h5754h_pause_active())(void)s26hr_terminal_sample(&g_s26hrTerminalSamples[h],&tu,&tv,&tp,tr,g_frameCounter,g_h576boSurfaceTokens,g_s26TerminalImGui,h5755ea_world_units_per_meter());float gap='
assert s.count(old)==1;s=s.replace(old,new)
old='if(!h5730_exact_terminal_state(0,0,0,0)){if(g_h576boPointerDown)'
new='if(!h5730_exact_terminal_state(0,0,0,0)){zero_bytes(g_s26hrTerminalSamples,sizeof(g_s26hrTerminalSamples));if(g_h576boPointerDown)'
assert s.count(old)==1;s=s.replace(old,new)
p.write_text(s)
