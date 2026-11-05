#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
typedef int i32;typedef unsigned u32;typedef struct{float f[16];}H10Vert;
#define H504_PALM_BOXES 12
#define H511_PALM_SLICES 5
#define H511_PALM_INSET 0.0006f
#define H511_PALM_OVERLAP 0.0012f
static H10Vert* g_h20CpuVerts[2];static u32 g_h20CpuVertCount[2];static float metric=1,pivot[3];static int mode;
static float sourceBones[512];static unsigned skinCalls;
static int h20_load_cpu_skin(int h){return g_h20CpuVerts[h]!=0;}
static float h5755ea_world_units_per_meter(void){return metric;}
static void h10_copy_f(float*a,const float*b,int n){memcpy(a,b,n*4);}
static void h10_build_rig(int h){(void)h;}
static void h10_build_bones(int h,float*b){(void)h;memcpy(b,sourceBones,sizeof(sourceBones));}
static int h504_vertex_is_palm(int h,const H10Vert*v){(void)h;int j;memcpy(&j,v->f+8,4);return mode==0?1:mode==1?(j%3==0):0;}
static void h10_identity(float*m){memset(m,0,64);for(int k=0;k<4;k++)m[k*5]=1;}
static void h14_transform_point(const float*m,const float*p,float*o){for(int a=0;a<3;a++)o[a]=m[a]*p[0]+m[4+a]*p[1]+m[8+a]*p[2]+m[12+a];}
static void h20_skin_vertex_local_metric(int h,const H10Vert*v,const float*b,float*out,float scale){(void)h;skinCalls++;float sp[3]={0},sw=0;for(int k=0;k<4;k++){float w=v->f[12+k];int j;memcpy(&j,v->f+8+k,4);if(w<=0||j<0||j>=32)continue;const float*B=b+j*16;sp[0]+=w*(B[0]*v->f[0]+B[4]*v->f[1]+B[8]*v->f[2]+B[12]);sp[1]+=w*(B[1]*v->f[0]+B[5]*v->f[1]+B[9]*v->f[2]+B[13]);sp[2]+=w*(B[2]*v->f[0]+B[6]*v->f[1]+B[10]*v->f[2]+B[14]);sw+=w;}if(sw<=.000001f)memcpy(sp,v->f,12);for(int a=0;a<3;a++)out[a]=(sp[a]-pivot[a])*(.01f*scale);}

