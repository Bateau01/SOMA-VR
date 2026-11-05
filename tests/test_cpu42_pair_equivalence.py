"""Native repeated-pair outcome audit. Calls are observed, never skipped."""
from pathlib import Path
import subprocess,sys,json,hashlib
r=Path(__file__).resolve().parents[1];b=r/'build/cpu42-native';b.mkdir(exist_ok=True)
s=(r/'build/cpu41-native/test.c').read_text()
s=s.replace('const void*pair,*raw10,*raw18;} C41Pair;', 'const void*pair,*raw10,*raw18;unsigned char input[48],output[48];} C41Pair;')
s=s.replace('unsigned long long a=C41_NOW();c41Kernel', 'unsigned char input[48];memcpy(input,p,48);unsigned long long a=C41_NOW();c41Kernel')
s=s.replace('q->contacts=*(unsigned short*)', 'memcpy(q->input,input,48);memcpy(q->output,p,48);q->contacts=*(unsigned short*)')
s=s.replace('static DWORD c41Main;', 'static unsigned long long repeats,identical,zeros,zeroMismatch,positiveMismatch;static DWORD c41Main;')
needle='c41Types|=1u<<q->type1;}'
assert s.count(needle)==1
s=s.replace(needle,needle[:-1]+r'''
 for(unsigned k=0;k<z;k++){C41Pair*t=c41Pairs+k;
  if(t->body0!=q->body0||t->body1!=q->body1)continue;
  repeats++;
  /* Scratch destination is assigned per pair. Compare every other input byte,
     including the flags/contact fields, rather than assuming they are unused. */
  if(memcmp(t->input,q->input,32)||memcmp(t->input+40,q->input+40,8))continue;
  identical++;int mismatch=memcmp(t->output,q->output,32)||memcmp(t->output+40,q->output+40,8);
  if(!t->contacts){zeros++;zeroMismatch+=mismatch;}else positiveMismatch+=mismatch;
  break;
 }
}''')
s=s.replace('printf("PAIR_RECORDS', 'printf("EQUIVALENCE repeats=%llu identical=%llu zeros=%llu zeroMismatch=%llu positiveMismatch=%llu\\n",repeats,identical,zeros,zeroMismatch,positiveMismatch);printf("PAIR_RECORDS')
(b/'test.c').write_text(s)
subprocess.run([sys.argv[1],'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe')],capture_output=True,text=True,timeout=180)
(r/'audit/cpu42-equivalence.json').write_text(json.dumps(dict(scope=__doc__,exit=x.returncode,output=x.stdout+x.stderr,source_sha256=hashlib.sha256(s.encode()).hexdigest()),indent=2))
print(x.stdout+x.stderr);raise SystemExit(x.returncode)
