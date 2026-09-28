#ifndef S26AN_CONTACT_DIAGNOSTICS
#define S26AN_CONTACT_DIAGNOSTICS 0
#endif
#if S26AN_CONTACT_DIAGNOSTICS
/* Bounded read-only activation evidence: 12 events per hand, 24 physics steps. */
static u32 g_s26ahEvents[2],g_s26ahStart[2],g_s26ahLast[2],g_s26ahActive[2];
static void s26ah_sample(i32 h,const char* phase){
    if(h<0||h>1||!g_h34HandNewton[h]||!p_h14GetMatrix)return;
    float m[16],v[4]={0},o[4]={0};p_h14GetMatrix(g_h34HandNewton[h],m);
    if(p_h14GetVelocity)p_h14GetVelocity(g_h34HandNewton[h],v);
    if(p_h14GetOmega)p_h14GetOmega(g_h34HandNewton[h],o);
    ext_Log(">>> S26AH ACTIVATION %s event %u step %u phase %s mode %u latch %p near %p held %p visual %u pending %u | root(%+.5f %+.5f %+.5f) target(%+.5f %+.5f %+.5f) v(%+.4f %+.4f %+.4f) omega(%+.4f %+.4f %+.4f) basisX(%+.4f %+.4f %+.4f) basisY(%+.4f %+.4f %+.4f)",h?"R":"L",g_s26ahEvents[h],g_h14PhysicsSteps,phase,g_s26afServoMode[h],g_h574RockerLatchBody[h],g_h5755gjControlNearBody[h],g_h14GripBody[h],(u32)g_h5755deContactVisualActive[h],(u32)g_h545Pending[h],m[12],m[13],m[14],g_h526Target[h][12],g_h526Target[h][13],g_h526Target[h][14],v[0],v[1],v[2],o[0],o[1],o[2],m[0],m[1],m[2],m[4],m[5],m[6]);
}
static i32 s26ah_begin(i32 h,const void* body,i32 rocker){
    if(h<0||h>1||g_s26ahEvents[h]>=12u)return 0;
    ++g_s26ahEvents[h];g_s26ahStart[h]=g_h14PhysicsSteps;g_s26ahLast[h]=g_h14PhysicsSteps;g_s26ahActive[h]=1;
    ext_Log(">>> S26AH ACTIVATION TARGET %s event %u step %u body %p rocker %d",h?"R":"L",g_s26ahEvents[h],g_h14PhysicsSteps,body,rocker);
    s26ah_sample(h,"before-native");return 1;
}
static void s26ah_tick(void){
    for(i32 h=0;h<2;++h){
        if(!g_s26ahActive[h])continue;
        u32 age=g_h14PhysicsSteps-g_s26ahStart[h];
        if(age>24u){g_s26ahActive[h]=0;continue;}
        if(g_s26ahLast[h]==g_h14PhysicsSteps)continue;
        g_s26ahLast[h]=g_h14PhysicsSteps;
        if(age<=4u||(age%2u)==0u)s26ah_sample(h,"post-physics");
    }
}

#else
static i32 s26ah_begin(i32 h,const void* body,i32 rocker){(void)h;(void)body;(void)rocker;return 0;}
static void s26ah_sample(i32 h,const char* phase){(void)h;(void)phase;}
static void s26ah_tick(void){}
#endif
