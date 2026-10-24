/* Visual orientation only. Pure lookup: no curl, ownership, latch or body writes.
   Keep the existing guide center; this is not a full collision-bound grip pose. */
static i32 s26_phone_guide_frame(const float* basis9,const float* center,float* frame){
    const S26EJGrip* grip=s26el_default_grip(1,2,"Phone");if(!grip)return 0;
    float basis[16]={0},anchor[3]={0};
    for(i32 col=0;col<3;++col)for(i32 row=0;row<3;++row)basis[col*4+row]=basis9[col*3+row];
    basis[15]=1;
    return s26ef_holster_matrix(basis,grip->rotation,anchor,center,frame);
}
