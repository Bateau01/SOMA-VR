from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1];s=(R/'source/desktop_settings_dz.inc').read_text();s=s[:s.index('static void s26dz_install_save_options')]
head=r'''
#include <stdio.h>
#include <stdint.h>
#include <string.h>
typedef int i32;typedef unsigned u32;typedef unsigned char u8;
#define ext_Log(...) ((void)0)
static int readable=1;
static int h20_mem_readable(void*p,unsigned n){return readable;}
#define C(x) do{if(!(x)){printf("FAIL %d\n",__LINE__);return 1;}}while(0)
'''
body=r'''
static int savedW,savedH,calls;
static void __attribute__((ms_abi)) save(void*p){calls++;if(p){savedW=*(int*)((u8*)p+0x64);savedH=*(int*)((u8*)p+0x68);}}
int main(void){
 u8 object[128],before[128];memset(object,0x5a,sizeof(object));o_s26dzSaveOptions=save;
 *(int*)(object+0x64)=2574;*(int*)(object+0x68)=1431;memcpy(before,object,sizeof(object));
 s26dz_save_options(object);C(savedW==2574&&savedH==1431); // Flat/no VR request: native path.
 s26dz_desktop_request(2560,1440);s26dz_save_options(object);C(savedW==2560&&savedH==1440&&memcmp(before,object,sizeof(object))==0);
 *(int*)(object+0x64)=1936;*(int*)(object+0x68)=1067;s26dz_desktop_request(1920,1080);s26dz_save_options(object);C(savedW==1920&&savedH==1080&&*(int*)(object+0x64)==1936);
 s26dz_desktop_request(3440,1440);s26dz_save_options(object);C(savedW==3440&&savedH==1440);
 s26dz_desktop_request(~0u,0);s26dz_save_options(object);C(savedW==3440&&savedH==1440);
 readable=0;s26dz_save_options(object);C(savedW==1936&&savedH==1067);
 s26dz_save_options(0);C(calls==7);
 puts("PASS native save receives selected resolution; odd client sizes excluded, object restored, flat/invalid paths unchanged");return 0;
}
'''
B=R/'build';B.mkdir(exist_ok=True);p=B/'desktop_settings.c';p.write_text(head+s+body)
subprocess.run([sys.argv[1],'cc',str(p),'-o',str(p.with_suffix('.exe'))],check=True);subprocess.run([str(p.with_suffix('.exe'))],check=True)
# Verify the actual native serialization path against the distributed executable.
import struct
exe=Path(r'D:\SteamLibrary\steamapps\common\SOMA\Soma.exe').read_bytes();pe=struct.unpack_from('<I',exe,60)[0];n=struct.unpack_from('<H',exe,pe+6)[0];op=struct.unpack_from('<H',exe,pe+20)[0]
for i in range(n):
 off=pe+24+op+i*40;vs,va,rs,ro=struct.unpack_from('<4I',exe,off+8)
 if va<=0x5d1f0<va+max(vs,rs):assert exe[ro+0x5d1f0-va:ro+0x5d1f0-va+16].hex()=='488bc45541544155488d68a14881ecb0';break
else:raise AssertionError('native save target missing')
print('PASS native hook signature matches local Steam executable')
