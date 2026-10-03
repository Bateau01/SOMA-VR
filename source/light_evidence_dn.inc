/* Read-only evidence at the existing, bounded scene sample. Native 140284720
   prepares cLightArguments at renderer+A64; deferred_light_vtx/frag consume
   its matrices and ScreenToFarPlane coefficients. Values below are native
   inputs, not a claim that the GPU drew a particular shadow pixel. */
static void s26dn_light_evidence(void* renderer,u32 frame,i32 eye){
    static u32 samples[2];
    if(eye<0||eye>1||samples[eye]>=48u||!renderer)return;
    u8* r=(u8*)renderer;
    if(!h20_mem_readable(r+0x40u,8u)||!h20_mem_readable(r+0xa64u,0x1e0u))return;
    ++samples[eye];
    const float* p=(const float*)(r+0xaa4u); /* transposed native projection */
    const float* v=(const float*)(r+0xae4u);
    const float* q=(const float*)(r+0xbf4u);
    ext_Log(">>> S26DN LIGHT_INPUT frame %u eye %d size %d/%d projection %.6f/%.6f offset %.6f/%.6f viewT %.6f/%.6f/%.6f far %.6f screenToFar %.6f/%.6f/%.6f/%.6f invSize %.8f/%.8f",
        frame,eye,*(i32*)(r+0x40u),*(i32*)(r+0x44u),p[0],p[5],p[8],p[9],v[12],v[13],v[14],*(float*)(r+0xbe4u),q[0],q[1],q[2],q[3],q[4],q[5]);
    /* Native light buckets: box, unshadowed, shadowed. Observe existing lists
       only; never enumerate the world or recompute visibility/shadow jobs. */
    if(!h20_mem_readable(r+0x23c8u,0x50u))return;
    for(i32 group=0;group<3;++group){
        u64 begin=*(u64*)(r+0x23c8u+group*32u),end=*(u64*)(r+0x23d0u+group*32u);
        if(end<begin||(end-begin)%8u||(end-begin)/8u>4096u)continue;
        u32 count=(u32)((end-begin)/8u),take=count<8u?count:8u;
        if(!h20_mem_readable((void*)begin,take*8u))continue;
        for(u32 n=0;n<take;++n){
            u8* light=*(u8**)(begin+n*8u);if(!light||!h20_mem_readable(light+0x1c0u,0xf0u))continue;
            ext_Log(">>> S26DN LIGHT_MEMBER frame %u eye %d group %d index %u/%u light %p type %d casts %u radius %.4f",
                frame,eye,group,n,count,light,*(i32*)(light+0x1c0u),(u32)light[0x2acu],*(float*)(light+0x298u));
        }
    }
}
