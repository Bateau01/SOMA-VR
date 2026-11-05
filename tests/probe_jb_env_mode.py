"""Native trigger geometry under injected input-mode changes; not a save/reload test."""
from pathlib import Path
r=Path(__file__).resolve().parents[1]
s=(r/'tests/probe_jb_env_geometry.py').read_text()
s=s.replace(" s=(R/'runtime'/mp).read_text(encoding='utf-8-sig')", " s=(R/'runtime'/mp).read_text(encoding='utf-8-sig');s=s.replace('bool vr=_HPL3VR_RuntimeActive_ThetaTunnelsAT();','bool vr=mbJBMode;')")
checks=r'''
 iLuxEntity@ guide=Map_GetEntity("Area_RetrieveBrokenChip");
 bool activeBefore=guide.IsActive(),disabledBefore=guide.GetInteractionDisabled();
 cVector3f beforeSize=guide.GetMainBody().GetBoundingVolume().GetSize();
 for(int mode=0;mode<4;mode++){
  mbJBMode=mode<2;
  for(int repeat=0;repeat<12;repeat++)VR_UpdateEnvRetrievalJB(1.0f);
  cVector3f at=guide.GetMatrix().GetTranslation();
  bool correct=cMath_Abs(at.z-(mbJBMode?-98.1352f:-98.2252f))<.0001f;
  bool flags=guide.IsActive()==activeBefore&&guide.GetInteractionDisabled()==disabledBefore;
  bool size=cMath_Vector3Dist(beforeSize,guide.GetMainBody().GetBoundingVolume().GetSize())<.0001f;
  LogNewLine("JB_ENV_MODE|mode="+mode+"|depth="+correct+"|flags="+flags+"|size="+size);
 }
'''
s=s.replace(" i=s.index(\"{\",s.index(\"class cScrMap\"));", " fixture='\\n [nosave] bool mbJBMode=false;\\n'+fixture;fixture=fixture.replace('LogNewLine(\"IL_DONE|',"+repr(checks)+"+'LogNewLine(\"IL_DONE|',1)\n i=s.index(\"{\",s.index(\"class cScrMap\"));")
exec(compile(s,str(r/'tests/probe_jb_env_geometry.py'),'exec'))
for mode in range(4):
 assert f'JB_ENV_MODE|mode={mode}|depth=true|flags=true|size=true' in log
print('PASS: repeated VR placement and native-input restoration preserve trigger size and permission flags')
