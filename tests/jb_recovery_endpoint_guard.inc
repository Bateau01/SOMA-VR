/* Conservative recovery-only envelope check. Newton's overlap/sweep queries
   miss some initially embedded thin shapes. Rays through the envelope's twelve
   edges and three centre axes, in BOTH directions, also reject t=0 containment.
   A bounding envelope can reject otherwise clear finger gaps; rejection is safe.
   Does not replace normal physical-hand collision or authorize recovery alone. */
static i32 jb_recovery_endpoint_clear(const void* collision,const float* bodyM,const float* lo,const float* hi){
 if(!collision||!p_h43CollisionRayCast)return 0;
 float inverse[16];h14_rigid_inverse(bodyM,inverse);
 for(i32 axis=0;axis<3;axis++)for(i32 sample=0;sample<5;sample++){
  float a[4]={0},b[4]={0},la[4]={0},lb[4]={0},normal[4]={0};i32 id=0;
  i32 side=0;
  for(i32 j=0;j<3;j++){
   if(j==axis){a[j]=lo[j];b[j]=hi[j];}
   else {a[j]=b[j]=sample==4?(lo[j]+hi[j])*.5f:((sample&(1<<side))?hi[j]:lo[j]);side++;}
  }
  h14_transform_point(inverse,a,la);h14_transform_point(inverse,b,lb);
  float t=p_h43CollisionRayCast(collision,la,lb,normal,&id);
  if(!h9_good(t,10)||t<0||t<=1.f)return 0;
  t=p_h43CollisionRayCast(collision,lb,la,normal,&id);
  if(!h9_good(t,10)||t<0||t<=1.f)return 0;
 }
 return 1;
}
