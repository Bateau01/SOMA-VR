/* Bridge only brief contact dropout; never retain query authority indefinitely. */
typedef struct { u32 step; i32 valid; } S26AMContact;
static S26AMContact g_s26amContact[2];
static i32 s26am_recent_contact(S26AMContact* s,u32 step,i32 contact,i32 queryValid){
    if(!queryValid){s->valid=0;return 0;}
    if(contact){s->step=step;s->valid=1;return 1;}
    if(s->valid&&(u32)(step-s->step)<=2u)return 1;
    s->valid=0;return 0;
}
