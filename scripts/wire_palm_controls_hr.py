from pathlib import Path
r=Path.cwd();p=r/'source/s26n.c';s=p.read_text().replace('used,active,blocked,frontAxis;','used,active,blocked,frontAxis,handMask;',1);s=s.replace('    s26y_rearm();','    s26y_rearm();\n    s26hr_palm_controls();',1);p.write_text(s)
p=r/'source/rocker_y.inc';s=p.read_text();s=s.replace('static void s26y_rearm(void){','''static i32 s26hr_control_palm(i32 h,float* center,float* direction){
    float pos[3],m[16];if(!visual_pose_valid(h)||!h14_hand_pose_raw(h,pos,m)||!h15_grip_center_world(h,m,center))return 0;
    for(i32 a=0;a<3;a++)direction[a]=-m[8+a];return h10_norm3(direction);
}
static void s26y_rearm(void){''',1)
s=s.replace('if(clear)r->blocked=0;','''if(clear)for(i32 h=0;h<2;h++){
            float palm[3],dir[3],gap,cp[3];
            if(!s26hr_control_palm(h,palm,dir)||!s26eq_return_point(r->raw,palm,&gap,cp)||gap<=.055f){clear=0;break;}
        }
        if(clear){r->blocked=0;r->handMask=0;}''',1)
s=s.replace('static i32 s26y_near(i32 hand,void* wrapper,void* owner,const float* tip,const float* dir,i32 len){','static i32 s26hr_control_contact(i32 hand,void* wrapper,void* owner,const float* tip,const float* dir,i32 len,float palmRadius){',1)
s=s.replace('S26YRocker* r=&g_s26yRocker[i];\n    if(!r->active','''S26YRocker* r=&g_s26yRocker[i];
    for(i32 k=0;k<g_s26yCount;k++)if(g_s26yRocker[k].used&&g_s26yRocker[k].blocked&&
        (g_s26yRocker[k].handMask&(1<<hand)))return 1;
    if(!r->active''',1)
s=s.replace('float skin=h572_index_skin_gap(hand,len,gap);','float skin=palmRadius>0?gap-palmRadius:h572_index_skin_gap(hand,len,gap);',1)
s=s.replace('r->blocked=1;r->raw=body;r->wrapper=wrapper;','r->blocked=1;r->handMask=1<<hand;r->raw=body;r->wrapper=wrapper;',1)
idx=s.index('\nstatic void s26z_retire')
s=s[:idx]+'''
static i32 s26y_near(i32 hand,void* wrapper,void* owner,const float* tip,const float* dir,i32 len){
    return s26hr_control_contact(hand,wrapper,owner,tip,dir,len,0);
}
// One first-hit ray per free palm, only near a registered push control. Other
// surfaces cannot become candidates; callbacks still use the captured main body.
static void s26hr_palm_controls(void){
    if(!g_s26yCount||!s26y_gate()||h5754h_pause_active()||g_s26CutsceneHandsHidden||g_lastSyncResult!=0)return;
    for(i32 h=0;h<2;h++){
        if(g_h14GripBody[h]||g_h482AuthoredDragActive[h])continue;
        float palm[3],dir[3];if(!s26hr_control_palm(h,palm,dir))continue;
        i32 nearby=0;
        for(i32 i=0;i<g_s26yCount;i++){
            S26YRocker* r=&g_s26yRocker[i];if(!r->used||!r->active||!r->mainWrapper||!h20_mem_readable(r->mainWrapper,0x2f0u))continue;
            if(*(const void**)((u8*)r->mainWrapper+0x2e8)!=r->mainRaw||*(void**)((u8*)r->mainWrapper+0x2c0)!=r->owner)continue;
            float m[16];p_h14GetMatrix(r->mainRaw,m);float x=palm[0]-m[12],y=palm[1]-m[13],z=palm[2]-m[14];
            if(x*x+y*y+z*z<.35f*.35f){nearby=1;break;}
        }
        if(!nearby)continue;
        PFN_H37_GetClosestEntity fn=0;void* helper=h37_map_helper(&fn);if(!helper||!fn)continue;
        float start[3];for(i32 a=0;a<3;a++)start[a]=palm[a]-dir[a]*.025f;
        float dist=999;void* wrapper=0;void* owner=0;
        if(!fn(helper,start,dir,.065f,0,0,&dist,&wrapper,&owner)||dist<0||dist>.065f||!h37_native_wrapper_matches_entity(wrapper,owner))continue;
        s26hr_control_contact(h,wrapper,owner,palm,dir,0,.020f);
    }
}
''' +s[idx:];p.write_text(s)
p=r/'runtime/script/props/Prop_Button.hps';s=p.read_text();s=s.replace('file=="lightswitch_button.ent");','file=="lightswitch_button.ent" || file=="panel_slidedoor_medium.ent" || file=="panel_slidedoor_medium_rigid.ent" || file=="panel_slidedoor_medium_rusty.ent");',1)
s=s.replace('(body is paddle) ? "A" : "R"','(body is paddle || file=="panel_slidedoor_medium.ent" || file=="panel_slidedoor_medium_rigid.ent" || file=="panel_slidedoor_medium_rusty.ent") ? "A" : "R"',1);p.write_text(s)
