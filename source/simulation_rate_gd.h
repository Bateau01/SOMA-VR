/* Startup-only experiment. Durations use ticks at the active gameplay rate;
   contact identities and physics-boundary fences still use real step numbers. */
static unsigned g_s26gdRateMultiplier=1u;
static unsigned s26gd_steps(unsigned at60){return at60*g_s26gdRateMultiplier;}
static float s26gd_tick_amount(float at60){return at60/(float)g_s26gdRateMultiplier;}
static float s26gd_alpha(float at60){
    if(g_s26gdRateMultiplier!=2u)return at60;
    float v=1.0f-at60;
    __asm__("sqrtss %0,%0" : "+x"(v));
    return 1.0f-v;
}
static void s26gd_install(void);
static float s26gd_half_damping(float perStep){
    /* Stable form of 1-sqrt(1-d), including very small damping values. */
    if(!(perStep>0.0f && perStep<1.0f))return perStep;
    float v=1.0f-perStep;__asm__("sqrtss %0,%0" : "+x"(v));
    return perStep/(1.0f+v);
}

