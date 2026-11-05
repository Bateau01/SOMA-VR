/* Direct touch hit sampling only. No hand-pose or physics interpolation. */
static i32 s26hr_terminal_sample(S26HRTerminalSample* sample,float* u,float* v,float* p,float r,
                                u32 frame,u32 generation,const void* gui,float metric){
    if(!sample||!u||!v||!p)return 0;
    if(!gui||!h9_good(*u,8)||!h9_good(*v,8)||!h9_good(*p,10)||
       !h9_good(r,1)||r<0||!h9_good(metric,10)||metric<=0){sample->valid=0;sample->sweepSide=0;return -1;}
    S26HRTerminalSample previous=*sample;
    if(previous.gui!=gui||previous.generation!=generation)sample->sweepSide=0;
    if(sample->sweepSide!=0){
        if(*p*sample->sweepSide>r+H576BO_FRONT_RELEASE_SKIN_M)sample->sweepSide=0;
        else return -1; // A swept press must withdraw to its original side.
    }
    sample->u=*u;sample->v=*v;sample->p=*p;sample->r=r;
    sample->frame=frame;sample->generation=generation;sample->gui=gui;sample->valid=1;
    float depth=*p<0?-*p:*p;
    if(*u>=0&&*u<=1&&*v>=0&&*v<=1&&depth<=r+H576BP_SURFACE_CAPTURE_M)return 1;
    if(!previous.valid||previous.gui!=gui||previous.generation!=generation||
       (u32)(frame-previous.frame)>2u||previous.u<0||previous.u>1||previous.v<0||previous.v>1||
       *u<0||*u>1||*v<0||*v>1)return 0;
    float dp=*p-previous.p,du=*u-previous.u,dv=*v-previous.v,dr=r-previous.r;
    if(dp*dp>(.15f*metric)*(.15f*metric)||du*du+dv*dv>.1225f||dr*dr>.0001f)return 0;
    float side=previous.p>=0?1.0f:-1.0f;
    float start=previous.p*side,end=*p*side,slab=r+H576BP_SURFACE_CAPTURE_M;
    if(start<=slab||end>=slab||start-end<.00001f)return 0;
    float t=(start-slab)/(start-end);
    *u=previous.u+du*t;*v=previous.v+dv*t;
    // Choose a point just inside the existing slab to avoid roundoff at equality.
    *p=side*(slab-.00001f);sample->sweepSide=side;return 2;
}
