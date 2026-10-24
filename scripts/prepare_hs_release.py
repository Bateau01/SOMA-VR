from pathlib import Path
import shutil
r=Path(__file__).resolve().parents[1]
for rel in ['source/s26n.c','installer/source/Build.ps1','installer/source/Installer.cs','installer/source/CurrentUpgradeTests.cs']:
 p=r/rel;b=p.read_bytes().replace(b'1.0.9-S26HR',b'1.0.9-S26HS').replace(b'2026102201',b'2026102202');p.write_bytes(b)
p=r/'scripts/package_hr.py';s=p.read_text().replace("version='1.0.9-S26HR';build=2026102201","version='1.0.9-S26HS';build=2026102202")
s=s.replace("'regression_batch_hr.json','adjacent_regressions_hr.json','power_sequence_hr.json'","'regression_batch_hr.json','control_lifetime_hs.json','terminal_touch_hs.json','widget_probe_hs.json','geometry_probe_hs.json','hint_anchor_hs.json'")
s=s.replace("'Roomscale physical alignment and guide placement require Steam Frame checks.'","'Full Munchi-to-Upsilon headset transition, real fingertip responsiveness and guide visual alignment remain hardware acceptance checks.'")
(r/'scripts/package_hs.py').write_text(s)
baseline=r.parents[1]/'SOMA_VR_109_S26HR/repo'
shutil.copytree(baseline/'installer/art',r/'installer/art',dirs_exist_ok=True)
print('Prepared S26HS release identity; no installed game changes')
