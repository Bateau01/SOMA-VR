/* Runtime LOCAL-origin changes. Keep the application's tracking frame stable
   by changing its reference-space offset before locating this frame's views.
   No game camera, body, cached hand pose or raw OpenXR view is rewritten. */
typedef struct { i32 type;const void* next;Handle session;i32 referenceSpaceType;
    i64 changeTime;u32 poseValid;XrPosef poseInPreviousSpace; } S26QRefEvent;
typedef struct { i32 type;const void* next;i32 referenceSpaceType;XrPosef poseInReferenceSpace; } S26QRefInfo;
typedef struct { i32 type;const void* next;i32 viewConfigurationType;i64 displayTime;Handle space; } S26QLocateInfo;
_Static_assert(sizeof(S26QRefEvent)==72,"reference event ABI");
_Static_assert(sizeof(S26QRefInfo)==48,"reference create ABI");
_Static_assert(sizeof(S26QLocateInfo)==40,"reference locate ABI");
typedef i32 (__attribute__((ms_abi)) *S26QPoll)(Handle,void*);
typedef i32 (__attribute__((ms_abi)) *S26QLocate)(Handle,const S26QLocateInfo*,void*,u32,u32*,void*);
typedef i32 (__attribute__((ms_abi)) *S26QCreateRef)(Handle,const S26QRefInfo*,Handle*);
typedef i32 (__attribute__((ms_abi)) *S26QDestroyRef)(Handle);
static S26QPoll g_s26qRefPoll;
static S26QLocate g_s26qRefLocate;
static S26QCreateRef g_s26qRefCreate;
static S26QDestroyRef g_s26qRefDestroy;
static void* g_s26qRefSelf;
static Handle g_s26qRefInstance,g_s26qRefSession,g_s26qRefSpace;
static XrPosef g_s26qRefOffset;
static S26QRefEvent g_s26qRefQueue[8];
static u32 g_s26qRefCount,g_s26qRefLogs,g_s26qRefDisabled;
static void s26q_ref_end(Handle session){
    if(session!=g_s26qRefSession)return;
    /* Session destruction owns all child spaces, including the active one.
       Clear identity before the runtime can reuse a session/space handle. */
    g_s26qRefSession=0;g_s26qRefSpace=0;g_s26qRefSelf=0;g_s26qRefCount=0;
}
static void s26q_ref_log(const char* reason){
    if(g_s26qRefLogs<32u){++g_s26qRefLogs;ext_Log(">>> S26Q tracking-origin event: %s",reason);}
}
static i32 s26q_ref_pose_valid(const XrPosef* p){
    const float* v=(const float*)p;
    for(u32 i=0;i<7u;++i)if(!(v[i]>-10000.0f&&v[i]<10000.0f))return 0;
    float n=v[0]*v[0]+v[1]*v[1]+v[2]*v[2]+v[3]*v[3];
    return n>0.98f&&n<1.02f;
}
static void s26q_ref_rotate(const XrQuaternionf* q,float x,float y,float z,XrVector3f* out){
    float tx=2.0f*(q->y*z-q->z*y),ty=2.0f*(q->z*x-q->x*z),tz=2.0f*(q->x*y-q->y*x);
    out->x=x+q->w*tx+q->y*tz-q->z*ty;
    out->y=y+q->w*ty+q->z*tx-q->x*tz;
    out->z=z+q->w*tz+q->x*ty-q->y*tx;
}
static i32 s26q_ref_compose(const XrPosef* change,const XrPosef* old,XrPosef* out){
    if(!s26q_ref_pose_valid(change)||!s26q_ref_pose_valid(old))return 0;
    XrQuaternionf q=change->orientation,b=old->orientation;
    float n=ext_Sqrtf(q.x*q.x+q.y*q.y+q.z*q.z+q.w*q.w);
    q.x=-q.x/n;q.y=-q.y/n;q.z=-q.z/n;q.w/=n;
    /* offset_new = inverse(new-natural-origin-in-old) * offset_old */
    out->orientation.x=q.w*b.x+q.x*b.w+q.y*b.z-q.z*b.y;
    out->orientation.y=q.w*b.y-q.x*b.z+q.y*b.w+q.z*b.x;
    out->orientation.z=q.w*b.z+q.x*b.y-q.y*b.x+q.z*b.w;
    out->orientation.w=q.w*b.w-q.x*b.x-q.y*b.y-q.z*b.z;
    XrQuaternionf* a=&out->orientation;n=ext_Sqrtf(a->x*a->x+a->y*a->y+a->z*a->z+a->w*a->w);
    a->x/=n;a->y/=n;a->z/=n;a->w/=n;
    s26q_ref_rotate(&q,old->position.x-change->position.x,old->position.y-change->position.y,old->position.z-change->position.z,&out->position);
    return s26q_ref_pose_valid(out);
}
static i32 __attribute__((ms_abi)) s26q_ref_poll(Handle instance,void* buffer){
    i32 result=g_s26qRefPoll?g_s26qRefPoll(instance,buffer):-12;
    if(result!=0||!buffer||instance!=g_s26qRefInstance||g_s26qRefDisabled)return result;
    const S26QRefEvent* e=(const S26QRefEvent*)buffer;
    if(e->type!=40||e->session!=g_s26qRefSession||e->referenceSpaceType!=2)return result;
    if(g_s26qRefCount>=8u){
        g_s26qRefDisabled=1;g_s26qRefCount=0;s26q_ref_log("queue overflow; compensation disabled for this session");return result;
    }
    u32 i=g_s26qRefCount++;
    while(i&&g_s26qRefQueue[i-1u].changeTime>e->changeTime){g_s26qRefQueue[i]=g_s26qRefQueue[i-1u];--i;}
    g_s26qRefQueue[i]=*e;
    /* The caller still receives exactly the runtime's event and result. */
    return result;
}
static i32 __attribute__((ms_abi)) s26q_ref_locate(Handle session,const S26QLocateInfo* info,void* state,u32 capacity,u32* count,void* views){
    if(!g_s26qRefLocate)return -12;
    if(!info||session!=g_s26qRefSession||!g_s26qRefSelf||g_s26qRefDisabled||
       info->space!=g_s26qRefSpace||*(Handle*)((u8*)g_s26qRefSelf+0x28)!=g_s26qRefSpace)
        return g_s26qRefLocate(session,info,state,capacity,count,views);
    S26QLocateInfo located=*info;
    while(g_s26qRefCount&&g_s26qRefQueue[0].changeTime<=info->displayTime){
        S26QRefEvent event=g_s26qRefQueue[0];--g_s26qRefCount;
        for(u32 i=0;i<g_s26qRefCount;++i)g_s26qRefQueue[i]=g_s26qRefQueue[i+1u];
        S26QRefInfo ci;zero_bytes(&ci,sizeof(ci));ci.type=37;ci.referenceSpaceType=2;
        if(!event.poseValid||!s26q_ref_compose(&event.poseInPreviousSpace,&g_s26qRefOffset,&ci.poseInReferenceSpace)){
            s26q_ref_log("runtime supplied no usable transform; existing space retained");continue;
        }
        Handle next=0;i32 result=g_s26qRefCreate(session,&ci,&next);
        if(result<0||!next){s26q_ref_log("reference-space creation failed; existing space retained");continue;}
        Handle previous=g_s26qRefSpace;
        g_s26qRefSpace=next;g_s26qRefOffset=ci.poseInReferenceSpace;
        *(Handle*)((u8*)g_s26qRefSelf+0x28)=next;located.space=next;
        /* Previous frame's xrEndFrame has returned before this frame begins.
           EndFrame, controllers, waist, skeleton and quad UI all read +0x28. */
        if(g_s26qRefDestroy(previous)<0){
            g_s26qRefDisabled=1;g_s26qRefCount=0;
            s26q_ref_log("old-space cleanup failed; further compensation disabled");break;
        }
        s26q_ref_log("applied at predicted display time; application tracking frame preserved");
    }
    return g_s26qRefLocate(session,&located,state,capacity,count,views);
}
static void s26q_ref_setup(void* self){
    if(!self)return;
    S26QGetProc get=*(S26QGetProc*)((u8*)self+0x1c8);
    Handle instance=*(Handle*)((u8*)self+0x10),session=*(Handle*)((u8*)self+0x20),space=*(Handle*)((u8*)self+0x28);
    S26QCreateRef create=0;S26QDestroyRef destroy=0;
    if(!get||!instance||!session||!space)return;
    if(get(instance,"xrCreateReferenceSpace",(void**)&create)<0||!create||get(instance,"xrDestroySpace",(void**)&destroy)<0||!destroy)return;
    S26QPoll* poll=(S26QPoll*)((u8*)self+0x278);S26QLocate* locate=(S26QLocate*)((u8*)self+0x270);
    if(!*poll||!*locate)return;
    if(*poll==s26q_ref_poll&&*locate==s26q_ref_locate&&g_s26qRefSession==session&&g_s26qRefSpace==space)return;
    if(*poll!=s26q_ref_poll)g_s26qRefPoll=*poll;
    if(*locate!=s26q_ref_locate)g_s26qRefLocate=*locate;
    if(!g_s26qRefPoll||!g_s26qRefLocate)return;
    g_s26qRefSelf=self;g_s26qRefInstance=instance;g_s26qRefSession=session;g_s26qRefSpace=space;
    g_s26qRefCreate=create;g_s26qRefDestroy=destroy;g_s26qRefCount=0;g_s26qRefDisabled=0;
    /* Verified base CreateSession uses LOCAL with an identity offset. */
    zero_bytes(&g_s26qRefOffset,sizeof(g_s26qRefOffset));g_s26qRefOffset.orientation.w=1.0f;
    *poll=s26q_ref_poll;*locate=s26q_ref_locate;
    s26q_hook_destroy(self);
}
