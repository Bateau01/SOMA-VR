static void cpu13_copy_cache(H5755DBHeldKindCache*d,const H5755DBHeldKindCache*s){volatile u8*o=(volatile u8*)d;const volatile u8*i=(const volatile u8*)s;for(u32 k=0;k<sizeof(*d);k++)o[k]=i[k];}
/* Shadow comparison: baseline result/state always returned to gameplay. */
static u8 h5755cy_check_held_world(float*push,void*shape,const float*m,void*w,const void*body,i32 hand,H5755DBHeldKindCache*cache){
 if(hand<0||hand>1||!cache||!cpuCounter)return cpu13_check_held_original(push,shape,m,w,body,hand,cache);
 u8 old[3]={g_h5755dgSweepSawFreeHand[hand],g_h5755dhQuerySawFreeHand[hand],g_h5755dhQuerySawExternal[hand]},flags[2][3],hits[2];float pushes[2][3];H5755DBHeldKindCache copies[2];cpu13_copy_cache(&copies[0],cache);cpu13_copy_cache(&copies[1],cache);static u32 order;
 for(u32 i=0;i<2;i++){u32 mode=i^(order&1);g_h5755dgSweepSawFreeHand[hand]=old[0];g_h5755dhQuerySawFreeHand[hand]=old[1];g_h5755dhQuerySawExternal[hand]=old[2];cpu13PairMode=mode;u64 t=0,q=0;cpuCounter(&t);hits[mode]=cpu13_check_held_original(pushes[mode],shape,m,w,body,hand,&copies[mode]);cpuCounter(&q);if(cpu13Phase<11)cpu13Totals[cpu13Phase][23+mode]+=q-t;flags[mode][0]=g_h5755dgSweepSawFreeHand[hand];flags[mode][1]=g_h5755dhQuerySawFreeHand[hand];flags[mode][2]=g_h5755dhQuerySawExternal[hand];}
 order++;cpu13PairMode=0;i32 bad=hits[0]!=hits[1];for(u32 i=0;i<3;i++)if(pushes[0][i]!=pushes[1][i]||flags[0][i]!=flags[1][i])bad=1;
 if(cpu13Phase<11){cpu13Totals[cpu13Phase][28]++;if(bad)cpu13Totals[cpu13Phase][25]++;}
 if(push)for(u32 i=0;i<3;i++)push[i]=pushes[0][i];g_h5755dgSweepSawFreeHand[hand]=flags[0][0];g_h5755dhQuerySawFreeHand[hand]=flags[0][1];g_h5755dhQuerySawExternal[hand]=flags[0][2];cpu13_copy_cache(cache,&copies[0]);return hits[0];
}
