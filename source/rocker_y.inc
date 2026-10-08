/* S26Y EXPERIMENT: only script-identified rocker assets; no general icon13 override. */
static i32 s26y_gate(void){return g_h576mScriptRuntimePublished==1&&p2_xr_on()&&p2_xr_running()&&!g_h576bfMapTransitionActive&&g_h5753cAuthorityEnabled;}
static void s26y_reset(void){s26dd_forget_button_contacts();zero_bytes(g_s26yRocker,sizeof(g_s26yRocker));g_s26yCount=0;g_s26yCapture=0;g_s26yMainWrapper=0;g_s26yMainRaw=0;g_s26yOwner=0;}
static i32 s26y_id(const H5730TString* text,u32* id){
    char value[16];if(!h5748n_copy_tstring((void*)text,value,sizeof(value))||!value[0])return 0;
    u32 n=0;for(u32 i=0;value[i];++i){u32 d=(u32)(value[i]-'0');if(d>9u||n>214748364u||(n==214748364u&&d>7u))return 0;n=n*10u+d;}*id=n;return 1;
}
static i32 s26y_slot(u32 id){for(i32 i=0;i<g_s26yCount;++i)if(g_s26yRocker[i].used&&g_s26yRocker[i].id==id)return i;return -1;}
static i32 s26y_body_slot(const void* body){
    if(!g_s26yCount||!s26y_gate()||!body||!p_h14GetUserData)return -1;
    void* w=p_h14GetUserData(body);if(!w||!h20_mem_readable(w,0x2f0u)||*(const void**)((u8*)w+0x2e8)!=body)return -1;
    i32 i=s26y_slot(*(u32*)((u8*)w+0x3c));
    if(i<0||*(void**)((u8*)w+0x2c0)!=g_s26yRocker[i].owner)return -1;
    return i;
}
static i32 s26y_rocker_body(const void* body){return s26y_body_slot(body)>=0;}
static i32 s26y_token(const H5730TString* text,const H5730TString* cmd){
    u32 id=0;
    if(h5748t_sso_eq(cmd,"U",1u)){if(!s26y_id(text,&id))return 0;i32 i=s26y_slot(id);if(i>=0)zero_bytes(&g_s26yRocker[i],sizeof(g_s26yRocker[i]));return 1;}
    if(!s26y_gate())return 0;
    if(h5748t_sso_eq(cmd,"C",1u)){g_s26yCapture=1;g_s26yMainWrapper=0;g_s26yMainRaw=0;g_s26yOwner=0;return 1;}
    if(h5748t_sso_eq(cmd,"D",1u)){g_s26yCapture=0;return g_s26yMainWrapper&&g_s26yMainRaw&&g_s26yOwner;}
    i32 active=h5748t_sso_eq(cmd,"A",1u);if(!active&&!h5748t_sso_eq(cmd,"R",1u))return 0;
    if(!s26y_id(text,&id)||!g_s26yMainWrapper||!g_s26yOwner||!h20_mem_readable(g_s26yMainWrapper,0x2f0u)||*(const void**)((u8*)g_s26yMainWrapper+0x2e8)!=g_s26yMainRaw)return 0;
    i32 i=s26y_slot(id);if(i<0){for(i32 j=0;j<64;++j)if(!g_s26yRocker[j].used){i=j;if(j>=g_s26yCount)g_s26yCount=j+1;break;}}
    if(i<0)return 0;
    S26YRocker* r=&g_s26yRocker[i];if(r->owner!=g_s26yOwner)zero_bytes(r,sizeof(*r));
    r->used=1;r->id=id;r->active=active;r->owner=g_s26yOwner;r->mainWrapper=g_s26yMainWrapper;r->mainRaw=g_s26yMainRaw;
    for(i32 h=0;h<2;++h)s26z_retire_rocker_hand(h);
    return 1;
}
static i32 s26y_tip(i32 h,float* tip,i32* length){
    float pos[3],m[16],pts[5][3],c[4];if(!visual_pose_valid(h)||!h14_hand_pose_raw(h,pos,m))return 0;
    for(i32 j=0;j<4;++j)c[j]=s26q_raw_joint(h,1,j);
    if(!h18_finger_points_world(h,1,c,m,pts,length)||*length<1||*length>4)return 0;
    for(i32 j=0;j<3;++j)tip[j]=pts[*length][j];return 1;
}
static void s26y_rearm(void){
    if(!g_s26yCount||!s26y_gate()||h5754h_pause_active()||g_lastSyncResult!=0)return;
    float tip[2][3];i32 len[2],valid[2]={0,0},sampled=0;
    for(i32 i=0;i<g_s26yCount;++i){S26YRocker* r=&g_s26yRocker[i];if(!r->used||!r->blocked||!r->raw)continue;
        if(!sampled){for(i32 h=0;h<2;++h)valid[h]=s26y_tip(h,tip[h],&len[h]);sampled=1;}
        if(!r->wrapper||!h20_mem_readable(r->wrapper,0x2f0u)||*(const void**)((u8*)r->wrapper+0x2e8)!=r->raw||*(u32*)((u8*)r->wrapper+0x3c)!=r->id)continue;
        i32 clear=1;for(i32 h=0;h<2;++h){float gap=0,cp[3];if(!valid[h]||!h14_point_to_body(r->raw,tip[h],&gap,cp)||h572_index_skin_gap(h,len[h],gap)<=.03f){clear=0;break;}}
        if(clear)r->blocked=0;
    }
}
static i32 s26y_near_gate(float skin,float front,float alignment){
    return skin>=-.002f&&skin<=.010f&&front>=.55f&&alignment<=-.15f;
}
/* Called only for the first exact entity hit by the existing fingertip ray. */
static i32 s26y_near(i32 hand,void* wrapper,void* owner,const float* tip,const float* dir,i32 len){
    if(!wrapper||!h20_mem_readable(wrapper,0x2f0u))return 0;
    const void* body=*(const void**)((u8*)wrapper+0x2e8);i32 i=s26y_body_slot(body);if(i<0)return 0;
    S26YRocker* r=&g_s26yRocker[i];
    if(!r->active||r->blocked||owner!=r->owner||h5754h_pause_active()||g_lastSyncResult!=0||!p_h14GetMatrix)return 1;
    float gap=999,cp[3],m[16];if(!h14_point_to_body(body,tip,&gap,cp))return 1;
    float normal[3]={tip[0]-cp[0],tip[1]-cp[1],tip[2]-cp[2]};if(!h10_norm3(normal))return 1;
    p_h14GetMatrix(body,m);float front[3]={m[8],m[9],m[10]};if(!h10_norm3(front))return 1;
    float skin=h572_index_skin_gap(hand,len,gap);if(!s26y_near_gate(skin,h10_dot(normal,front),h10_dot(dir,normal)))return 1;s26fc_hint_near(21);
    // Capture is the authored GetMainBody wrapper, even when the ray hits the moving paddle.
    if(!r->mainWrapper||!h20_mem_readable(r->mainWrapper,0x2f0u)||*(const void**)((u8*)r->mainWrapper+0x2e8)!=r->mainRaw||*(void**)((u8*)r->mainWrapper+0x2c0)!=owner)return 1;
    i32 icon=-1;const void* raw=0;void* can=0;void* on=0;
    g_s26yCalling=1;i32 usable=h483_surface_target_info(r->mainWrapper,owner,&icon,&raw,&can,&on);g_s26yCalling=0;
    if(!usable||icon!=H482_POKE_SWITCH_ICON||raw!=r->mainRaw)return 1;
    r->blocked=1;r->raw=body;r->wrapper=wrapper; // Both hands share this one-shot latch; it never anchors a hand.
    H25TString empty;zero_bytes(&empty,sizeof(empty));empty.capacity=15u;
    i32 traceAH=s26ah_begin(hand,body,1);u64 result=((PFN_H25_OnInteract)on)(owner,0,r->mainWrapper,cp,&empty);if(traceAH)s26ah_sample(hand,"after-native");
    if(result&0xffu)h576ac_queue_haptic(hand,H576AC_HAPTIC_CONFIRM);
    if(g_s26yLogs<48u){g_s26yLogs++;ext_Log(">>> S26Y EXPERIMENTAL ROCKER NEAR: hand %d skin-gap %.4f m native result %u; withdraw both fingertips >3cm to rearm; no hand contact latch",hand,skin,(u32)(result&0xffu));}
    return 1;
}

static void s26z_retire_rocker_hand(i32 h){
    if(h<0||h>1)return;
    if(s26y_rocker_body(g_h574RockerLatchBody[h])){
        g_h574RockerLatchBody[h]=0;g_h574RockerClearStreak[h]=0;g_h574RockerPassBody[h]=0;
        __atomic_store_n(&g_h5755deContactVisualActive[h],0u,__ATOMIC_RELEASE);
        h48_poke_clear(h);
    }
    if(s26y_rocker_body(g_h5755gjControlNearBody[h])){g_h5755gjControlNearBody[h]=0;g_h5755gjControlNearStep[h]=0;}
    if(s26y_rocker_body(g_h576buRockerNormalBody[h])){g_h576buRockerNormalBody[h]=0;g_h576buRockerNormalValid[h]=0;}
}
