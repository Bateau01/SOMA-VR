from pathlib import Path
import math,xml.etree.ElementTree as E
r=Path(__file__).resolve().parents[1];g=Path(r'D:\SteamLibrary\steamapps\common\SOMA')
for name,chapter,pos,yaw,local in [
 ('03_02_omicron_inside','chapter03',[-23.7179,3,-53.6803],0,[.4,.94729,-.25]),
 ('05_01_phi_inside','chapter05',[-22.1276,12.5,48.1735],2.35619,[.4,1.08857,-.6])]:
 rel=Path('maps')/chapter/name/(name+'.hpm_Area');src=(g/rel).read_text(encoding='utf-8-sig');root=E.fromstring(src);areas=next(x for x in root.iter() if x.find('Area') is not None)
 for h in range(2):
  x,y,z=local;x=x if h else -x
  world=[pos[0]+math.cos(yaw)*x+math.sin(yaw)*z,pos[1]+y,pos[2]-math.sin(yaw)*x+math.cos(yaw)*z]
  a=E.Element('Area',{'ID':str(1900000100+h),'Name':'VRSeatArm_'+str(h),'WorldPos':' '.join(map(str,world)),'Rotation':f'0 {yaw} 0','Scale':'.22 .10 .42','Active':'false','Mesh':'','AreaType':'InteractAux','CreStamp':'0','ModStamp':'0','UID':f'90 1 {1900000100+h}'})
  u=E.SubElement(a,'UserVariables')
  for k,v in [('InteractParent','Area_ScanChair'),('UseParentMainBody','true'),('MaxFocusDistance','-1')]:E.SubElement(u,'Var',Name=k,Value=v)
  areas.append(a)
 # Preserve original file text, only insert the new nodes at the owning section end.
 tag=areas.tag;insert='\n'.join(E.tostring(x,encoding='unicode') for x in list(areas)[-2:])
 marker='</'+tag+'>';at=src.rfind(marker);assert at>=0;src=src[:at]+insert+'\n'+src[at:]
 dest=r/'runtime'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(src)
 p=r/'runtime'/rel.with_suffix('.hps');s=p.read_text()
 s='#include "helpers/helper_vr_seat_hu.hps"\n'+s
 i=s.index('{',s.index('class cScrMap'));s=s[:i+1]+'\n [nosave] cVRSeatGuideHU mVRSeatHU;\n'+s[i+1:]
 s=s.replace('void Update(float afTimeStep)\n\t{','void Update(float afTimeStep)\n\t{\n        mVRSeatHU.Update(afTimeStep);',1)
 s=s.replace('void OnLeave()\n\t{','void OnLeave()\n\t{\n        mVRSeatHU.Dispose();',1)
 # Same callback is used by the original trigger and its added contact regions.
 s=s.replace('void InteractScanChair(const tString &in asEntity)\n\t{','void InteractScanChair(const tString &in asEntity)\n\t{\n        if(!VRSeatHU_Ready())return;',1)
 s=s.replace('void InteractScanChair(const tString &in asEntity)\n\t\t{','void InteractScanChair(const tString &in asEntity)\n\t\t{\n            if(!VRSeatHU_Ready())return;',1)
 p.write_text(s)
# Exact added areas additionally check live parent state before forwarding.
p=r/'runtime/script/areas/Area_InteractAux.hps';s=p.read_text()
s=s.replace('if (pInteractEntity.GetInteractionDisabled())','if ((mBaseObj.GetName()=="VRSeatArm_0" || mBaseObj.GetName()=="VRSeatArm_1") &&\n            (!pInteractEntity.IsActive() || cLux_GetPlayer().GetCurrentStateId()!=ePlayerState_Normal))return false;\n\t\tif (pInteractEntity.GetInteractionDisabled())')
p.write_text(s)

