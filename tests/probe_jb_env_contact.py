"""Native real-shape contact envelope. Fixture relocation is setup, not insertion proof."""
from pathlib import Path
r=Path(__file__).resolve().parents[1]
s=(r/'tests/probe_jb_env_geometry.py').read_text()
method=r'''
 void _Global_JBContactProbe(){
  cLuxMap@ map=cLux_GetCurrentMap();
  iLuxEntity@ chip=map.GetEntityByName("chip_unformatted",eLuxEntityType_LastEnum,""),area=map.GetEntityByName("Area_Broken_Panel",eLuxEntityType_LastEnum,"");
  if(chip is null || area is null){LogNewLine("JB_CONTACT_MISSING");return;}
  cMatrixf saved=chip.GetMatrix();bool active=chip.IsActive();chip.SetActive(true);
  tString savedSlot=chip.GetVarString("VRReturnSlot"),savedArea=chip.GetVarString("VRReturnArea");
  cVector3f center=area.GetMainBody().GetWorldPosition();
  array<cVector3f> offsets={cVector3f(0,0,.02f),cVector3f(0,0,.12f),cVector3f(0,0,.20f),cVector3f(.20f,0,.07f),cVector3f(0,.20f,.07f),cVector3f(0,0,-.12f)};
  for(uint k=0;k<offsets.length();k++){
   cMatrixf m=area.GetMatrix();m.SetTranslation(center+offsets[k]);chip.SetMatrix(m);
   cVector3f before=chip.GetMainBody().GetWorldPosition();
   bool nativeHit=Entity_GetCollide("chip_unformatted","Area_Broken_Panel");
   bool contact=VR_PhysicalTargetContact("chip_unformatted","Area_Broken_Panel");
   chip.SetVarString("VRReturnSlot","");chip.SetVarString("VRReturnArea","Area_Broken_Panel");
   bool cleared=VR_ReturnedCarrierHasClearedSocket("chip_unformatted");
   bool retained=chip.GetVarString("VRReturnArea")=="Area_Broken_Panel";
   LogNewLine("JB_CONTACT|case="+k+"|native="+nativeHit+"|contact="+contact+"|unchanged="+(cMath_Vector3Dist(before,chip.GetMainBody().GetWorldPosition())<.00001f)+"|cleared="+cleared+"|retained="+retained);
  }
  chip.SetVarString("VRReturnSlot",savedSlot);chip.SetVarString("VRReturnArea",savedArea);
  chip.SetMatrix(saved);chip.SetActive(active);
 }
'''
needle=" mp=Path('maps/chapter02/02_06_theta_tunnels/02_06_theta_tunnels.hps')"
inject=" hp=G/'script/modules/PlayerToolHandler.hps';hs=hp.read_text(encoding='utf-8-sig');hs=hs.replace('    bool VR_PhysicalTargetContact(',"+repr(method)+"+'    bool VR_PhysicalTargetContact(',1);put(hp,hs)\n"
s=s.replace(needle,inject+needle)
s=s.replace('LogNewLine("IL_DONE|NONCE");','cScript_RunGlobalFunc("PlayerToolHandler","","_Global_JBContactProbe");LogNewLine("IL_DONE|NONCE");')
exec(compile(s,str(r/'tests/probe_jb_env_geometry.py'),'exec'))
lines=[x for x in log.splitlines() if 'JB_CONTACT' in x];print('\n'.join(lines))
assert len(lines)==6 and all('unchanged=true' in x for x in lines),lines
assert 'native=false|contact=true' in lines[1],lines
assert all('contact=false' in lines[k] for k in (2,3,4,5)),lines
assert all('cleared=false|retained=true' in lines[k] for k in (0,1)),lines
assert all('cleared=true|retained=false' in lines[k] for k in (2,3,4,5)),lines
