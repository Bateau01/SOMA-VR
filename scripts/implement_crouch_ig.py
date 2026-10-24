from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'source/s26n.c';s=p.read_text()
start=s.index('    if(cq&&ac){if(h5711_resolve_crouch_action_id())')
end=s.index('\n    if(jq){',start)
block=s[start:end]
assert block.endswith('g_h5711CrouchPending=0;}')
(R/'audit/baseline_dispatch_if.txt').write_text(block)
new='''static void s26ig_dispatch_crouch_pre(float timestep){
    if(!g_h5711CrouchPending)return;
    if(g_h576bfMapTransitionActive||g_h5755bhPresentationState!=H5755BH_GAMEPLAY_VR||
       g_h5755asUiIslandActive||g_h5755asResumeClassifyActive||g_h5755azExitPending||
       g_h5755bbTitlePresentationLatch)return;
    void* pi=0;PFN_H5711_PlayerExit ex=0;PFN_H5711_PlayerAction ac=0;
    if(!h5711_native_player_callbacks(&pi,&ex,&ac)||!ac){
        g_h5711CrouchPending=0;g_h5711NativeRejects++;return;
    }
    /* Consume before native dispatch: subsequent Newton substeps cannot replay it.
       Native OnAction still owns crouch permissions and character collision. */
    g_h5711CrouchPending=0;
'''+block.replace('if(cq&&ac)', 'if(ac)').replace('float dt=g_h14LastPhysicsDt;', 'float dt=timestep;')+'''
}

'''
s=s[:start]+s[end:]
s=s.replace('u32 cq=g_h5711CrouchPending,bq=', 'u32 bq=',1).replace('if(!cq&&!bq&&!jq&&!sq)', 'if(!bq&&!jq&&!sq)',1).replace('if(!cq&&!bq&&!jq)', 'if(!bq&&!jq)',1)
s=s.replace('g_h5711CrouchPending=0;g_h5711BackPending=0;', 'g_h5711BackPending=0;',1)
s=s.replace('static void h5711_dispatch_semantic_actions(void){',new+'static void h5711_dispatch_semantic_actions(void){',1)
needle='h5729_state_boundary_observe("pre");h5749a_refresh_gui_state();h14_physics_step(world,timestep);'
assert needle in s
s=s.replace(needle,'h5729_state_boundary_observe("pre");h5749a_refresh_gui_state();s26ig_dispatch_crouch_pre(timestep);h14_physics_step(world,timestep);',1)
s=s.replace('1.0.9-S26IF-AUDIT','1.0.9-S26IG')
p.write_text(s)
