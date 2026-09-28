/* Preserve existing control gains through <=4 missed physics steps.
   No body dereference, collision query, target edit, or activation authority. */
typedef struct { const void* body; const void* handBody; u32 last; i32 valid; } S26AIHold;
static S26AIHold g_s26aiHold[2];
static i32 s26ai_control_hold(i32 h,const void* body,const void* handBody,u32 step,i32 signal,i32 reset){
    S26AIHold* s=&g_s26aiHold[h];
    if(reset||!body||!handBody){s->valid=0;s->body=0;s->handBody=0;return 0;}
    if(s->body!=body||s->handBody!=handBody){s->valid=0;s->body=body;s->handBody=handBody;}
    if(signal){s->last=step;s->valid=1;return 1;}
    if(s->valid&&(u32)(step-s->last)<=4u)return 1;
    s->valid=0;return 0;
}
