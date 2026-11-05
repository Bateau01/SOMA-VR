static i32 cpu_ascii_baseline(const void* p,char* out,u32 cap){
    if(!p||!out||cap<6||!h20_mem_readable(p,1))return 0;const unsigned char* s=(const unsigned char*)p;u32 n=0,alpha=0;
    for(;n+1<cap&&n<63;++n){if(!h20_mem_readable(s+n,1))return 0;unsigned char c=s[n];if(c==0)break;if(c<32||c>126)return 0;if((c>='A'&&c<='Z')||(c>='a'&&c<='z'))alpha++;out[n]=(char)c;}
    if(n<4||alpha<2||n>=63)return 0;out[n]=0;return 1;
}
