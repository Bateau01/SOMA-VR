
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
typedef int32_t i32;typedef uint32_t u32;typedef uint8_t u8;typedef uint64_t u64;
typedef struct {float f[16];} H10Vert;
typedef struct {u32 a,b;} H10Edge;
typedef struct {H10Vert a,b;} H10Seg;
#define ext_Sqrtf sqrtf
#define ext_malloc malloc
#define ext_free free
#define ext_fopen fopen
#define ext_fread fread
#define ext_fclose fclose
#define ext_Log(...) ((void)0)
#define zero_bytes(p,n) memset(p,0,n)
#define H5748_FAMILY_DEEPSEA 2
#define H5748_FAMILY_DEEPSEA_MUTILATED 3
static int g_h5748Family,g_cleanTried[2],g_cleanVerts[2],g_cleanCapStart[2],g_cleanCapVerts[2],g_cleanCapTris[2];
static const char *inputPath,*outputPath;
static int h5748_is_stump(int hand){return hand==0&&g_h5748Family==3;}
static const char* h5748_skin_filename(int hand){(void)hand;return inputPath;}
static int make_sibling_path(char* out,size_t n,const char* path){return snprintf(out,n,"%s",path)>0;}
static void h10_build_rig(int hand){(void)hand;}
static u32 h5755bq_fnv1a32(u32 a,const void*b,u64 n){(void)b;(void)n;return a;}
static void h10_copy_f(float* d,const float* s,i32 n){ for(i32 i=0;i<n;++i)d[i]=s[i]; }
static float h10_len3(float x,float y,float z){ return ext_Sqrtf(x*x+y*y+z*z); }
static i32 h10_norm3(float* v){ float l=h10_len3(v[0],v[1],v[2]); if(l<0.000001f)return 0; v[0]/=l;v[1]/=l;v[2]/=l;return 1; }
static float h10_dot(const float* a,const float* b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
static i32 h10_pos_eq(const H10Vert* a,const H10Vert* b,float eps2){float x=a->f[0]-b->f[0],y=a->f[1]-b->f[1],z=a->f[2]-b->f[2];return x*x+y*y+z*z<=eps2;}
static void h10_vertex_copy(H10Vert* d,const H10Vert* s){for(i32 i=0;i<16;++i)d->f[i]=s->f[i];}
static i32 h10_joint_id(const H10Vert* v,i32 k){const i32* p=(const i32*)(const void*)&v->f[8];return p[k];}
static void h10_set_joint_id(H10Vert* v,i32 k,i32 id){i32* p=(i32*)(void*)&v->f[8];p[k]=id;}
static void h10_interp_vertex(const H10Vert* a,const H10Vert* b,float t,H10Vert* o){
    for(i32 i=0;i<8;++i)o->f[i]=a->f[i]+(b->f[i]-a->f[i])*t;
    float n[3]={o->f[3],o->f[4],o->f[5]}; if(h10_norm3(n)){o->f[3]=n[0];o->f[4]=n[1];o->f[5]=n[2];}
    i32 ids[8];float ws[8];i32 count=0;
    for(i32 side=0;side<2;++side){const H10Vert* v=side?b:a;float mul=side?t:(1.0f-t);for(i32 k=0;k<4;++k){float w=v->f[12+k]*mul;if(w<=0.000001f)continue;i32 id=h10_joint_id(v,k),slot=-1;for(i32 q=0;q<count;++q)if(ids[q]==id){slot=q;break;}if(slot<0&&count<8){slot=count;ids[count]=id;ws[count]=0.0f;count++;}if(slot>=0)ws[slot]+=w;}}
    for(i32 k=0;k<4;++k){i32 best=-1;for(i32 q=0;q<count;++q){i32 used=0;for(i32 p=0;p<k;++p)if(h10_joint_id(o,p)==ids[q])used=1;if(!used&&(best<0||ws[q]>ws[best]))best=q;}if(best>=0){h10_set_joint_id(o,k,ids[best]);o->f[12+k]=ws[best];}else{h10_set_joint_id(o,k,0);o->f[12+k]=0.0f;}}
    float sw=o->f[12]+o->f[13]+o->f[14]+o->f[15]; if(sw>0.000001f)for(i32 k=0;k<4;++k)o->f[12+k]/=sw;
}
static void h10_average_skin(H10Vert* center,const H10Vert* loop,u32 n){
    i32 ids[128];float ws[128];i32 count=0;for(i32 q=0;q<128;++q){ids[q]=-1;ws[q]=0.0f;}
    for(u32 i=0;i<n;++i)for(i32 k=0;k<4;++k){float w=loop[i].f[12+k];if(w<=0.000001f)continue;i32 id=h10_joint_id(&loop[i],k),slot=-1;for(i32 q=0;q<count;++q)if(ids[q]==id){slot=q;break;}if(slot<0&&count<128){slot=count;ids[count]=id;ws[count]=0.0f;count++;}if(slot>=0)ws[slot]+=w;}
    for(i32 k=0;k<4;++k){i32 best=-1;for(i32 q=0;q<count;++q){i32 used=0;for(i32 p=0;p<k;++p)if(h10_joint_id(center,p)==ids[q])used=1;if(!used&&(best<0||ws[q]>ws[best]))best=q;}if(best>=0){h10_set_joint_id(center,k,ids[best]);center->f[12+k]=ws[best];}else{h10_set_joint_id(center,k,0);center->f[12+k]=0.0f;}}
    float sw=center->f[12]+center->f[13]+center->f[14]+center->f[15];if(sw>0.000001f)for(i32 k=0;k<4;++k)center->f[12+k]/=sw;
}
static i32 h10_build_clean_mesh(i32 hand){
    if(hand<0||hand>1)return 0;if(g_cleanTried[hand])return g_cleanVerts[hand]>0;g_cleanTried[hand]=1;
    if(h5748_is_stump(hand)){ext_Log(">>> S6-HANDS5748N AUTHORED STUMP PRESERVED: left mutilated mesh bypasses normal +0.85 cm wrist recut/cap; severed geometry is rendered exactly as authored");return 0;}
    char path[512];if(!make_sibling_path(path,sizeof(path),h5748_skin_filename(hand)))return 0;
    void* f=ext_fopen(path,"rb");if(!f){ext_Log(">>> S6-HANDS34 CLEAN WRIST: could not open %s",path);return 0;}
    u32 magic=0,nv=0,nj=0;float pivot[3];
    if(ext_fread(&magic,4,1,f)!=1||ext_fread(&nv,4,1,f)!=1||ext_fread(&nj,4,1,f)!=1||ext_fread(pivot,4,3,f)!=3||magic!=0x484E4435u||nv<9||nv>30000||(nv%3)!=0){ext_fclose(f);ext_Log(">>> S6-HANDS34 CLEAN WRIST: bad skin header for %s",path);return 0;}
    u64 bytes=(u64)nv*sizeof(H10Vert);H10Vert* src=(H10Vert*)ext_malloc(bytes);if(!src){ext_fclose(f);return 0;}if(ext_fread(src,1,bytes,f)!=bytes){ext_free(src);ext_fclose(f);return 0;}ext_fclose(f);
    float uvMinU=src[0].f[6],uvMaxU=src[0].f[6],uvMinV=src[0].f[7],uvMaxV=src[0].f[7];u32 uvOutside=0;
    for(u32 ui=0;ui<nv;++ui){float u=src[ui].f[6],v=src[ui].f[7];if(u<uvMinU)uvMinU=u;if(u>uvMaxU)uvMaxU=u;if(v<uvMinV)uvMinV=v;if(v>uvMaxV)uvMaxV=v;if(u<-0.001f||u>1.001f||v<-0.001f||v>1.001f)uvOutside++;}
    u32 vertexHash=h5755bq_fnv1a32(2166136261u,src,bytes);
    ext_Log(">>> S6-HANDS5755BQ SKIN UV/FINGERPRINT %s: %s verts %u | U %.6f..%.6f V %.6f..%.6f outside01 %u | vertex fnv1a32=0x%08x | telemetry only",hand==0?"L":"R",h5748_skin_filename(hand),nv,(double)uvMinU,(double)uvMaxU,(double)uvMinV,(double)uvMaxV,uvOutside,vertexHash);
    h10_build_rig(hand); /* H12: preserve source-authored skin weights exactly; no destructive cross-finger cleanup. */
    float mn[3]={src[0].f[0],src[0].f[1],src[0].f[2]},mx[3]={mn[0],mn[1],mn[2]},meshC[3]={0,0,0};
    for(u32 i=0;i<nv;++i){for(i32 a=0;a<3;++a){float v=src[i].f[a];meshC[a]+=v;if(v<mn[a])mn[a]=v;if(v>mx[a])mx[a]=v;}}for(i32 a=0;a<3;++a)meshC[a]/=(float)nv;
    float range=mx[0]-mn[0];if(mx[1]-mn[1]>range)range=mx[1]-mn[1];if(mx[2]-mn[2]>range)range=mx[2]-mn[2];float eps=range*0.00002f+0.00002f,eps2=eps*eps;
    H10Edge* edges=(H10Edge*)ext_malloc((u64)nv*sizeof(H10Edge));u8* boundary=(u8*)ext_malloc((u64)nv);if(!edges||!boundary){if(edges)ext_free(edges);if(boundary)ext_free(boundary);ext_free(src);return 0;}
    u32 ne=0;for(u32 t=0;t<nv;t+=3){edges[ne].a=t;edges[ne++].b=t+1;edges[ne].a=t+1;edges[ne++].b=t+2;edges[ne].a=t+2;edges[ne++].b=t;}
    for(u32 i=0;i<ne;++i)boundary[i]=1;
    for(u32 i=0;i<ne;++i){const H10Vert* ia=&src[edges[i].a];const H10Vert* ib=&src[edges[i].b];for(u32 j=0;j<ne;++j){if(i==j)continue;const H10Vert* ja=&src[edges[j].a];const H10Vert* jb=&src[edges[j].b];if((h10_pos_eq(ia,ja,eps2)&&h10_pos_eq(ib,jb,eps2))||(h10_pos_eq(ia,jb,eps2)&&h10_pos_eq(ib,ja,eps2))){boundary[i]=0;break;}}}
    u32 nb=0;for(u32 i=0;i<ne;++i)if(boundary[i])++nb;if(nb<5||nb>1000){ext_Log(">>> S6-HANDS34 CLEAN WRIST: boundary census %u invalid",nb);ext_free(boundary);ext_free(edges);ext_free(src);return 0;}
    u8* used=(u8*)ext_malloc((u64)ne);u32* loopIdx=(u32*)ext_malloc((u64)(nb+1)*sizeof(u32));u32* best=(u32*)ext_malloc((u64)(nb+1)*sizeof(u32));if(!used||!loopIdx||!best){if(used)ext_free(used);if(loopIdx)ext_free(loopIdx);if(best)ext_free(best);ext_free(boundary);ext_free(edges);ext_free(src);return 0;}for(u32 i=0;i<ne;++i)used[i]=0;
    u32 bestN=0,loops=0;for(u32 seed=0;seed<ne;++seed){if(!boundary[seed]||used[seed])continue;u32 ln=0,startV=edges[seed].a,curV=edges[seed].b;used[seed]=1;loopIdx[ln++]=startV;loopIdx[ln++]=curV;i32 closed=0;for(u32 guard=0;guard<nb+2;++guard){if(h10_pos_eq(&src[curV],&src[startV],eps2)){closed=1;break;}i32 found=-1;u32 other=0;for(u32 e=0;e<ne;++e){if(!boundary[e]||used[e])continue;if(h10_pos_eq(&src[edges[e].a],&src[curV],eps2)){found=(i32)e;other=edges[e].b;break;}if(h10_pos_eq(&src[edges[e].b],&src[curV],eps2)){found=(i32)e;other=edges[e].a;break;}}if(found<0)break;used[found]=1;curV=other;if(ln<nb+1)loopIdx[ln++]=curV;}if(closed&&ln>=5){++loops;if(h10_pos_eq(&src[loopIdx[ln-1]],&src[loopIdx[0]],eps2))--ln;if(ln>bestN){bestN=ln;for(u32 i=0;i<ln;++i)best[i]=loopIdx[i];}}}
    if(bestN<5){ext_Log(">>> S6-HANDS34 CLEAN WRIST: no closed wrist loop from %u boundary edges",nb);ext_free(best);ext_free(loopIdx);ext_free(used);ext_free(boundary);ext_free(edges);ext_free(src);return 0;}
    float center[3]={0,0,0};for(u32 i=0;i<bestN;++i){center[0]+=src[best[i]].f[0];center[1]+=src[best[i]].f[1];center[2]+=src[best[i]].f[2];}for(i32 a=0;a<3;++a)center[a]/=(float)bestN;
    float n[3]={0,0,0};for(u32 i=0;i<bestN;++i){const H10Vert* a=&src[best[i]];const H10Vert* b=&src[best[(i+1)%bestN]];n[0]+=(a->f[1]-b->f[1])*(a->f[2]+b->f[2]);n[1]+=(a->f[2]-b->f[2])*(a->f[0]+b->f[0]);n[2]+=(a->f[0]-b->f[0])*(a->f[1]+b->f[1]);}if(!h10_norm3(n)){n[0]=0;n[1]=0;n[2]=1;}
    float toMesh[3]={meshC[0]-center[0],meshC[1]-center[1],meshC[2]-center[2]};if(h10_dot(n,toMesh)<0.0f){n[0]=-n[0];n[1]=-n[1];n[2]=-n[2];}
    float insetCm=0.85f;if(g_h5748Family==H5748_FAMILY_DEEPSEA||g_h5748Family==H5748_FAMILY_DEEPSEA_MUTILATED)insetCm=2.20f;float planeP[3]={center[0]+n[0]*insetCm,center[1]+n[1]*insetCm,center[2]+n[2]*insetCm};
    u64 capOut=(u64)nv*2u+(u64)nb*6u+96u;H10Vert* out=(H10Vert*)ext_malloc(capOut*sizeof(H10Vert));H10Seg* segs=(H10Seg*)ext_malloc((u64)(nv/3+8)*sizeof(H10Seg));if(!out||!segs){if(out)ext_free(out);if(segs)ext_free(segs);ext_free(best);ext_free(loopIdx);ext_free(used);ext_free(boundary);ext_free(edges);ext_free(src);return 0;}u32 outN=0,segN=0;
    for(u32 t=0;t<nv;t+=3){H10Vert poly[5];u32 pn=3;for(i32 k=0;k<3;++k)h10_vertex_copy(&poly[k],&src[t+k]);H10Vert clipped[5];u32 cn=0;H10Vert crosses[3];u32 crossN=0;
        for(u32 e=0;e<3;++e){const H10Vert* A=&src[t+e];const H10Vert* B=&src[t+((e+1)%3)];float da=(A->f[0]-planeP[0])*n[0]+(A->f[1]-planeP[1])*n[1]+(A->f[2]-planeP[2])*n[2];float db=(B->f[0]-planeP[0])*n[0]+(B->f[1]-planeP[1])*n[1]+(B->f[2]-planeP[2])*n[2];if((da>=0.0f)!=(db>=0.0f)){float q=da/(da-db);if(crossN<3)h10_interp_vertex(A,B,q,&crosses[crossN++]);}}
        if(crossN==2&&segN<nv/3+8){h10_vertex_copy(&segs[segN].a,&crosses[0]);h10_vertex_copy(&segs[segN].b,&crosses[1]);segN++;}
        cn=0;for(u32 e=0;e<pn;++e){const H10Vert* A=&poly[e];const H10Vert* B=&poly[(e+1)%pn];float da=(A->f[0]-planeP[0])*n[0]+(A->f[1]-planeP[1])*n[1]+(A->f[2]-planeP[2])*n[2];float db=(B->f[0]-planeP[0])*n[0]+(B->f[1]-planeP[1])*n[1]+(B->f[2]-planeP[2])*n[2];i32 ina=da>=-eps,inb=db>=-eps;if(ina){h10_vertex_copy(&clipped[cn++],A);}if(ina!=inb){float q=da/(da-db);h10_interp_vertex(A,B,q,&clipped[cn++]);}}
        if(cn>=3)for(u32 k=1;k+1<cn;++k){if(outN+3<=capOut){h10_vertex_copy(&out[outN++],&clipped[0]);h10_vertex_copy(&out[outN++],&clipped[k]);h10_vertex_copy(&out[outN++],&clipped[k+1]);}}
    }
    H10Vert* cutLoop=(H10Vert*)ext_malloc((u64)(segN+2)*sizeof(H10Vert));H10Vert* bestLoop=(H10Vert*)ext_malloc((u64)(segN+2)*sizeof(H10Vert));u8* segUsed=(u8*)ext_malloc((u64)segN);u32 cutN=0,cutLoops=0;if(cutLoop&&bestLoop&&segUsed&&segN){for(u32 i=0;i<segN;++i)segUsed[i]=0;float ceps2=(eps*8.0f)*(eps*8.0f);for(u32 seed=0;seed<segN;++seed){if(segUsed[seed])continue;u32 ln=0;H10Vert startV,curV;h10_vertex_copy(&startV,&segs[seed].a);h10_vertex_copy(&curV,&segs[seed].b);segUsed[seed]=1;h10_vertex_copy(&cutLoop[ln++],&startV);h10_vertex_copy(&cutLoop[ln++],&curV);i32 closed=0;for(u32 guard=0;guard<segN+2;++guard){if(h10_pos_eq(&curV,&startV,ceps2)){closed=1;break;}i32 found=-1;H10Vert other;for(u32 s=0;s<segN;++s){if(segUsed[s])continue;if(h10_pos_eq(&segs[s].a,&curV,ceps2)){found=(i32)s;h10_vertex_copy(&other,&segs[s].b);break;}if(h10_pos_eq(&segs[s].b,&curV,ceps2)){found=(i32)s;h10_vertex_copy(&other,&segs[s].a);break;}}if(found<0)break;segUsed[found]=1;h10_vertex_copy(&curV,&other);if(ln<segN+2)h10_vertex_copy(&cutLoop[ln++],&curV);}if(closed&&ln>=5){cutLoops++;if(h10_pos_eq(&cutLoop[ln-1],&cutLoop[0],ceps2))--ln;if(ln>cutN){cutN=ln;for(u32 q=0;q<ln;++q)h10_vertex_copy(&bestLoop[q],&cutLoop[q]);}}}}
    if(cutN>=5){g_cleanCapStart[hand]=(i32)outN;H10Vert c;zero_bytes(&c,sizeof(c));for(u32 i=0;i<cutN;++i){c.f[0]+=bestLoop[i].f[0];c.f[1]+=bestLoop[i].f[1];c.f[2]+=bestLoop[i].f[2];c.f[6]+=bestLoop[i].f[6];c.f[7]+=bestLoop[i].f[7];}c.f[0]/=cutN;c.f[1]/=cutN;c.f[2]/=cutN;c.f[6]/=cutN;c.f[7]/=cutN;c.f[3]=-n[0];c.f[4]=-n[1];c.f[5]=-n[2];h10_average_skin(&c,bestLoop,cutN);for(u32 i=0;i<cutN;++i){H10Vert a,b;h10_vertex_copy(&a,&bestLoop[i]);h10_vertex_copy(&b,&bestLoop[(i+1)%cutN]);a.f[3]=b.f[3]=c.f[3];a.f[4]=b.f[4]=c.f[4];a.f[5]=b.f[5]=c.f[5];if(outN+3<=capOut){h10_vertex_copy(&out[outN++],&c);h10_vertex_copy(&out[outN++],&b);h10_vertex_copy(&out[outN++],&a);}}g_cleanCapTris[hand]=(i32)cutN;g_cleanCapVerts[hand]=(i32)outN-g_cleanCapStart[hand];}
    FILE* output=fopen(outputPath,"wb");if(!output)return 0;
    fwrite(out,sizeof(H10Vert),outN,output);fclose(output);g_cleanVerts[hand]=(i32)outN;
    printf("%u %d %d\n",outN,g_cleanCapStart[hand],g_cleanCapVerts[hand]);
    ext_Log(">>> S6-HANDS34 CLEAN WRIST READY: hand %d | old boundary %u edges/%u loops | planar recut +%.2f cm | new cut %u points/%u loops | cap %d SOLID-COLOR skinned tris | authored weights preserved | %u -> %u verts",hand,nb,loops,insetCm,cutN,cutLoops,g_cleanCapTris[hand],nv,outN);
    if(segUsed)ext_free(segUsed);if(bestLoop)ext_free(bestLoop);if(cutLoop)ext_free(cutLoop);ext_free(segs);ext_free(out);ext_free(best);ext_free(loopIdx);ext_free(used);ext_free(boundary);ext_free(edges);ext_free(src);return g_cleanVerts[hand]>0;
}
int main(int argc,char**argv){if(argc!=5)return 2;inputPath=argv[1];outputPath=argv[2];g_h5748Family=atoi(argv[3]);return h10_build_clean_mesh(atoi(argv[4]))?0:1;}
