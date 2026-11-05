/* Standalone prototype only. Same SSE job, partitioned as native generic path. */
static void(*c36Execute)(void*);static void(*c36Queue)(void*,void*);static void(*c36Join)(void*);
static unsigned c36Mx,c36Groups;static unsigned long long c36Runs;
static unsigned c36_getmx(void){unsigned v;__asm__ volatile("stmxcsr %0":"=m"(v));return v;}
static void c36_setmx(unsigned v){__asm__ volatile("ldmxcsr %0"::"m"(v));}
static void c36_job(void*arg){
 unsigned char*j=arg;
 if(*(int*)(j+0x18)!=1||*(int*)(j+0x10)!=1||*(int*)(j+8)!=0){unsigned old=c36_getmx();c36_setmx(c36Mx);c36Execute(j);c36_setmx(old);return;}
 void*w=*(void**)(j+0x20);int count=*(int*)(j+0x14),threads=*(int*)((unsigned char*)w+0x2250);
 if(count<32||threads<2||threads>8){c36Execute(j);return;}
 unsigned char saved[8][40];void*vt[1]={(void*)c36_job};int n=threads;
 c36Mx=c36_getmx();c36Groups=n;c36Runs++;
 for(int i=0;i<n;i++){
  unsigned char*q=j+i*40;memcpy(saved[i],q,40);
  *(void**)q=vt;*(int*)(q+8)=i;*(int*)(q+0x10)=n;
  *(int*)(q+0x14)=((count+n-1-i)/n)*n;*(int*)(q+0x18)=1;
  *(float*)(q+0x1c)=*(float*)(j+0x1c);*(void**)(q+0x20)=w;
 }
 for(int i=0;i<n;i++)c36Queue((unsigned char*)w+0x2250,j+i*40);
 c36Join((unsigned char*)w+0x2250);
 for(int i=0;i<n;i++)memcpy(j+i*40,saved[i],40);
}
