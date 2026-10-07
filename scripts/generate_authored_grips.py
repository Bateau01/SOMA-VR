"""Regenerate shared defaults from the checked-in, lossless pose JSON."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
entries=json.loads((R/'reference/authored_grips/poses.json').read_text())
assert len(entries)==52
fl=lambda x:float(x).hex()+'f'
lines=['/* Authored by Bateau1; 26 profiles, both hands. Generated from reference/authored_grips/captured.dat. */','static const S26EJGrip g_s26elDefaultGrips[]={']
for e in entries:
 lines.append('{"'+e['profile']+'",'+str(['left','right'].index(e['hand']))+','+str(e['kind'])+',{'+','.join(map(fl,e['controller_relative_rotation']))+'},{'+','.join(map(fl,e['normalized_body_contact']))+'},{'+','.join('{'+','.join(map(fl,j))+'}' for j in e['finger_joints'])+'}},')
lines+=['};','static const S26EJGrip* s26el_default_grip(i32 hand,i32 kind,const char* name){',' for(u32 i=0;i<sizeof(g_s26elDefaultGrips)/sizeof(g_s26elDefaultGrips[0]);++i){const S26EJGrip* e=&g_s26elDefaultGrips[i];if(e->hand==hand&&e->kind==kind&&h576c_ci_streq(e->name,name))return e;}return 0;','}']
(R/'source/authored_grips_el.inc').write_text('\n'.join(lines)+'\n')
