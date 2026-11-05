"""Private real-XR/synthetic controller acquisition fixture, no release payload."""
from pathlib import Path
r=Path(__file__).resolve().parents[1]
s=(r/'tests/build_iz_profile.py').read_text()
s=s.replace('tests/iz_physics_replay.inc','tests/jb_mechanism_replay.inc')
s=s.replace('s=s.replace("s=s.replace', 's=s.replace("b=r/\'build/movement\'","b=r/\'build/jb-mechanism\'")\ns=s.replace("s=s.replace',1)
exec(compile(s,str(r/'tests/build_iz_profile.py'),'exec'),{'__file__':str(r/'tests/build_iz_profile.py'),'__name__':'__main__'})
