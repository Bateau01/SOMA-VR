/* Observation only. Entered only inside the original main-thread SSE job. */
typedef struct {unsigned long long a,b;const void*body0,*body1;unsigned type0,type1,contacts;const void*pair,*raw10,*raw18;} C41Pair;
static C41Pair c41Pairs[2048];static unsigned c41Count,c41Overflow,c41Active;
static void(*c41Kernel)(void*,void*,float,int);
static void c41_pair(void*w,void*p,float dt,int thread){
 if(!c41Active){c41Kernel(w,p,dt,thread);return;}
 /* The original serial descriptor supplies index0. Fail closed for observations,
    never for collision evaluation, if an unrelated worker reaches this hook. */
 if(thread!=0||!C41_MAIN()){c41Kernel(w,p,dt,thread);return;}
 const void*b0=*(const void**)p,*b1=*(const void**)((unsigned char*)p+8);
 const void*raw10=*(const void**)((unsigned char*)p+0x10),*raw18=*(const void**)((unsigned char*)p+0x18);
 unsigned long long a=C41_NOW();c41Kernel(w,p,dt,thread);unsigned long long b=C41_NOW();
 if(c41Count>=2048){c41Overflow++;return;}
 C41Pair*q=c41Pairs+c41Count++;q->a=a;q->b=b;q->body0=b0;q->body1=b1;
 q->type0=*(unsigned*)((unsigned char*)*(void**)((unsigned char*)b0+0x200)+0x68);
 q->type1=*(unsigned*)((unsigned char*)*(void**)((unsigned char*)b1+0x200)+0x68);
 q->pair=p;q->raw10=raw10;q->raw18=raw18;
 q->contacts=*(unsigned short*)((unsigned char*)p+0x28);
}

