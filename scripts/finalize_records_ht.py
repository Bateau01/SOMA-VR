from pathlib import Path
import json,re
r=Path(__file__).resolve().parents[1]
p=r/'docs/RELEASE_NOTES.md'
try:s=p.read_text(encoding='utf-8')
except UnicodeDecodeError:s=p.read_text(encoding='cp1252')
s=s.replace('all 17 usable campaign key-item identities','all 16 usable campaign key-item identities').replace('tracer fluid remains excluded','tracer fluid and the stun baton remain excluded').replace('Delta replacement chips and baton contact','Delta replacement chips')
p.write_text(s,encoding='utf-8')
p=r/'scripts/package_ht.py';s=p.read_text().replace('Animated guides, guide legibility','Guide legibility');p.write_text(s)
e=r/'docs/v109-evidence';summary=[]
for p in sorted(e.glob('*key_geometry_*.log')):
 s=p.read_text(errors='replace')
 assert all(v not in s for v in ['HT_ALIGNMENT_FAIL','HT_MISSING','HT_NO_GUIDE','HT_UNEXPECTED_USE','FATAL ERROR']),p
 assert 'HR_STORY_DONE' in s,p
 rows=[x for x in s.splitlines() if 'HT_GEOMETRY|' in x and '|StunRod|' not in x]
 assert rows,p
 summary.append({'log':p.name,'passed':True,'comparisons':rows,'native_permission':[x for x in s.splitlines() if 'HT_NATIVE_PERMISSION' in x]})
(e/'key_geometry_summary_ht.json').write_text(json.dumps(summary,indent=2))
p=r/'docs/key-item-guides-ht.md';s=p.read_text();s=s.replace('In-progress evidence:','Completed automated evidence:')
s=s.replace('- Remaining geometry, permission/lifecycle and installer checks are pending. No headset/visual pass is claimed.','- Native placement comparisons passed across all eight affected campaign maps, including Omicron animated mesh bones and Tau/Phi placements. The Epic executable passed Theta/Omicron checks; the local GOG executable has the same SHA-256.\n- Native guide permission/exclusion/lifecycle fixture passed: tracer fluid and baton excluded; denied/inactive/missing-stage guides suppressed; four permission queries and zero use callbacks; repeated clone lifecycle checks passed.\n- The fixture logs contain missing optional map-cache/voice warnings for the synthetic test map; these are not a complete story/audio test.\n- Installer delivery results are recorded separately after packaging. No headset visual pass or complete story playthrough is claimed.')
s+='\nEvidence index: v109-evidence/key_geometry_summary_ht.json, unchanged_boundaries_ht.json, guide_vm_probe.json, installer_delivery_ht.json. Geometry errors use a composite matrix tolerance of 0.002, not a claim of millimeter accuracy. The oldProxyError field is an approximate prior-placement comparison, not a recorded baseline headset reproduction.\n'
p.write_text(s)
print('Recorded',len(summary),'native map runs')

