from pathlib import Path
r=Path(__file__).resolve().parents[1]
s=(r/'tests/test_geometry_probe_hs.py').read_text();s=s.replace("['00_03_laboratory','02_01_ms_curie_outside']","['00_03_laboratory']")
a=s.index(" for(int k=0;k<3;k++){");b=s.index(' cEngine_Exit();}',a)
probe='''
cGuiSet@ set=cGui_CreateSet("HSTouchProbe",null);set.SetVirtualSize(cVector2f(512),-1000,1000,cVector2f(0));
cImGui@ gui=cGui_CreateImGui("HSTouchProbe",set);
cImGuiButtonData data;data.mbUseBackgroundGfx=false;data.mbUseInFocusGfx=false;data.mbUseTriggeredGfx=false;
data.mFont.SetFile("sansation.fnt");data.mFont.mvSize=cVector2f(16);
for(int test=0;test<6;test++){
 gui.ClearStates();int accepted=0;bool pending=false;
 for(int frame=0;frame<5;frame++){
  gui.Begin(1.0f/60.0f);gui.SetShowMouse(true);
  bool down=frame==1 || frame==2;bool edge=frame==1 || (test>=3 && pending && down);
  cVector2f pos(110,110);if((test==1 || test==3 || test==5) && frame==1)pos=cVector2f(30,30);
  if((test==2 || test==4) && frame==2)pos=cVector2f(230,110);
  gui.SendMouseVirtualPosition(pos,cVector2f(1));gui.SendMouseVirtualPosition(pos,cVector2f(1));
  gui.SendAction(eImGuiAction_MouseLeft,down,edge);
  bool hit=gui.DoButton("ONE",tWString(""),data,cVector3f(100,100,1),cVector2f(80,40));
  bool other=gui.DoButton("TWO",tWString(""),data,cVector3f(220,100,1),cVector2f(80,40));
  if(hit)accepted++;LogNewLine("HS_WIDGET|test="+test+"|frame="+frame+"|accepted="+hit+"|other="+other);
  bool custom=false;if(test==5)custom=gui.ActionTriggered(eImGuiAction_MouseLeft);
  pending=gui.ActionTriggered(eImGuiAction_MouseLeft,true);
  LogNewLine("HS_WIDGET_CONSUMED|test="+test+"|frame="+frame+"|pending="+pending+"|custom="+custom);
  gui.End();
 }
 LogNewLine("HS_WIDGET_TOTAL|test="+test+"|accepted="+accepted);
}
cGui_DestroyImGui(gui);cGui_DestroySet(set);
'''.replace('\n',' ')
s=s[:a]+' '+probe+s[b:];s=s.replace("'geometry_probe_hs.json'","'widget_probe_hs.json'")
s=s.replace("'geometry_'+mapname", "'widget_'+mapname")
s=s.replace("ok='HR_STORY_DONE|'", "widget_ok=all(('HS_WIDGET_TOTAL|test='+str(i)+'|accepted='+str(n)) in log for i,n in enumerate([1,0,1,1,1,0])) and '|other=true' not in log\n  ok=widget_ok and 'HR_STORY_DONE|'")
(r/'tests/test_widget_probe_hs.py').write_text(s)
