/* Generic bounded packing helper; input metadata must be validated before writes. */
typedef struct{const u8*src;u64 bytes;u32 width;}CPU24Attr;
static i32 cpu24_pack(u8*dst,u64 capacity,const CPU24Attr*a,u32 n){
 if(!dst||!a||!n||n>16)return 0;
 u64 vertices=0,stride=0;
 for(u32 i=0;i<n;i++){u32 w=a[i].width;if(!a[i].src||!w||w>16||!a[i].bytes||a[i].bytes%w)return 0;u64 v=a[i].bytes/w;if(i&&v!=vertices)return 0;vertices=v;stride+=w;}
 if(!stride||capacity/stride!=vertices||capacity%stride)return 0;
 const u8*src[16];for(u32 i=0;i<n;i++)src[i]=a[i].src;
 for(u64 v=0;v<vertices;v++)for(u32 i=0;i<n;i++){
  u32 w=a[i].width;const u8*p=src[i];
  switch(w){case 16:__builtin_memcpy(dst,p,16);break;case 12:__builtin_memcpy(dst,p,12);break;case 8:__builtin_memcpy(dst,p,8);break;case 4:__builtin_memcpy(dst,p,4);break;default:for(u32 k=0;k<w;k++)dst[k]=p[k];break;}
  dst+=w;src[i]+=w;
 }
 return 1;
}
