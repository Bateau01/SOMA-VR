"""Extracted production GUI router with instrumented native calls; not a renderer test."""
from pathlib import Path
import re,sys,subprocess,json
R=Path(__file__).resolve().parents[1];s=(R/'source/s26n.c').read_text()
a=s.index('static void __attribute__((ms_abi)) h5755ez_guiset_draw_detour(');b=s.index('static void __attribute__((ms_abi)) h5755fh_render_objects_detour',a)
f=s[a:b]
ptrs={'g_s26hrHintSet','g_h5755duSubtitleSet','g_h5755feGameHud','g_h5755feRenderContext'}
globals=set(re.findall(r'\bg_\w+',f));decl='\n'.join(('void* ' if v in ptrs else 'unsigned long long ')+v+';' for v in sorted(globals))
code=r"""
#include <cstdio>
#include <cstdlib>
#include <cstring>
using u8=unsigned char;using u64=unsigned long long;
#define ext_Log(...) ((void)0)
#define CHECK(x) do{checks++;if(!(x)){printf("FAIL %d: %s\n",__LINE__,#x);exit(1);}}while(0)
int checks,active=1,cacheOK=1,prepareOK=1,poseOK=1,hintDraws,subDraws,hudDraws,otherDraws,poses;
unsigned char hint[0x200],sub[0x200],hud[0x200],other[0x200],eye[0x200],aux[0x200];
"""+decl+r"""
bool h20_mem_readable(const void*p,int){return p!=nullptr;}
bool h5755dg_gameplay_vr(){return active;}
bool h5755fh_main_eye_cache_eligible(void*p){return p==eye;}
bool h5755fe_capture_final_surface_state(void*,void*p){if(cacheOK)g_h5755feRenderContext=p;return cacheOK;}
bool h5755fe_prepare_cached_perspective(){return prepareOK;}
void h5755fm_refresh_subtitle_final_translation(void*,void*){}
bool s26hr_hint_pose(void*,void*){poses++;return poseOK;}
void draw(void*s,void*){if(s==hint)hintDraws++;else if(s==sub)subDraws++;else if(s==hud)hudDraws++;else otherDraws++;}
void(*o_h5755ezGuiSetDraw)(void*,void*)=draw;
"""+f+r"""
void reset(){g_s26hrHintSet=hint;g_h5755duSubtitleSet=sub;g_h5755feGameHud=hud;g_s26hrHintReplayPending=0;
 hintDraws=subDraws=hudDraws=otherDraws=poses=0;active=cacheOK=prepareOK=poseOK=1;*(u64*)(hint+0xe0)=1;*(u64*)(sub+0xe0)=0;}
int main(){
 reset();h5755ez_guiset_draw_detour(hint,eye);CHECK(hintDraws==0&&g_s26hrHintReplayPending);
 h5755ez_guiset_draw_detour(hint,aux);CHECK(hintDraws==0&&g_s26hrHintReplayPending);
 h5755ez_guiset_draw_detour(hud,eye);CHECK(hintDraws==1&&hudDraws==1&&poses==1&&!g_s26hrHintReplayPending);
 h5755ez_guiset_draw_detour(hud,eye);CHECK(hintDraws==1&&hudDraws==2);
 // Next eye obtains its own traversal and pose; no shared once-per-frame gate.
 h5755ez_guiset_draw_detour(hint,eye);h5755ez_guiset_draw_detour(hud,eye);CHECK(hintDraws==2&&poses==2);
 reset();active=0;h5755ez_guiset_draw_detour(hint,eye);h5755ez_guiset_draw_detour(hud,eye);CHECK(hintDraws==0&&!g_s26hrHintReplayPending);
 reset();cacheOK=0;h5755ez_guiset_draw_detour(hint,eye);h5755ez_guiset_draw_detour(hud,eye);CHECK(hintDraws==1&&!g_s26hrHintReplayPending);
 reset();h5755ez_guiset_draw_detour(hint,eye);active=0;h5755ez_guiset_draw_detour(hud,eye);CHECK(hintDraws==0&&!g_s26hrHintReplayPending);
 reset();h5755ez_guiset_draw_detour(other,eye);CHECK(otherDraws==1&&hintDraws==0);
 reset();*(u64*)(sub+0xe0)=1;h5755ez_guiset_draw_detour(sub,eye);h5755ez_guiset_draw_detour(hint,eye);h5755ez_guiset_draw_detour(hud,eye);CHECK(subDraws==1&&hintDraws==1&&hudDraws==1);
 CHECK(!g_h5755fhFinalReplayScope);
 printf("PASS %d production router assertions: both-eye traversals, auxiliary rejection, independent subtitles, pause and fallback\n",checks);
}
"""
p=R/'build/hint_route_hr.cpp';p.write_text(code)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
v=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True)
(R/'docs/v109-evidence/hint_route_hr.json').write_text(json.dumps({'exit':v.returncode,'output':v.stdout+v.stderr,'scope':__doc__},indent=2));print(v.stdout+v.stderr);raise SystemExit(v.returncode)
