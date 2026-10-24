from pathlib import Path
r=Path('.');s=(r/'tests/test_story_smoke_hr.py').read_text();s=s.replace('Native map initialization/compile smoke tests. No VR runtime or completed story sequence.','Native escape permission/callback test with supplied normal player state; not the preceding flood cinematic or headset appearance.')
s=s.replace("['00_03_laboratory','00_01_apartment','04_03_tau_escape']","['01_03_upsilon_outside']")
start=s.index("  idx=source.index('{',source.index('class '))");end=s.index('\n  cfg=',start)
s=s[:start]+'''  fixture=(R/'tests/fixtures/escape_hw.hps').read_text()
  idx=source.index('{',source.index('class cScrMap'));source=source[:idx+1]+fixture+source[idx+1:];put(G/rel,source)
'''+s[end:]
s=s.replace("ok='HR_STORY_DONE|'","ok='HW_FAIL' not in log and 'HR_STORY_DONE|'")
s=s.replace("'HR_STORY' in x or", "'HW_' in x or 'HR_STORY' in x or").replace('story_smoke_hr.json','escape_hw.json')
(r/'tests/test_escape_hw.py').write_text(s)
