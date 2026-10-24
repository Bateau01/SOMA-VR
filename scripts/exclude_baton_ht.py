from pathlib import Path
import json,re
r=Path(__file__).resolve().parents[1]
p=r/'runtime/script/modules/PlayerToolHandler.hps';s=p.read_text(encoding='utf-8-sig')
s=s.replace('2 Lambda inserted Omni-Tool cortex submesh, 3 baton contact demonstration.','2 Lambda inserted Omni-Tool cortex submesh.')
s=s.replace('tool.msPickedEntityName=="Tracer_Fluid" ||','tool.msPickedEntityName=="Tracer_Fluid" || tool.msPickedEntityName=="StunRod" ||')
s=s.replace('(mode!=3 && target.GetInteractionDisabled())','target.GetInteractionDisabled()')
start=s.index('        }else if(mode==3){');end=s.index('        if(mvVRItemGuides.length()',start)
s=s[:start]+'        }\n'+s[end:]
s=s.replace('if(name=="Tracer_Fluid")return;','if(name=="Tracer_Fluid" || name=="StunRod")return;')
s=re.sub(r'        if\(mapName=="02_03_delta" && \(name=="StunRod"\)\)\n            VR_ShowItemGuide[^\n]+\n','',s)
p.write_text(s,encoding='utf-8')
p=r/'docs/key-item-guide-routes-ht.json';d=json.loads(p.read_text());d['routes']=[v for v in d['routes'] if 'StunRod' not in v['items']];d['excluded']=['Tracer_Fluid','StunRod'];p.write_text(json.dumps(d,indent=2))
p=r/'tests/test_key_guide_boundaries_ht.py';s=p.read_text().replace("'GoyaChip','StunRod',","'GoyaChip',").replace('17 key identities / 27 routes; tracer excluded','16 key identities / 24 routes; tracer and baton excluded');s=s.replace("'Tracer_Fluid' not in names","'Tracer_Fluid' not in names and 'StunRod' not in names");p.write_text(s)
p=r/'tests/test_key_geometry_ht.py';s=p.read_text();start=s.index('        if(mode==3){');end=s.index('        if(mode!=3 && err>',start);s=s[:start]+s[end:];s=s.replace('if(mode!=3)err=','err=').replace('if(mode!=3 && err>','if(err>');p.write_text(s)
for f in ['docs/key-item-guides-ht.md','docs/RELEASE_NOTES.md']:
 p=r/f;s=p.read_text(encoding='utf-8');s=s.replace('17 usable campaign key identities, 27 target routes','16 usable campaign key identities, 24 target routes').replace('17 campaign key identities','16 campaign key identities')
 s='\n'.join(line for line in s.split('\n') if not line.startswith('| Delta | Stun baton'))
 s=s.replace(' The baton likewise uses verified tip contact rather than pretending it occupies a socket.','')
 s+='\nStun-baton and tracer-fluid holograms are explicitly excluded by user request. Their gameplay interactions are unchanged.\n'
 p.write_text(s,encoding='utf-8')

