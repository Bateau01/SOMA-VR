from pathlib import Path
import shutil,subprocess,hashlib,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1];fixture=R/'build/cache_fixture_hl';(fixture/'_shadersource').mkdir(parents=True,exist_ok=True)
game=Path(r'D:\SteamLibrary\steamapps\common\SOMA')
for name in ['shadercache.xml','shadersource.hpss']:shutil.copy2(game/'_shadersource'/name,fixture/'_shadersource'/name)
index=fixture/'_shadersource/shadercache.xml';bank=fixture/'_shadersource/shadersource.hpss'
old=bank.read_bytes();tree=ET.parse(index)
old_entries={e.attrib['Name']:old[int(e.attrib['SourceStart']):int(e.attrib['SourceEnd'])] for e in tree.findall('./Cache/Shader')}
cmd=f". '{R/'runtime/SOMA-VR-ShaderCache.ps1'}'; Update-SomaVrOutlineCache '{fixture}'"
subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-Command',cmd],check=True)
new=bank.read_bytes();assert new[:len(old)]==old
changed=0
for e in ET.parse(index).findall('./Cache/Shader'):
 fragment=new[int(e.attrib['SourceStart']):int(e.attrib['SourceEnd'])];previous=old_entries[e.attrib['Name']]
 if e.attrib['Name'].startswith('game_edge_glow') and e.attrib['ShaderType']=='1':
  assert b'SOMA_VR_REMOTE_RIM_HM' in fragment
  assert fragment[fragment.index(b'const float kGlowEdgeSharpness'):]==previous[previous.index(b'const float kGlowEdgeSharpness'):]
  changed+=1
 elif e.attrib['Name'].startswith('deferred_base_vtxMaterialType_EdgeGlow') and e.attrib['ShaderType']=='0':
  assert b'SOMA_VR_REMOTE_RIM_HM' in fragment and b'vrWorldNormal*0.003' in fragment
 else:assert fragment==previous
assert changed
hashes=[hashlib.sha256(p.read_bytes()).digest() for p in [index,bank]]
subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-Command',cmd],check=True)
assert hashes==[hashlib.sha256(p.read_bytes()).digest() for p in [index,bank]]
print(f'PASS {changed} cached edge fragments updated, stock shader tails and all other fragments identical; repeat launch idempotent')
