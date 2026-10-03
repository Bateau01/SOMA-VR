/* XR_EXT_hand_joints_motion_range, extension 81. Request the complete virtual
   hand range rather than controller-constrained gripping. No touch gating. */
typedef struct {i32 type;const void* next;i32 range;} S26DNMotionRange;
_Static_assert(sizeof(S26DNMotionRange)==24,"motion range ABI");
static void s26dn_motion_range(S26QHandLocate* locate,S26DNMotionRange* range,i32 enabled){
    range->type=1000080000;range->next=locate->next;range->range=1;
    if(enabled)locate->next=range;
}
