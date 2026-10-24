from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'source/accessibility_hd.inc';s=p.read_text()
at=s.index('static void s26hd_grab(')
helper='''/* Observation only: bounded one-line outcomes, no changes to pull policy. */
static u32 g_s26hnOutcomes;
static char g_s26hnName[2][96];
static void s26hn_outcome(i32 hand,const char* reason,float gap,const void* blocker){
    S26HDPull* p=&g_s26hdPull[hand];
    if(!g_s26hdRemoteEnabled||!p->body||g_s26hnOutcomes>=48u)return;
    char blockName[96]={0};void* w=blocker&&p_h14GetUserData?p_h14GetUserData(blocker):0;
    if(w&&h20_mem_readable(w,0x2f0u)&&*(const void**)((u8*)w+0x2e8)==blocker){
        const char* name=*(const char**)((u8*)w+0x10);if(name)h21_copy_ascii(name,blockName,sizeof(blockName));
    }
    g_s26hnOutcomes++;
    ext_Log(">>> S26HN REMOTE OUTCOME #%u hand %d name %s reason %s age %.3f gap %.4f readStage %u raw %p blocker %p blockerName %s held %p pending %u nativeBusy %d state %s",
       g_s26hnOutcomes,hand,g_s26hnName[hand],reason,p->age,gap,g_s26hlReadStage[hand],p->body,blocker,blockName,g_h14GripBody[hand],g_h25PendingValid[hand],s26hk_remote_native_busy(),g_h5729LastClassName);
}
'''
s=s[:at]+helper+s[at:]
a=s.index('static void s26hd_grab(');b=s.index('/* Native readable callbacks',a);part=s[a:b]
part=part.replace('        zero_bytes(p,sizeof(*p));zero_bytes(&g_s26hgFocus','        s26hn_outcome(hand,"state/input ownership",-1,0);zero_bytes(p,sizeof(*p));zero_bytes(&g_s26hgFocus')
part=part.replace('{zero_bytes(p,sizeof(*p));return;}', '{s26hn_outcome(hand,"unspecified",-1,0);zero_bytes(p,sizeof(*p));return;}')
part=part.replace('s26hn_outcome(hand,"unspecified",-1,0)', 's26hn_outcome(hand,!pressed?"grip released":(!(dt>0&&dt<0.1f)?"invalid timestep":(p->age>3.0f?"timeout":"body lifetime")),-1,0)',1)
part=part.replace('s26hn_outcome(hand,"unspecified",-1,0)', 's26hn_outcome(hand,"eligibility changed",-1,0)',1)
part=part.replace('s26hn_outcome(hand,"unspecified",-1,0)', 's26hn_outcome(hand,"closest point failed",-1,0)',1)
part=part.replace('s26hn_outcome(hand,"unspecified",-1,0)', 's26hn_outcome(hand,"obstructed",gap,path.body)',1)
part=part.replace('s26hn_outcome(hand,"unspecified",-1,0)', 's26hn_outcome(hand,"caught",gap,0)',1)
part=part.replace('s26hn_outcome(hand,"unspecified",-1,0)', 's26hn_outcome(hand,"assembly changed",gap,0)',1)
assert 'unspecified' not in part
needle='    p->body=hit.body;p->wrapper=wrapper;p->owner=owner;p->age=0;'
part=part.replace(needle,needle+'''\n    g_s26hnName[hand][0]=0;
    if(h20_mem_readable(wrapper,0x18u)){const char* name=*(const char**)((u8*)wrapper+0x10);if(name)h21_copy_ascii(name,g_s26hnName[hand],sizeof(g_s26hnName[hand]));}''')
s=s[:a]+part+s[b:];p.write_text(s)
# Test fixture substitutes telemetry only; the production pull function remains extracted verbatim.
p=R/'tests/test_accessibility_hd.py';s=p.read_text();s=s.replace("code=header+fn('s26hk_remote_state')", "header+='\\nchar g_s26hnName[2][96];void s26hn_outcome(int,const char*,float,const void*){} int h20_mem_readable(void*,unsigned){return 0;}void h21_copy_ascii(const char*,char*,unsigned){}\\n'\ncode=header+fn('s26hk_remote_state')");p.write_text(s)
