static i32 h5748n_copy_tstring(void*,char*,u32);
/* Bounded identity logging after generation; not part of the timed pair span.
   Identity deduplication suppresses logging only, never a collision query. */
static const void*c41Named[64];static unsigned c41NamedCount;
static void c41_name(const void*b){
 if(!b)return;for(unsigned i=0;i<c41NamedCount;i++)if(c41Named[i]==b)return;if(c41NamedCount>=64)return;
 c41Named[c41NamedCount++]=b;char name[96];name[0]=0;void*w=p_h14GetUserData?p_h14GetUserData(b):0;
 if(w)h5748n_copy_tstring((u8*)w+0x10,name,sizeof(name));
 i32 root=b==g_h34HandNewton[0]?0:b==g_h34HandNewton[1]?1:-1; i32 held=b==g_h14GripBody[0]?0:b==g_h14GripBody[1]?1:-1;
 ext_Log(">>> CPU41_BODY step %u body %p wrapper %p name [%s] root %d held %d",g_h14PhysicsSteps,b,w,name,root,held);
}
