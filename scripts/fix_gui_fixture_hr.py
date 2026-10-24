from pathlib import Path
p=Path('tests/test_native_gui.py');s=p.read_text();s=s.replace("b=s.index('static void s26cr_rebuild_native_menu(',a)","b=s.index('{',a);depth=1;b+=1\nwhile depth:\n depth+=(s[b]=='{')-(s[b]=='}');b+=1");p.write_text(s)
