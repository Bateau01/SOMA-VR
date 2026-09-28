from pathlib import Path
import re
p=Path(__file__).resolve().with_name('s26n.c')
s=p.read_text()
def editfn(name, transform):
    global s
    m=re.search(r'^static [^\n]*\b'+name+r'\([^;\n]*\)\s*\{',s,re.M)
    assert m,name
    start=m.start(); brace=s.index('{',m.start()); end=brace+1; depth=1
    while depth:
        if s[end]=='{': depth+=1
        elif s[end]=='}': depth-=1
        end+=1
    old=s[start:end]; new=transform(old); assert new!=old,name
    s=s[:start]+new+s[end:]
metric='h5755ea_world_units_per_meter()'
for name in ['h20_skin_vertex_local','h14_finger_tip_world','s26q_finger_points_pose']:
    editfn(name,lambda x:x.replace('*0.01f','*(0.01f*'+metric+')'))
# Render-only basis scaling. Controller/physics transforms stay orthonormal.
s=s.replace('h576bt_probe_rocker_render_tip(hand,M);h10_matmul', 'h576bt_probe_rocker_render_tip(hand,M);s26bb_scale_visual_basis(M);h10_matmul',1)
s=s.replace('    for(i32 r=0;r<4;++r)for(i32 c=0;c<4;++c)hm[r*4+c]=M[c*4+r];','    s26bb_scale_visual_basis(M);\n    for(i32 r=0;r<4;++r)for(i32 c=0;c<4;++c)hm[r*4+c]=M[c*4+r];',1)
point=s.index('static void h5755ee_apply_xr_stereo_scale')
s=s[:point]+'''/* S26BB: compensate only rendered geometry, never rigid tracking frames. */
static void s26bb_scale_visual_basis(float* m){
    float metric=h5755ea_world_units_per_meter();
    for(i32 c=0;c<3;++c)for(i32 r=0;r<3;++r)m[c*4+r]*=metric;
}
static void s26bb_apply_world_scale(void);
'''+s[point:]
def lengths(x,tokens):
    for token in tokens:
        x=re.sub(r'(?<![\w.])'+re.escape(token)+r'(?![\w.])','('+token+'*'+metric+')',x)
    return x
editfn('h504_fit_palm_boxes',lambda x:lengths(x,['0.035f','0.025f','H511_PALM_INSET','H511_PALM_OVERLAP','0.0045f','0.13f']))
editfn('s26q_link_frame_pose',lambda x:lengths(x,['0.0045f']))
editfn('h519_nearest_link',lambda x:lengths(x,['H519_FIT_MAX_NEAR']))
editfn('h519_fit_finger_shell',lambda x:lengths(x,['H519_OFFSET_MAX','H519_RADIUS_MARGIN','H519_RADIUS_MAX']).replace('nominal[f]','(nominal[f]*'+metric+')'))
editfn('h572_index_skin_radius',lambda x:lengths(x,['0.0080f','0.004f','H519_RADIUS_MAX','0.0065f']))
editfn('h557_ensure_guard_shapes',lambda x:lengths(x,['H557_GUARD_MARGIN_M']))
# Broad query bounds must grow along with the exact hand geometry.
match=re.search(r'^static [^\n]*\b(\w+)\([^\n]*\)\s*\{\n[^{}]*?// complete finger',s,re.M)
idx=s.index('float r=0.014f,v0=pt[d][a]-r')
start=s.rfind('\nstatic ',0,idx)+1
name=re.search(r'\b(\w+)\(',s[start:]).group(1)
editfn(name,lambda x:lengths(x,['0.014f','H523_BROAD_MARGIN','0.06f','0.45f']))
# Apply after Newton returns, using the already-established safe teardown point.
# Preserve CPU rig and GL allocations; this is a geometry change, not a skin swap.
src=s[s.index('static void h5748_clear_family_geometry_cache(i32 hand){'):s.index('static i32 h5748_family_assets_exist')]
retire=src.replace('h5748_clear_family_geometry_cache','s26bb_retire_scaled_geometry',1)
a=retire.index('    if(g_h20CpuVerts[hand])')
b=retire.index('    s26q_roots_reset(hand)',a)
retire=retire[:a]+retire[b:]
s=s.replace('static i32 h5748_family_assets_exist',retire+'static i32 h5748_family_assets_exist',1)
s=s.replace('h5748_post_physics_switch();h482_camera_guard_step();','h5748_post_physics_switch();s26bb_apply_world_scale();h482_camera_guard_step();',1)
s=s.replace('    s26bb_apply_world_scale();\n    g_s26qWaistValid','    g_s26qWaistValid',1)
editfn('s26bb_apply_world_scale',lambda x:x.replace('g_h576bfMapTransitionActive||','g_h5748SwitchStage||g_h576bfMapTransitionActive||').replace('    g_h5755euWorldScale=metric;','    s26bb_retire_scaled_geometry(0);s26bb_retire_scaled_geometry(1);\n    g_h5755euWorldScale=metric;').replace('hand mesh/collision dimensions unchanged; applied between frames','hand visual and collision geometry compensated together; applied after physics'))
s=s.replace('// Apply once at a frame boundary. Do not change a held object\'s controller frame.','// Apply after NewtonUpdate returns. Do not change a held object\'s controller frame.')
p.write_text(s)
print('Applied staged hand-size compensation; no installed files changed.')
