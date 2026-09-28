static void h504_lerp_rigid(const float* a,const float* b,float t,float* o);
#include "surface_guard_core_ag.inc"
typedef struct {const void* shape;S26AGHull hull;} S26AGShape;
static S26AGShape g_s26agShapes[2][4];
static u32 g_s26agShapeCursor[2];
static void s26ag_copy_hull(S26AGHull* dst,const S26AGHull* src){dst->count=src->count;for(i32 i=0;i<src->count;++i)for(i32 a=0;a<4;++a)dst->point[i][a]=src->point[i][a];}
static void s26ag_remember_shape(i32 hand,const void* shape,const S26AGHull* hull){
    if(!shape||!hull->count)return;i32 slot=-1;for(i32 i=0;i<4;++i)if(g_s26agShapes[hand][i].shape==shape){slot=i;break;}
    if(slot<0)for(i32 i=0;i<4;++i){i32 candidate=(i32)(g_s26agShapeCursor[hand]++%4u);if(!g_s26agShapes[hand][candidate].shape||g_s26agShapes[hand][candidate].shape!=g_h536NativePalmShape[hand]){slot=candidate;break;}}
    if(slot<0)return;g_s26agShapes[hand][slot].shape=shape;s26ag_copy_hull(&g_s26agShapes[hand][slot].hull,hull);
}
static i32 s26ag_load_shape(i32 hand,const void* shape,S26AGHull* hull){
    if(!shape)return 0;for(i32 i=0;i<4;++i)if(g_s26agShapes[hand][i].shape==shape){s26ag_copy_hull(hull,&g_s26agShapes[hand][i].hull);return 1;}return 0;
}
