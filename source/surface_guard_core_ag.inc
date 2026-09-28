/* Pure bounded geometry. The caller supplies current static-world contacts.
   No allocation, engine calls, retained dereferences or world searches. */
#define S26AG_POINTS 80
#define S26AG_PLANES 4
typedef struct {float point[S26AG_POINTS][4];i32 count;} S26AGHull;
typedef struct {float n[3],floor;const void* body;u32 age,seen;} S26AGPlane;
typedef struct {S26AGHull hull;S26AGPlane plane[S26AG_PLANES];i32 count;u32 clear,admitted;} S26AGCore;
static void s26ag_hull_point(S26AGHull* h,const float* p,float radius){
    if(h->count>=S26AG_POINTS)return;float* q=h->point[h->count++];q[0]=p[0];q[1]=p[1];q[2]=p[2];q[3]=radius;
}
static void s26ag_hull_box(S26AGHull* h,const float* m,const float* dims){
    for(i32 mask=0;mask<8;++mask){float p[3];for(i32 a=0;a<3;++a){p[a]=m[12+a];for(i32 k=0;k<3;++k)p[a]+=m[k*4+a]*dims[k]*((mask&(1<<k))?0.5f:-0.5f);}s26ag_hull_point(h,p,0);}
}
static void s26ag_hull_capsule(S26AGHull* h,const float* m,float radius,float height){
    float half=height*0.5f-radius;if(half<0)half=0;for(i32 sign=-1;sign<=1;sign+=2){float p[3];for(i32 a=0;a<3;++a)p[a]=m[12+a]+m[a]*half*(float)sign;s26ag_hull_point(h,p,radius);}
}
static float s26ag_minimum(const S26AGHull* h,const float* m,const float* n){
    float local[3];for(i32 k=0;k<3;++k)local[k]=m[k*4]*n[0]+m[k*4+1]*n[1]+m[k*4+2]*n[2];
    float origin=m[12]*n[0]+m[13]*n[1]+m[14]*n[2],best=1.0e20f;
    for(i32 k=0;k<h->count;++k){const float* p=h->point[k];float v=origin+h10_dot(p,local)-p[3];if(v<best)best=v;}return best;
}
static i32 s26ag_admissible(const S26AGCore* s,const float* m){
    for(i32 i=0;i<s->count;++i)if(s26ag_minimum(&s->hull,m,s->plane[i].n)<s->plane[i].floor-0.00001f)return 0;return 1;
}
static void s26ag_begin_contacts(S26AGCore* s){for(i32 i=0;i<s->count;++i)s->plane[i].seen=0;}
static void s26ag_contact_plane(S26AGCore* s,const void* body,const float* point,const float* normal,const float* pre){
    if(!s->admitted||!s->hull.count)return;float n[3]={normal[0],normal[1],normal[2]};if(!h10_norm3(n))return;
    for(i32 i=0;i<s->count;++i){S26AGPlane* p=&s->plane[i];float dot=h10_dot(n,p->n);if(p->body==body&&(dot>0.98f||dot<-0.98f)){p->seen=1;return;}}
    if(s->count>=S26AG_PLANES)return;
    float side=(pre[12]-point[0])*n[0]+(pre[13]-point[1])*n[1]+(pre[14]-point[2])*n[2];
    if(side<0){n[0]=-n[0];n[1]=-n[1];n[2]=-n[2];}
    S26AGPlane* p=&s->plane[s->count++];for(i32 a=0;a<3;++a)p->n[a]=n[a];p->floor=h10_dot(point,n)+0.0005f;p->body=body;p->age=0;p->seen=1;
}
static void s26ag_end_contacts(S26AGCore* s,i32 anyWorldContact){
    if(anyWorldContact)s->clear=0;else if(s->clear<4)s->clear++;
    if(s->clear>=4)s->admitted=1;
    i32 count=0;for(i32 i=0;i<s->count;++i){S26AGPlane* p=&s->plane[i];if(p->seen)p->age=0;else p->age++;if(p->age<=4){if(count!=i){S26AGPlane* q=&s->plane[count];for(i32 a=0;a<3;++a)q->n[a]=p->n[a];q->floor=p->floor;q->body=p->body;q->age=p->age;q->seen=p->seen;}count++;}}s->count=count;
}
static i32 s26ag_correct(const S26AGCore* s,const float* pre,const float* post,float* out,float* velocity,float* omega){
    if(!s->count||!s->hull.count||s26ag_admissible(s,post))return 0;
    float base[16],rotated[16];for(i32 i=0;i<16;++i){base[i]=pre[i];rotated[i]=post[i];}for(i32 a=0;a<3;++a)base[12+a]=post[12+a];
    for(i32 pass=0;pass<4;++pass)for(i32 i=0;i<s->count;++i){const S26AGPlane* p=&s->plane[i];float missing=p->floor-s26ag_minimum(&s->hull,base,p->n);if(missing>0)for(i32 a=0;a<3;++a)base[12+a]+=p->n[a]*(missing+0.00002f);}
    float dx=base[12]-post[12],dy=base[13]-post[13],dz=base[14]-post[14];
    if(dx*dx+dy*dy+dz*dz>0.01f||!s26ag_admissible(s,base))return 0;
    for(i32 a=0;a<3;++a)rotated[12+a]=base[12+a];
    float lo=0,hi=1;if(s26ag_admissible(s,rotated))lo=1;else for(i32 iteration=0;iteration<12;++iteration){float mid=(lo+hi)*0.5f,m[16];h504_lerp_rigid(base,rotated,mid,m);if(s26ag_admissible(s,m))lo=mid;else hi=mid;}
    h504_lerp_rigid(base,rotated,lo,out);for(i32 a=0;a<3;++a)omega[a]*=lo;
    for(i32 i=0;i<s->count;++i){const float* n=s->plane[i].n;float into=h10_dot(velocity,n);if(into<0)for(i32 a=0;a<3;++a)velocity[a]-=n[a]*into;}
    return 1;
}
