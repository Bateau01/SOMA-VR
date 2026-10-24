from pathlib import Path
r=Path(__file__).resolve().parents[1]
s=(r/'tests/test_story_smoke_hr.py').read_text()
s=s.replace("['00_03_laboratory','00_01_apartment','04_03_tau_escape']","['00_03_laboratory','02_01_ms_curie_outside']")
s=s.replace("p=next((R/'runtime/maps').rglob(mapname+'.hps'));rel=p.relative_to(R/'runtime');source=p.read_text(encoding='utf-8-sig')", "matches=list((R/'runtime/maps').rglob(mapname+'.hps'));p=matches[0] if matches else next((G/'maps').rglob(mapname+'.hps'));rel=p.relative_to(R/'runtime') if matches else p.relative_to(G);source=p.read_text(encoding='utf-8-sig')")
probe='''
for(int k=0;k<3;k++){
 array<tString> names={"ScanChair","OmniToolSlot","CathTool_NoChip"};
 cLuxProp@ prop=Map_GetProp(names[k]);if(prop is null)continue;
 cMatrixf a=prop.GetMatrix();cMatrixf b=prop.GetMeshEntity().GetWorldMatrix();
 LogNewLine("HS_GEOMETRY|name="+names[k]+"|prop="+a.GetTranslation()+"|mesh="+b.GetTranslation()+"|up="+a.GetUp()+"|meshUp="+b.GetUp()+"|file="+prop.GetFileName());
 cVector3f point=cMath_MatrixMul(a,cVector3f(.40625,1.10,.08447));
 LogNewLine("HS_GEOMETRY|oldChairPoint="+point);
 for(int j=0;j<prop.GetMeshEntity().GetSubMeshEntityNum();j++){
 cMatrixf sm=prop.GetMeshEntity().GetSubMeshEntity(j).GetWorldMatrix();
 LogNewLine("HS_SUBMESH|name="+names[k]+"|index="+j+"|position="+sm.GetTranslation()+"|up="+sm.GetUp()+"|chairContact="+cMath_MatrixMul(sm,cVector3f(.25,.66695,.05198)));
 }
}
'''.replace('\n',' ')
s=s.replace('cEngine_Exit();}',probe+'cEngine_Exit();}')
s=s.replace("'story_smoke_hr.json'","'geometry_probe_hs.json'")
s=s.replace("'story_'+mapname", "'geometry_'+mapname")
(r/'tests/test_geometry_probe_hs.py').write_text(s)
