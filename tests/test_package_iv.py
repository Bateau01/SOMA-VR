from pathlib import Path
import subprocess,json,zipfile,shutil
R=Path('.').resolve();B=R/'build/iv-installer-test';B.mkdir(exist_ok=True)
setup=R/'installer/output/SOMA-VR-1.0.9-S26IV-Setup.exe'
ps="$a=[Reflection.Assembly]::LoadFile('"+str(setup)+"');$s=$a.GetManifestResourceStream('payload.zip');$f=[IO.File]::Create('"+str(B/'embedded.zip')+"');$s.CopyTo($f);$f.Dispose();$s.Dispose()"
subprocess.run(['powershell','-NoProfile','-Command',ps],check=True)
with zipfile.ZipFile(B/'embedded.zip') as z:z.extractall(B/'payload')
old=R/'build/iu-installer-test/payload';assert json.loads((old/'installer-manifest.json').read_text(encoding='utf-8-sig'))['Version']=='1.0.9-S26IU'
root=Path('D:/SteamLibrary/steamapps/common/SOMA/_iv_package_tests').resolve();assert str(root).lower().startswith('d:\\steamlibrary\\steamapps\\common\\soma\\_iv_package_tests') and not root.exists()
compiler=Path('C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe');results=[]
for suite in ['FullTests','TransactionTests','UpdaterTests','CurrentUpgradeTests']:
 exe=B/(suite+'.exe');args=[str(compiler),'/nologo','/target:exe','/platform:x64','/main:'+suite,'/out:'+str(exe)]+['/r:'+s for s in ['System.Windows.Forms.dll','System.Drawing.dll','System.Web.Extensions.dll','System.IO.Compression.dll','System.IO.Compression.FileSystem.dll']]+[str(R/'installer/source/Installer.cs'),str(R/'installer/source'/(suite+'.cs'))]
 subprocess.run(args,check=True,capture_output=True)
 dest=root/(suite+' é');args=[str(exe),str(dest),str(B/'payload')]
 if suite=='UpdaterTests':args.append('D:/SteamLibrary/steamapps/common/SOMA/Soma.exe')
 if suite=='CurrentUpgradeTests':args=[str(exe),str(dest),str(old),str(B/'payload')]
 p=subprocess.run(args,capture_output=True,text=True,timeout=180);(B/(suite+'.log')).write_text(p.stdout+p.stderr,encoding='utf-8');results.append({'suite':suite,'passed':p.returncode==0,'lines':[s for s in p.stdout.splitlines() if 'PASS' in s]});print(json.dumps(results[-1]),flush=True)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
(B/'results.json').write_text(json.dumps(results,indent=2))
