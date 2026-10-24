from pathlib import Path
import shutil,subprocess,sys
R=Path(__file__).resolve().parents[1];T=R/'build/roomscale-research';T.mkdir(exist_ok=True)
for folder in ('source','scripts','reference','third_party'):shutil.copytree(R/folder,T/folder,dirs_exist_ok=True)
probe=(R/'tests/roomscale_sweep_probe.inc').read_text()
for mode in ('steam','store'):
 p=T/'source/roomscale_hr.inc';s=(R/'source/roomscale_hr.inc').read_text()
 s='#define RS_FIT_RVA '+('0x23f1d0' if mode=='steam' else '0x238df0')+'\n'+probe+'\n'+s
 s=s.replace('static i32 s26hr_room_token(const H5730TString* cls,const H5730TString* fn){','static i32 s26hr_room_token(const H5730TString* cls,const H5730TString* fn){\n if(h5748t_sso_eq(fn,"PROBE",5u))return rs_probe();')
 p.write_text(s)
 subprocess.run([sys.executable,str(T/'scripts'/('build.py' if mode=='steam' else 'build_store.py')),'--zig',sys.argv[1]],check=True)
 src=T/('build/hpl3vr.dll' if mode=='steam' else 'build/store/hpl3vr-store.dll')
 shutil.copy2(src,R/f'build/roomscale-probe-{mode}.dll')
