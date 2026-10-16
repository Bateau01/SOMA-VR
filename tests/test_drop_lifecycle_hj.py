from pathlib import Path
import subprocess,sys
r=Path(__file__).resolve().parents[1];s=(r/'source/s26n.c').read_text()
a=s.index('    H576AAInvItem* remoteItem=h576aa_inv_find_body(body);\n    if(remoteItem&&lastHolder)');b=s.index('\n',s.index('remoteItem->remoteDropped=',a));release=s[a:b]
a=s.index('    H576AAInvItem* remoteItem=h576aa_inv_find_body(body);if(remoteItem)');b=s.index('\n',a);hold=s[a:b]
code='''#include <cstdio>
#include <cstdlib>
using u8=unsigned char;
struct H576AAInvItem {int stowed,remoteDropped;}; H576AAInvItem item;
int found=1;H576AAInvItem* h576aa_inv_find_body(const void*){return found?&item:nullptr;}
void release(const void* body,int lastHolder,int normalRelease,int wasJointed,int wasCluster,int shoulderStow){'''+release+'''}
void hold(const void* body){'''+hold+'''}
int main(){int n=0;
for(int bits=0;bits<128;bits++){
 found=!(bits&64);item.stowed=!!(bits&32);item.remoteDropped=0;
 int last=!!(bits&1),normal=!!(bits&2),joint=!!(bits&4),cluster=!!(bits&8),stow=!!(bits&16);
 release((void*)1,last,normal,joint,cluster,stow);
 if(item.remoteDropped!=(found&&last&&normal&&!joint&&!cluster&&!stow&&!item.stowed))return 1;n++;
 item.remoteDropped=1;hold((void*)1);if(item.remoteDropped!=!found)return 2;n++;
}
printf("PASS %d exact production drop/regrab bookkeeping checks\\n",n);}
'''
p=r/'build/drop_lifecycle_hj.cpp';p.write_text(code);subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True);subprocess.run([str(p.with_suffix('.exe'))],check=True)
# Registered replacements cannot inherit drop authority; table compaction preserves it.
assert 'it->remoteDropped=0;it->raw=raw;it->owner=owner;' in s
assert 'd->stowed=q->stowed;d->remoteDropped=q->remoteDropped;' in s
old=r.parents[1]/'SOMA_VR_S26HI_ACCESS_VISIBILITY/repo'
for rel in ['source/omni_recall_gb.inc','source/item_grips_ej.inc']:
 assert (r/rel).read_bytes()==(old/rel).read_bytes(),rel
for p in (r/'runtime/script').rglob('*'):
 if p.is_file() and p.name!='MenuHandler.hps':assert p.read_bytes()==(old/p.relative_to(r)).read_bytes(),p
print('PASS unchanged interaction scripts, shared authored poses and recall implementation')

