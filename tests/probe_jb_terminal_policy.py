"""Native AngelScript policy regression; synthetic state, no tapping/pixel proof.

Uses the existing isolated runner with explicit expected terminal identities.
Does not reconstruct historical baseline hashes from current source.
"""
from pathlib import Path
import re
r=Path(__file__).resolve().parents[1]
expected={
 'chapter00/00_01_apartment/00_01_apartment.hps':['laptop_touchscreen_1','televison_small_1'],
 'chapter00/00_03_laboratory/00_03_laboratory.hps':['security_keypad_1'],
 'chapter02/02_01_ms_curie_outside/02_01_ms_curie_outside.hps':['monitor_theta_terminal_1'],
 'chapter02/02_06_theta_tunnels/02_06_theta_tunnels.hps':['SecurityOfficeTerminal'],
 'chapter03/03_01_omicron_outside/03_01_omicron_outside.hps':['StatusTerminal','BloodTerminal'],
 'chapter03/03_02_omicron_inside/03_02_omicron_inside.hps':['TerminalBiomech','SecurityTerminal_3','SecurityTerminal_15','SecurityTerminal_17','RobotRepairTerminal_WorkBench'],
}
policies=[]
for path,allow in expected.items():
 file='runtime/maps/'+path
 text=(r/file).read_text(encoding='utf-8-sig')
 method=re.search(r'    bool VR_CanUseWorldControlsFromTerminal\([^\n]+\)\s*\{[^}]+\}',text)
 assert method,file
 policies.append(dict(file=file,allow=allow,policy=method[0]))
s=(r/'tests/probe_terminal_io.py').read_text()
s=s.replace('W=R.parents[1];','W=R.parent;')
s=s.replace('Main/mirror_force_11000016B11BA91/AutoSave_02-05-theta-inside_2021_1_5_14_3_20_0.sav','Main/Default/AutoSave_02-05-theta-inside_2021_1_5_14_3_20_0.sav')
s=s.replace("policies=json.loads((R/'docs/v109-evidence/terminal_policies_io.json').read_text())",'policies='+repr(policies))
s=s.replace("current=(R/policy['file']).read_text();","current=(R/policy['file']).read_text(encoding='utf-8-sig');")
s=s.replace("out=R/'audit/IO-terminal-policy'","out=R/'audit/jb-terminal-policy'")
s=s.replace(".read_text()",".read_text(encoding='utf-8-sig')")
exec(compile(s,str(r/'tests/probe_terminal_io.py'),'exec'))
