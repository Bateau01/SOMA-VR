"""Private store-layout native-input fixture; never packaged."""
from pathlib import Path
r=Path(__file__).resolve().parents[1]
import shutil
(r/'build/store-ja-test/tests').mkdir(parents=True,exist_ok=True)
shutil.copy2(r/'tests/smaa_observer_iu.inc',r/'build/store-ja-test/tests/smaa_observer_iu.inc')
s=(r/'scripts/build_store.py').read_text().replace("'build/store-cpu65'","'build/store-ja-test'").replace("[args.zig,'cc']","[args.zig,'cc','-DS26IU_TEST=1']")
exec(compile(s,str(r/'scripts/build_store.py'),'exec'),{'__file__':str(r/'scripts/build_store.py'),'__name__':'__main__'})
