/* Direct fingertip only. Retain an otherwise unconsumed contact edge briefly
   while the tip settles from blank space onto a native widget. Consumption is
   read before cImGui::End clears actionUsed[MouseLeft] (+4f69).
   Verified native button and ActionTriggered paths both mark this field.
   A custom canvas/drag consuming the initial contact is never retriggered. */
typedef struct { float remaining; } S26HSTouch;
static S26HSTouch g_s26hsTouch;
static i32 s26hs_touch_edge(S26HSTouch* s,i32 kind,i32 direct,float dt){
    if(!direct || kind==2 || kind==4 || kind==0){s->remaining=0;return kind==1;}
    if(kind==1){s->remaining=.35f;return 1;}
    if(kind!=3 || !(dt>=0.0f && dt<.1f)){s->remaining=0;return 0;}
    s->remaining-=dt;
    if(s->remaining<=0){s->remaining=0;return 0;}
    return 1;
}
static void s26hs_touch_consumed(S26HSTouch* s,i32 used){if(used)s->remaining=0;}
