"""Read-only compatibility tests. Mutated executable fixtures are NEVER launched."""
from pathlib import Path
import argparse,subprocess,json,struct,shutil
p=argparse.ArgumentParser();p.add_argument('--game-exe',required=True);p.add_argument('--alternate-exe');a=p.parse_args()
r=Path(__file__).resolve().parents[1];out=r/'audit/compatibility';out.mkdir(parents=True,exist_ok=True)
b=Path(a.game_exe).read_bytes();e=struct.unpack_from('<I',b,60)[0];o=e+24;table=o+struct.unpack_from('<H',b,e+20)[0]
sections={}
for i in range(struct.unpack_from('<H',b,e+6)[0]):
 t=table+40*i;sections[b[t:t+8].split(b'\0')[0].decode()]=struct.unpack_from('<I',b,t+20)[0]
fixtures={'verified':(b,'VerifiedExecutable'),'overlay':(b+b'TEST-UNMAPPED-TRAILER','EquivalentEngineUnverified')}
for name,offset,status in [('checksum',o+64,'EquivalentEngineUnverified'),('resource',sections['.rsrc']+128,'EquivalentEngineUnverified'),('code',sections['.text']+128,'Incompatible'),('data',sections['.data']+128,'Incompatible')]:
 v=bytearray(b);v[offset]^=1;fixtures[name]=(bytes(v),status)
fixtures['truncated']=(b[:100],'ERROR')
v=bytearray(b);struct.pack_into('<H',v,e+4,0x14c);fixtures['x86']=(bytes(v),'ERROR')
if a.alternate_exe:fixtures['alternate']=(Path(a.alternate_exe).read_bytes(),'Incompatible')
for name,(data,expected) in fixtures.items():(out/(name+'.exe')).write_bytes(data)
q=lambda x:"'"+str(x).replace("'","''")+"'"
ps="Import-Module (Join-Path $PSHOME 'Modules\\Microsoft.PowerShell.Utility'); Import-Module (Join-Path $PSHOME 'Modules\\Microsoft.PowerShell.Management'); . "+q(r/'runtime/SOMA-VR-Compatibility.ps1')+"\n$results=@()\n"
for name,(_,expected) in fixtures.items():
 ps+="try {$r=Get-SomaExecutableReport "+q(out/(name+'.exe'))+' '+q(r/'runtime/SOMA-VR-Executable.json')+"; $status=$r.status} catch {$status='ERROR'}\n"
 ps+="$results += [pscustomobject]@{name="+q(name)+";status=$status}\n"
ps+='$results | ConvertTo-Json -Compress\n'
res=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-Command',ps],capture_output=True,text=True);assert res.returncode==0,res.stderr
checks=json.loads(res.stdout)
for row in checks:assert row['status']==fixtures[row['name']][1],row
# Exercise the actual launcher preflight in an isolated folder. CheckOnly must
# stop before process cleanup, default-file copying, C# injection setup or launch.
f=out/'launcher';f.mkdir(exist_ok=True)
for name in ['Launch-SOMA-VR.ps1','SOMA-VR-Compatibility.ps1','SOMA-VR-Executable.json']:
 shutil.copy2(r/'runtime'/name,f/name)
for name in ['hpl3vr.dll','hpl3vr-store.dll','hpl3vr_inject.exe','openxr_loader.dll']:(f/name).write_bytes(b'CHECKONLY-MUST-NOT-LOAD')
cases=[('verified',[],True),('resource',[],True),('code',['-Experimental'],False),('verified',['-Executable','not-soma.exe'],False)]
if a.alternate_exe:cases.append(('alternate',[],True))
for source,extra,ok in cases:
 (f/'Soma.exe').write_bytes(fixtures[source][0])
 c=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(f/'Launch-SOMA-VR.ps1'),'-CheckOnly']+extra,capture_output=True,text=True)
 assert (c.returncode==0)==ok,(source,c.stdout,c.stderr)
 assert not (f/'hpl3vr_vr_settings.ini').exists()
 assert not (f/'hpl3vr_hand_calibration.ini').exists()
 if source=='alternate':
  report=json.loads((f/'SOMA-VR-compatibility-report.json').read_text(encoding='utf-8-sig'))
  assert report['runtime_dll']=='hpl3vr-store.dll'
 checks.append({'name':'launcher_'+source+'_'+'_'.join(extra),'passed':True})
result={'checks':len(checks),'passed':True,'cases':checks,'scope':'PE comparison and actual launcher CheckOnly. No mutated fixture, alternate storefront executable, injector or game was launched.'}
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))



