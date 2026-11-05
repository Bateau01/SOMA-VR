from pathlib import Path
import subprocess,json,zipfile,shutil,argparse,re
a=argparse.ArgumentParser();a.add_argument("--run-id",default="final");run=a.parse_args().run_id
assert re.fullmatch(r"[a-z0-9_-]{1,32}",run)
R=Path('.').resolve();B=R/('build/package-ji-'+run);B.mkdir(exist_ok=True)
setup=R/'installer-ji/output/SOMA-VR-1.1.1-S26JI-Setup.exe'
ps="$a=[Reflection.Assembly]::LoadFile('"+str(setup)+"');$s=$a.GetManifestResourceStream('payload.zip');$f=[IO.File]::Create('"+str(B/'embedded.zip')+"');$s.CopyTo($f);$f.Dispose();$s.Dispose()"
subprocess.run(['powershell','-NoProfile','-Command',ps],check=True)
with zipfile.ZipFile(B/'embedded.zip') as z:z.extractall(B/'payload')
with zipfile.ZipFile(B/'embedded.zip') as z:
 import hashlib
 manifest=json.loads(z.read('installer-manifest.json').decode('utf-8-sig'))
 for name,digest in manifest['Files'].items():assert hashlib.sha256(z.read(name)).hexdigest()==digest,name
 for name in ('SOMA-VR-Logging.dll','SOMA-VR-Support.ps1','Collect-SOMA-VR-Logs.cmd'):
  assert z.read(name)==(R/'runtime'/name).read_bytes()
 assert b'S26JI' in z.read('script/modules/MenuHandler.hps')
 assert not any(Path(n).name.lower() in ('agents.md','claude.md') or n.endswith(('.pdb','.lib')) for n in z.namelist())
old=R/'installer-jh/payload'
root=Path('D:/SteamLibrary/steamapps/common/SOMA/_ji_package_'+run);assert not root.exists()
compiler=Path('C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe');results=[]
for suite in ['FullTests','TransactionTests','UpdaterTests','CurrentUpgradeTests']:
 exe=B/(suite+'.exe');args=[str(compiler),'/nologo','/target:exe','/platform:x64','/main:'+suite,'/out:'+str(exe)]+['/r:'+s for s in ['System.Windows.Forms.dll','System.Drawing.dll','System.Web.Extensions.dll','System.IO.Compression.dll','System.IO.Compression.FileSystem.dll']]+[str(R/'installer-ji/source/Installer.cs'),str(R/'installer-ji/source'/(suite+'.cs'))]
 subprocess.run(args,check=True,capture_output=True)
 dest=root/(suite+' é');args=[str(exe),str(dest),str(B/'payload')]
 if suite=='UpdaterTests':args.append('D:/SteamLibrary/steamapps/common/SOMA/Soma.exe')
 if suite=='CurrentUpgradeTests':args=[str(exe),str(dest),str(old),str(B/'payload')]
 p=subprocess.run(args,capture_output=True,text=True,timeout=180);(B/(suite+'.log')).write_text(p.stdout+p.stderr,encoding='utf-8');results.append({'suite':suite,'passed':p.returncode==0,'lines':[s for s in p.stdout.splitlines() if 'PASS' in s]});print(json.dumps(results[-1]),flush=True)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
(B/'results.json').write_text(json.dumps(results,indent=2))
