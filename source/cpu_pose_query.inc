/* Pose-rebuild preflight only. Reject disjoint compound children through the
   established native-equivalent query helper. A hit, including zero depth,
   remains a rejection of the proposed hand shape. No result survives a pair.
   See docs/CPU72_VALIDATION.md. Not used by acquisition or solver callbacks. */
static u8 ct_pose_shape_collision(void*w,void*a,const float*am,void*b,const float*bm,void*data,i32 limit,u8 correct,i32 thread){
 g_ctQueryCache.shape=0;
 u8 hit=ct_check_shape_collision(w,a,am,b,bm,data,limit,correct,thread);
 g_ctQueryCache.shape=0;
 return hit;
}
