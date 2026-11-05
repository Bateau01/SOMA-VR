from pathlib import Path
r=Path(__file__).resolve().parents[1]
s=(r/'tests/build_iz_profile.py').read_text()
s=s.replace("tests/iz_physics_replay.inc","tests/jb_hand_replay.inc")
needle='s=s[:a]+post+s[z:]'
assert s.count(needle)==1
s=s.replace(needle,needle+"\ns=s.replace('h5755eg_phys_add_since(H5755EG_P_POST,egPost)', 'jb_hand_observe();h5755eg_phys_add_since(H5755EG_P_POST,egPost)')\ns='static void jb_hand_observe(void);\\n'+s")
# Keep outputs separate from older profile evidence.
s=s.replace("s=s.replace(\"s=s.replace", "s=s.replace(\"b=r/'build/movement'\",\"b=r/'build/jb-hand'\")\ns=s.replace(\"s=s.replace",1)
exec(compile(s,str(r/'tests/build_iz_profile.py'),'exec'),{'__file__':str(r/'tests/build_iz_profile.py'),'__name__':'__main__'})
