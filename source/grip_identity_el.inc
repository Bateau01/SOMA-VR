/* Script-owned profile metadata. No physics, inventory or story authority. */
typedef struct {const void* raw;void* owner;char profile[96];} S26ELGripIdentity;
static S26ELGripIdentity g_s26elGripIdentity[64];
static u32 g_s26elGripIdentityCount;static char g_s26elGripScope[96];
static void s26el_grip_reset(void){zero_bytes(g_s26elGripIdentity,sizeof(g_s26elGripIdentity));g_s26elGripIdentityCount=0;g_s26elGripScope[0]=0;}
static void s26el_grip_body(const void* raw,void* owner){
 if(!raw||!owner||!g_s26elGripScope[0])return;
 u32 i;for(i=0;i<g_s26elGripIdentityCount;++i)if(g_s26elGripIdentity[i].raw==raw||g_s26elGripIdentity[i].owner==owner)break;
 if(i>=64u)return;if(i==g_s26elGripIdentityCount)g_s26elGripIdentityCount++;
 if(g_s26elGripIdentity[i].raw==raw&&g_s26elGripIdentity[i].owner==owner&&h576c_ci_streq(g_s26elGripIdentity[i].profile,g_s26elGripScope))return;
 ext_Log(">>> S26EL AUTHORED PROFILE: %s body %p owner %p",g_s26elGripScope,raw,owner);
 g_s26elGripIdentity[i].raw=raw;g_s26elGripIdentity[i].owner=owner;h5748n_copyz(g_s26elGripIdentity[i].profile,96,g_s26elGripScope);
}
static const char* s26el_grip_profile(const void* body,const char* fallback){
 void* owner=h482_body_owner(body,0);if(!owner)return fallback;
 for(u32 i=0;i<g_s26elGripIdentityCount;++i)if(g_s26elGripIdentity[i].raw==body&&g_s26elGripIdentity[i].owner==owner)return g_s26elGripIdentity[i].profile;
 return fallback;
}
