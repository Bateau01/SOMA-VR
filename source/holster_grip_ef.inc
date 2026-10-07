/* Pure holster draw geometry: an item-local authored rotation and grip anchor
   are applied once relative to the hand. Never inherit the item's old world
   rotation or the hand/world-scale factor. Ordinary regrabs do not call this. */
static i32 s26ef_grip_unit(float* v){
    float n=v[0]*v[0]+v[1]*v[1]+v[2]*v[2];
    if(!(n>.000001f&&n<1000000.0f))return 0;
    float inv=1.0f/ext_Sqrtf(n);for(i32 i=0;i<3;++i)v[i]*=inv;return 1;
}
static i32 s26ef_holster_matrix(const float* hand,const float* rotation,
                               const float* bodyAnchor,const float* contact,float* out){
    if(!hand||!rotation||!bodyAnchor||!contact||!out)return 0;
    for(i32 i=0;i<16;++i)if(!(hand[i]>-100000.0f&&hand[i]<100000.0f))return 0;
    for(i32 i=0;i<3;++i)if(!(bodyAnchor[i]>-10&&bodyAnchor[i]<10&&contact[i]>-100000&&contact[i]<100000))return 0;
    for(i32 i=0;i<9;++i)if(!(rotation[i]>=-1.001f&&rotation[i]<=1.001f))return 0;
    /* Profiles must be proper rigid rotations: no scale, skew or reflection. */
    for(i32 a=0;a<3;++a)for(i32 b=a;b<3;++b){
        float dot=0;for(i32 j=0;j<3;++j)dot+=rotation[a*3+j]*rotation[b*3+j];
        float expected=a==b?1.0f:0.0f;if(!(dot>expected-.001f&&dot<expected+.001f))return 0;
    }
    float det=rotation[0]*(rotation[4]*rotation[8]-rotation[5]*rotation[7])-
              rotation[3]*(rotation[1]*rotation[8]-rotation[2]*rotation[7])+
              rotation[6]*(rotation[1]*rotation[5]-rotation[2]*rotation[4]);
    if(!(det>.999f&&det<1.001f))return 0;
    float x[3]={hand[0],hand[1],hand[2]},y[3]={hand[4],hand[5],hand[6]};
    if(!s26ef_grip_unit(x))return 0;
    float dot=x[0]*y[0]+x[1]*y[1]+x[2]*y[2];for(i32 j=0;j<3;++j)y[j]-=x[j]*dot;
    if(!s26ef_grip_unit(y))return 0;
    float z[3]={x[1]*y[2]-x[2]*y[1],x[2]*y[0]-x[0]*y[2],x[0]*y[1]-x[1]*y[0]};
    if(!(z[0]*hand[8]+z[1]*hand[9]+z[2]*hand[10]>.00001f))return 0;
    float result[16];for(i32 col=0;col<3;++col){
        for(i32 row=0;row<3;++row)result[col*4+row]=x[row]*rotation[col*3]+y[row]*rotation[col*3+1]+z[row]*rotation[col*3+2];
        result[col*4+3]=0;
    }
    for(i32 row=0;row<3;++row)result[12+row]=contact[row]-result[row]*bodyAnchor[0]-result[4+row]*bodyAnchor[1]-result[8+row]*bodyAnchor[2];
    result[15]=1;for(i32 i=0;i<16;++i)out[i]=result[i];return 1;
}
