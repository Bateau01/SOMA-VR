/* A matching collision-query result must not flicker with the manifold bit. */
static float s26al_visual_target(float raw,float query,i32 valid,i32 contact,i32 matching){
    return valid&&(contact||matching)?clamp01(query):raw;
}
