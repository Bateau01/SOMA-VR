/* Script registers only two verified moving-body assets. No new Newton object,
   body flags, transform, mass or joint is changed. Called with a live body from
   the hand-pair callback; stored owner addresses are compared, never dereferenced.
   Registration runs outside NewtonUpdate and is reset with the world registry. */
typedef struct {u32 id;void* owner;u8 used;} S26JBSolid;
static S26JBSolid g_s26jbSolid[32];
static i32 g_s26jbSolidCount;
static void s26jb_solid_reset(void){zero_bytes(g_s26jbSolid,sizeof(g_s26jbSolid));g_s26jbSolidCount=0;}
static i32 s26jb_solid_token(const H5730TString* text,const H5730TString* cmd){
    u32 id=0;if(!s26y_id(text,&id))return 0;
    i32 remove=h5748t_sso_eq(cmd,"U",1u);
    if(!remove&&(!h5748t_sso_eq(cmd,"S",1u)||!s26y_gate()||ni_native_input()||!g_s26yOwner||!g_s26yMainRaw))return 0;
    i32 slot=-1;
    for(i32 i=0;i<g_s26jbSolidCount;i++)if(g_s26jbSolid[i].used&&g_s26jbSolid[i].id==id){slot=i;break;}
    if(remove){if(slot>=0)zero_bytes(&g_s26jbSolid[slot],sizeof(g_s26jbSolid[slot]));return 1;}
    if(slot<0)for(i32 i=0;i<32;i++)if(!g_s26jbSolid[i].used){slot=i;if(i>=g_s26jbSolidCount)g_s26jbSolidCount=i+1;break;}
    if(slot<0)return 0;
    g_s26jbSolid[slot].id=id;g_s26jbSolid[slot].owner=g_s26yOwner;g_s26jbSolid[slot].used=1;return 1;
}
static i32 s26jb_solid_body(const void* body){
    if(!g_s26jbSolidCount||!body||!s26y_gate()||ni_native_input()||!p_h14GetUserData)return 0;
    void* w=p_h14GetUserData(body);
    if(!w||!h20_mem_readable(w,0x2f0u)||*(const void**)((u8*)w+0x2e8)!=body||!*(u8*)((u8*)w+0xe4))return 0;
    u32 id=*(u32*)((u8*)w+0x3c);void* owner=*(void**)((u8*)w+0x2c0);
    for(i32 i=0;i<g_s26jbSolidCount;i++)if(g_s26jbSolid[i].used&&g_s26jbSolid[i].id==id&&g_s26jbSolid[i].owner==owner)return 1;
    return 0;
}
