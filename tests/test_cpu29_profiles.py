from pathlib import Path
import re,struct,hashlib,json
r=Path(__file__).resolve().parents[1];src=(r/'source/cpu_streaming.inc').read_text()
names=('update','prepare','dtor','dtor','module','upload','convert','count','data','scalarDelete')
rvas=(0x46b410,0x45eef0,0x23d4d0,0x147cc0,0x15a390,0x56be20,0x24f2c0,0x581e00,0x581dc0,0x64ae54)
sigs={n:bytes(int(v.strip(),0) for v in re.search(r'const u8 '+n+r'\[\]=\{([^}]+)\}',src)[1].split(',')) for n in names}
def read(b,rva,size):
 pe=struct.unpack_from('<I',b,0x3c)[0];count=struct.unpack_from('<H',b,pe+6)[0];opt=struct.unpack_from('<H',b,pe+20)[0]
 for i in range(count):
  p=pe+24+opt+i*40;vs,va,rs,raw=struct.unpack_from('<IIII',b,p+8)
  if va<=rva and rva+size<=va+rs:return b[raw+rva-va:raw+rva-va+size]
 return b''
results=[]
for edition,path in [('Steam',r'D:\SteamLibrary\steamapps\common\SOMA\Soma.exe'),('Epic',r'C:\Program Files\Epic Games\SOMA\Soma.exe'),('GOG',r'C:\Program Files\GOG Galaxy\Games\SOMA\Soma.exe')]:
 p=Path(path);assert p.is_file(),path;b=p.read_bytes();checks=[read(b,a,len(sigs[n]))==sigs[n] for a,n in zip(rvas,names)]
 accepted=all(checks);assert accepted==(edition=='Steam'),(edition,checks)
 results.append({'edition':edition,'exe_sha256':hashlib.sha256(b).hexdigest(),'release_group_eligible':accepted,'signature_matches':checks})
(r/'audit/cpu29-profiles.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
print('PASS exact Steam guards; Epic/GOG rejected by new group and retain existing runtime. Static executable checks only.')
