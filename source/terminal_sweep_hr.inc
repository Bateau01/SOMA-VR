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
    /* Test the earliest bounded crossing before accepting the final sample.
       A fast angled stroke can start/end beyond an edge but cross a widget. */
    float depth=*p<0?-*p:*p;
    if(previous.valid&&previous.gui==gui&&previous.generation==generation&&
       (u32)(frame-previous.frame)==1u){
        float dp=*p-previous.p,du=*u-previous.u,dv=*v-previous.v,dr=r-previous.r;
        const H576BOTerminalSurface* S=&g_h576boTerminalSurface;
        float uu=h10_dot(S->uSpan,S->uSpan),vv=h10_dot(S->vSpan,S->vSpan),uv=h10_dot(S->uSpan,S->vSpan);
        /* Bound physical travel, not a percentage of differently-sized screens.
           Affine screen coordinates make this relative to a moving handheld. */
        float travel2=dp*dp+du*du*uu+dv*dv*vv+2*du*dv*uv;
        float side=previous.p>=0?1.0f:-1.0f;
        float start=previous.p*side,end=*p*side,slab=r+H576BP_SURFACE_CAPTURE_M;
        if(h9_good(travel2,100)&&travel2>=0&&travel2<=(.15f*metric)*(.15f*metric)&&
           dr*dr<=.0001f&&start>slab&&end<=slab&&start-end>.00001f){
            float t=(start-slab)/(start-end),hitU=previous.u+du*t,hitV=previous.v+dv*t;
            if(hitU>=0&&hitU<=1&&hitV>=0&&hitV<=1){
                *u=hitU;*v=hitV;*p=side*(slab-.00001f);
                sample->sweepSide=side;return 2;
            }
        }
    }
    return *u>=0&&*u<=1&&*v>=0&&*v<=1&&depth<=r+H576BP_SURFACE_CAPTURE_M?1:0;
}
