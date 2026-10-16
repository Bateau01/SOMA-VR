/* FY: original asymmetric shoulder volume. In s26r_shoulder_yaw's basis,
   +Z is tracked rearward (OpenXR +Z), NOT HPL camera forward. Keep the old
   front/lateral/vertical limits and taper an extra 8 cm toward the rear.
   Distances are physical metres; caller converts from game units once.
   No world queries, model assets, allocations or finger-pose dependency. */
#define S26FY_REAR_REACH_M 0.08f
static float s26fy_slot_score(float x,float y,float z,float radius){
    float rx=radius*1.5f,ry=radius;
    float rz=radius*g_h576apSlotDepthScale+(z>0.0f?S26FY_REAR_REACH_M:0.0f);
    x/=rx;y/=ry;z/=rz;
    return x*x+y*y+z*z;
}

/* FZ: deposit-only lower/rear lobe, unioned with the existing retrieval core.
   The lobe's frontmost point is local Z=0; its lateral width is unchanged.
   Physical metres, independent of item/model dimensions and world scale. */
#define S26FZ_DEPOSIT_DOWN_M 0.08f
#define S26FZ_DEPOSIT_HEIGHT_M 0.025f
#define S26FZ_DEPOSIT_DEPTH_M 0.04f
static float s26fz_deposit_score(float x,float y,float z,float radius){
    float core=s26fy_slot_score(x,y,z,radius);
    if(z<=0.0f)return core; /* never expand the face/front side */
    float rx=radius*1.5f,ry=radius+S26FZ_DEPOSIT_HEIGHT_M;
    float rz=radius*g_h576apSlotDepthScale+S26FZ_DEPOSIT_DEPTH_M;
    x/=rx;y=(y+S26FZ_DEPOSIT_DOWN_M)/ry;z=(z-rz)/rz;
    float lobe=x*x+y*y+z*z;
    return core<lobe?core:lobe;
}
