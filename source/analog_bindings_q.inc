/* Analog roles are remapped after a complete physical input sample. Controller
   action handles and the OpenXR binding graph retain their existing lifetime. */
static volatile u32 g_s26qAnalogRequested;
static u8 g_s26qAnalogApplied[2];
static u32 g_s26qAnalogLogs;
static void s26q_set_analog_bindings(u32 mask){
    if(mask<4u)__atomic_store_n(&g_s26qAnalogRequested,mask,__ATOMIC_RELEASE);
}
static i32 s26q_analog_valid(i32 result,u32 active,float value){
    return result>=0&&active&&value>=0.0f&&value<=1.0f;
}
static void s26q_remap_grip_trigger(i32 hand,i32 owned){
    if(hand<0||hand>1)return;
    float grip=g_lastSqueeze[hand],trigger=g_lastTrigger[hand];
    u32 ga=(u32)s26q_analog_valid(g_lastSqueezeResult[hand],g_lastSqueezeActive[hand],grip);
    u32 ta=(u32)s26q_analog_valid(g_lastTriggerResult[hand],g_lastTriggerActive[hand],trigger);
    if(!ga)grip=0.0f;if(!ta)trigger=0.0f;
    u8 wanted=(u8)((__atomic_load_n(&g_s26qAnalogRequested,__ATOMIC_ACQUIRE)>>hand)&1u);
    if(wanted!=g_s26qAnalogApplied[hand]&&!owned&&ga&&ta&&grip<0.05f&&trigger<0.05f){
        g_s26qAnalogApplied[hand]=wanted;
        if(g_s26qAnalogLogs++<16u)ext_Log(">>> S26Q ANALOG BINDING: %s grab=%s, trigger action=%s; released/neutral boundary",hand==0?"L":"R",wanted?"trigger":"grip",wanted?"grip":"trigger");
    }
    if(g_s26qAnalogApplied[hand]){
        i32 result=g_lastSqueezeResult[hand];g_lastSqueezeResult[hand]=g_lastTriggerResult[hand];g_lastTriggerResult[hand]=result;
        g_lastSqueeze[hand]=trigger;g_lastSqueezeActive[hand]=ta;
        g_lastTrigger[hand]=grip;g_lastTriggerActive[hand]=ga;
        /* Grip has no universal capacitive-touch action. Its logical trigger
           touch is derived from the valid analog pressure instead. */
        g_lastTouchResult[hand]=g_lastTriggerResult[hand];g_lastTouchActive[hand]=ga;g_lastTriggerTouch[hand]=(ga&&grip>0.01f)?1u:0u;
    }else{
        g_lastSqueeze[hand]=grip;g_lastSqueezeActive[hand]=ga;
        g_lastTrigger[hand]=trigger;g_lastTriggerActive[hand]=ta;
        if(g_lastTouchResult[hand]<0||!g_lastTouchActive[hand]){g_lastTouchActive[hand]=0;g_lastTriggerTouch[hand]=0;}
    }
}
