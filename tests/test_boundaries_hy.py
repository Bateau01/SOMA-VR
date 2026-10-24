from pathlib import Path
import re,json
r=Path.cwd();b=r.parents[1]/'SOMA_VR_109_S26HX/repo';native=Path('D:/SteamLibrary/steamapps/common/SOMA')
def norm(s):
 s=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S);s=re.sub(r'#include "helpers/helper_vr_traversal_hy.hps"','',s);s=re.sub(r'\[nosave\]\s*cVRTraversalGuidesHY\s+mVRTraversalHY\s*;','',s);s=re.sub(r'mVRTraversalHY\.(?:Add|Dispose|Update)\([^;]*\);','',s);s=re.sub(r'void\s+(?:Update\(float\s+\w+\)|OnLeave\(\))\s*\{\s*\}','',s);return re.sub(r'\s+','',s)
report={}
for p in (r/'runtime/maps').rglob('*.hps'):
 if 'mVRTraversalHY' not in p.read_text(encoding='utf-8-sig'):continue
 rel=p.relative_to(r);q=b/rel
 if not q.exists():q=native/p.relative_to(r/'runtime')
 ok=norm(p.read_text(encoding='utf-8-sig'))==norm(q.read_text(encoding='utf-8-sig'));report[str(rel)]={'native_code_unchanged':ok,'baseline':str(q)};assert ok,rel
for rel in ['runtime/script/modules/PlayerToolHandler.hps','source/guide_hand_hr.inc','runtime/item_grips.dat']:
 if (r/rel).exists():
  ok=(r/rel).read_bytes()==(b/rel).read_bytes();assert ok,rel;report[rel]={'byte_identical':ok}
(r/'docs/v109-evidence/boundaries_final_hy.json').write_text(json.dumps(report,indent=2));print('PASS',len(report),'boundaries')
