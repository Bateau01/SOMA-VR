"""Private native GUI-destruction observer. No installed game changes."""
from pathlib import Path
import shutil,sys,json,hashlib
r=Path(__file__).resolve().parents[1]
baseline='--without-lifetime' in sys.argv
if baseline:sys.argv.remove('--without-lifetime')
folder='build/jb-cursor-baseline' if baseline else 'build/jb-cursor';b=r/folder
shutil.copytree(r/'source',b/'source',dirs_exist_ok=True)
shutil.copytree(r/'third_party/smaa',b/'third_party/smaa',dirs_exist_ok=True)
p=b/'source/terminal_cursor_an.inc';s=p.read_text()
if baseline:
 s=s.replace('    if(ext_MH_CreateHook(base+offsets[3],(void*)s26jb_gui_destroy,(void**)&o_s26jbGuiDestroy)||ext_MH_EnableHook(base+offsets[3]))return;','')
s=s.replace('    s26jb_forget_terminal(self);','    static u32 observed=0;u32 before=g_s26bvGuiCount;\n    s26jb_forget_terminal(self);\n    if(observed++<32)ext_Log("JB_GUI_DESTROY before %u after %u self %p",before,g_s26bvGuiCount,self);')
p.write_text(s)
s=(r/'scripts/build_smaa_test_iu.py').read_text()
s=s.replace("B=R/('build/native-runtime' if args.production else 'build/smaa-test')", "B=R/"+repr(folder))
s=s.replace("str(R/'source/s26n.c')","str(B/'source/s26n.c')")
exec(compile(s,str(r/'scripts/build_smaa_test_iu.py'),'exec'),{'__file__':str(r/'scripts/build_smaa_test_iu.py'),'__name__':'__main__'})
receipt=b/'build-receipt.json';d=json.loads(receipt.read_text());d['private_observer']='native destructor entry/count only';d['compiled_source_hashes']={p.relative_to(b).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (b/'source').glob('*') if p.is_file()};receipt.write_text(json.dumps(d,indent=2))