static i32 h504_fit_palm_boxes(i32 hand,const float* bodyToHand,float outDims[H504_PALM_BOXES][4],float outM[H504_PALM_BOXES][16],i32* outCount){
    if(outCount)*outCount=0;if(hand<0||hand>1||!bodyToHand||!outDims||!outM||!h20_load_cpu_skin(hand))return 0;
    float canonicalM[16];h10_copy_f(canonicalM,bodyToHand,16);float metric=h5755ea_world_units_per_meter();for(i32 k=0;k<3;++k)canonicalM[12+k]/=metric;bodyToHand=canonicalM;
    h10_build_rig(hand);float bones[32*16];h10_build_bones(hand,bones);H10Vert* vv=g_h20CpuVerts[hand];u32 nv=g_h20CpuVertCount[hand];
    float lo[3]={999,999,999},hi[3]={-999,-999,-999};i32 n=0;
    for(u32 i=0;i<nv;++i){if(!h504_vertex_is_palm(hand,&vv[i]))continue;float hp[3],bp[3];h20_skin_vertex_local_metric(hand,&vv[i],bones,hp,1.0f);h14_transform_point(bodyToHand,hp,bp);for(i32 a=0;a<3;++a){if(bp[a]<lo[a])lo[a]=bp[a];if(bp[a]>hi[a])hi[a]=bp[a];}n++;}
    if(n<48)return 0;float ex[3]={hi[0]-lo[0],hi[1]-lo[1],hi[2]-lo[2]};i32 thin=0;if(ex[1]<ex[thin])thin=1;if(ex[2]<ex[thin])thin=2;i32 a0=(thin==0)?1:0,a1=(thin==2)?1:2;if(a0==thin)a0=2;if(a1==thin||a1==a0){for(i32 a=0;a<3;++a)if(a!=thin&&a!=a0){a1=a;break;}}
    i32 longA=ex[a0]>=ex[a1]?a0:a1,shortA=longA==a0?a1:a0;float span=hi[longA]-lo[longA];if(span<(0.035f*1.0f)||ex[shortA]<(0.025f*1.0f))return 0;
    float sl[H511_PALM_SLICES][3],sh[H511_PALM_SLICES][3];i32 cnt[H511_PALM_SLICES];for(i32 q=0;q<H511_PALM_SLICES;++q){cnt[q]=0;for(i32 a=0;a<3;++a){sl[q][a]=999;sh[q][a]=-999;}}
    for(u32 i=0;i<nv;++i){if(!h504_vertex_is_palm(hand,&vv[i]))continue;float hp[3],bp[3];h20_skin_vertex_local_metric(hand,&vv[i],bones,hp,1.0f);h14_transform_point(bodyToHand,hp,bp);i32 q=(i32)(((bp[longA]-lo[longA])/span)*(float)H511_PALM_SLICES);if(q<0)q=0;if(q>=H511_PALM_SLICES)q=H511_PALM_SLICES-1;cnt[q]++;for(i32 a=0;a<3;++a){if(bp[a]<sl[q][a])sl[q][a]=bp[a];if(bp[a]>sh[q][a])sh[q][a]=bp[a];}}
    i32 outN=0;for(i32 q=0;q<H511_PALM_SLICES&&outN<H504_PALM_BOXES;++q){if(cnt[q]<18)continue;float dims[3],cen[3];for(i32 a=0;a<3;++a){float r=sh[q][a]-sl[q][a];float inset=(a==longA)?0.0f:(H511_PALM_INSET*1.0f);dims[a]=r-2.0f*inset;if(a==longA)dims[a]+=(H511_PALM_OVERLAP*1.0f);if(dims[a]<(0.0045f*1.0f))dims[a]=(0.0045f*1.0f);cen[a]=0.5f*(sl[q][a]+sh[q][a]);}if(dims[0]>(0.13f*1.0f)||dims[1]>(0.13f*1.0f)||dims[2]>(0.13f*1.0f))continue;outDims[outN][0]=dims[0];outDims[outN][1]=dims[1];outDims[outN][2]=dims[2];outDims[outN][3]=0;h10_identity(outM[outN]);outM[outN][12]=cen[0];outM[outN][13]=cen[1];outM[outN][14]=cen[2];outN++;}
    if(outN<3)return 0;for(i32 q=0;q<outN;++q)for(i32 k=0;k<3;++k){outDims[q][k]*=metric;outM[q][12+k]*=metric;}if(outCount)*outCount=outN;return 1;
}
static i32 candidate(i32 hand,const float* bodyToHand,float outDims[H504_PALM_BOXES][4],float outM[H504_PALM_BOXES][16],i32* outCount){
    if(outCount)*outCount=0;if(hand<0||hand>1||!bodyToHand||!outDims||!outM||!h20_load_cpu_skin(hand))return 0;
    float canonicalM[16];h10_copy_f(canonicalM,bodyToHand,16);float metric=h5755ea_world_units_per_meter();for(i32 k=0;k<3;++k)canonicalM[12+k]/=metric;bodyToHand=canonicalM;
    h10_build_rig(hand);float bones[32*16];h10_build_bones(hand,bones);H10Vert* vv=g_h20CpuVerts[hand];u32 nv=g_h20CpuVertCount[hand];
    float palmPoints[4096][3];float lo[3]={999,999,999},hi[3]={-999,-999,-999};i32 n=0;
    for(u32 i=0;i<nv;++i){if(!h504_vertex_is_palm(hand,&vv[i]))continue;float hp[3],bp[3];h20_skin_vertex_local_metric(hand,&vv[i],bones,hp,1.0f);h14_transform_point(bodyToHand,hp,bp);for(i32 a=0;a<3;++a){if(bp[a]<lo[a])lo[a]=bp[a];if(bp[a]>hi[a])hi[a]=bp[a];}if(n<4096)for(i32 a=0;a<3;a++)palmPoints[n][a]=bp[a];n++;}
    if(n<48)return 0;float ex[3]={hi[0]-lo[0],hi[1]-lo[1],hi[2]-lo[2]};i32 thin=0;if(ex[1]<ex[thin])thin=1;if(ex[2]<ex[thin])thin=2;i32 a0=(thin==0)?1:0,a1=(thin==2)?1:2;if(a0==thin)a0=2;if(a1==thin||a1==a0){for(i32 a=0;a<3;++a)if(a!=thin&&a!=a0){a1=a;break;}}
    i32 longA=ex[a0]>=ex[a1]?a0:a1,shortA=longA==a0?a1:a0;float span=hi[longA]-lo[longA];if(span<(0.035f*1.0f)||ex[shortA]<(0.025f*1.0f))return 0;
    float sl[H511_PALM_SLICES][3],sh[H511_PALM_SLICES][3];i32 cnt[H511_PALM_SLICES];for(i32 q=0;q<H511_PALM_SLICES;++q){cnt[q]=0;for(i32 a=0;a<3;++a){sl[q][a]=999;sh[q][a]=-999;}}
    if(n<=4096){    for(i32 i=0;i<n;++i){const float* bp=palmPoints[i];i32 q=(i32)(((bp[longA]-lo[longA])/span)*(float)H511_PALM_SLICES);if(q<0)q=0;if(q>=H511_PALM_SLICES)q=H511_PALM_SLICES-1;cnt[q]++;for(i32 a=0;a<3;++a){if(bp[a]<sl[q][a])sl[q][a]=bp[a];if(bp[a]>sh[q][a])sh[q][a]=bp[a];}}}else{    for(u32 i=0;i<nv;++i){if(!h504_vertex_is_palm(hand,&vv[i]))continue;float hp[3],bp[3];h20_skin_vertex_local_metric(hand,&vv[i],bones,hp,1.0f);h14_transform_point(bodyToHand,hp,bp);i32 q=(i32)(((bp[longA]-lo[longA])/span)*(float)H511_PALM_SLICES);if(q<0)q=0;if(q>=H511_PALM_SLICES)q=H511_PALM_SLICES-1;cnt[q]++;for(i32 a=0;a<3;++a){if(bp[a]<sl[q][a])sl[q][a]=bp[a];if(bp[a]>sh[q][a])sh[q][a]=bp[a];}}}
    i32 outN=0;for(i32 q=0;q<H511_PALM_SLICES&&outN<H504_PALM_BOXES;++q){if(cnt[q]<18)continue;float dims[3],cen[3];for(i32 a=0;a<3;++a){float r=sh[q][a]-sl[q][a];float inset=(a==longA)?0.0f:(H511_PALM_INSET*1.0f);dims[a]=r-2.0f*inset;if(a==longA)dims[a]+=(H511_PALM_OVERLAP*1.0f);if(dims[a]<(0.0045f*1.0f))dims[a]=(0.0045f*1.0f);cen[a]=0.5f*(sl[q][a]+sh[q][a]);}if(dims[0]>(0.13f*1.0f)||dims[1]>(0.13f*1.0f)||dims[2]>(0.13f*1.0f))continue;outDims[outN][0]=dims[0];outDims[outN][1]=dims[1];outDims[outN][2]=dims[2];outDims[outN][3]=0;h10_identity(outM[outN]);outM[outN][12]=cen[0];outM[outN][13]=cen[1];outM[outN][14]=cen[2];outN++;}
    if(outN<3)return 0;for(i32 q=0;q<outN;++q)for(i32 k=0;k<3;++k){outDims[q][k]*=metric;outM[q][12+k]*=metric;}if(outCount)*outCount=outN;return 1;
}

int main(int argc,char**argv){unsigned cases=0,positive=0,empty=0,fallback=0,saved=0;
for(int f=1;f<argc;f++){FILE*fp=fopen(argv[f],"rb");if(!fp)return 2;unsigned magic,nv,nj;fread(&magic,4,1,fp);fread(&nv,4,1,fp);fread(&nj,4,1,fp);fread(pivot,4,3,fp);if(magic!=0x484e4435||nv>30000)return 3;H10Vert*v=malloc(nv*sizeof(*v));if(fread(v,sizeof(*v),nv,fp)!=nv)return 4;fclose(fp);g_h20CpuVerts[0]=g_h20CpuVerts[1]=v;g_h20CpuVertCount[0]=g_h20CpuVertCount[1]=nv;
for(int pose=0;pose<8;pose++)for(int side=0;side<2;side++)for(int scale=0;scale<3;scale++)for(mode=0;mode<3;mode++){
 metric=scale==0?.7f:scale==1?1.f:1.3f;for(int j=0;j<32;j++){float*m=sourceBones+j*16;h10_identity(m);float a=.025f*pose*j;m[0]=cosf(a);m[1]=sinf(a);m[4]=-sinf(a);m[5]=cosf(a);}
 float m[16];h10_identity(m);float a=.13f*pose;m[0]=cosf(a);m[2]=-sinf(a);m[8]=sinf(a);m[10]=cosf(a);m[12]=.03f*side;m[13]=.01f*pose;
 float da[H504_PALM_BOXES][4]={0},db[H504_PALM_BOXES][4]={0},ma[H504_PALM_BOXES][16]={0},mb[H504_PALM_BOXES][16]={0};int na=0,nb=0;skinCalls=0;int x=h504_fit_palm_boxes(side,m,da,ma,&na);unsigned c=skinCalls;skinCalls=0;int y=candidate(side,m,db,mb,&nb);if(x!=y||na!=nb||(x&&(memcmp(da,db,na*16)||memcmp(ma,mb,na*64)))){printf("FAIL %s pose%d side%d scale%d mode%d count%d/%d\n",argv[f],pose,side,scale,mode,na,nb);return 5;}saved+=c-skinCalls;cases++;if(x)positive++;else empty++;if(mode==0&&nv>4096)fallback++;
}free(v);}
printf("PASS cases=%u positive=%u rejected=%u overflow_fallback_cases=%u saved_skin_calls=%u\n",cases,positive,empty,fallback,saved);return positive&&empty&&fallback?0:6;}
