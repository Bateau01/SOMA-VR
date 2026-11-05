"""Native handheld presentation/cancel fixture; omits authored screen contents."""
ASSETS={
 'phone':('entities/urban/tech/cellphone/cellphone_smartphone_terminal.ent','human'),
 'datapad':('entities/station/terminals/datapad/datapad.ent','diving'),
 'camera':('entities/station/terminals/camera_portable/camera_portable.ent','diving'),
}
def prepare(game,put,menu,kind):
 asset,family=ASSETS[kind]
 menu=menu.replace('if(phase==2 || phase==6)','if(false)').replace('if(phase==3 || phase==7)','if(false)')
 menu=menu.replace('HPL3VR_SetAA(phase>=5 && phase<=6?2:0);mbVRDynamicFoveation=phase==3;','HPL3VR_SetAA(0);mbVRDynamicFoveation=false;')
 inject='''
  if(phase==0){
   PlayerHands_SetHandModel("character/player/hands/hands_FAMILY.ent");
   cMatrixf pose=cMatrixf_Identity;pose.SetTranslation(cLux_GetPlayer().GetCamera().GetPosition()+cLux_GetPlayer().GetCamera().GetForward()*0.6f);
   cLux_GetCurrentMap().CreateEntity("NIHandheld","ASSET",pose,cVector3f(1));
   cLuxProp@ prop=Map_GetProp("NIHandheld");for(int i=0;i<prop.GetBodyNum();i++)prop.GetBody(i).SetMass(0);
  }
  if(phase==1)cScript_RunGlobalFunc("NIHandheld","","NI_Open");
  if(phase==3)cScript_RunGlobalFunc("State_Interact_HandheldTerminal","","NI_Cancel");
 '''.replace('FAMILY',family).replace('ASSET',asset)
 menu=menu.replace('  int iuNativePhase=0;', '  int iuNativePhase=0;'+inject)
 p=game/'script/props/Prop_HandheldTerminal.hps';s=p.read_text(encoding='utf-8-sig')
 s=s.replace('void Init()', '''void NI_Open(){
  LogNewLine("NI_HANDHELD_OPEN onground="+cLux_GetPlayer().GetCharacterBody().IsOnGround());
  OnInteract(0,mBaseObj.GetBody(0),mBaseObj.GetPosition(),"");
 }
 void Init()''',1);put(p,s)
 p=game/'script/player/PlayerState_Interact_HandheldTerminal.hps';s=p.read_text(encoding='utf-8-sig')
 s=s.replace('void SetupTerminal()', '''void NI_Cancel(){LogNewLine("NI_HANDHELD_CANCEL allowed="+mbAllowCancel+" entering="+mbEnteringState);OnAction(eAction_InteractCancel,true);}
 void SetupTerminal()''',1)
 s=s.replace('EnterInteractState(alPrevStateId);','EnterInteractState(alPrevStateId);LogNewLine("NI_HANDHELD_ENTER physical="+VR_PhysicalTablet());',1)
 s=s.replace('mfStateTimer = 0.0f;','LogNewLine("NI_HANDHELD_LEAVING");mfStateTimer = 0.0f;',1)
 s=s.replace('void Exit()\n\t{','void Exit()\n\t{\n LogNewLine("NI_HANDHELD_EXIT_CALLBACK");',1)
 s=s.replace('bool OnAction(int alAction, bool abPressed)\n\t{','bool OnAction(int alAction, bool abPressed)\n\t{\n if(abPressed)LogNewLine("NI_HANDHELD_ACTION id="+alAction+" cancel="+(alAction==eAction_InteractCancel));',1)
 s=s.replace('void OnLeaveState(int alNextStateId)\n\t{','void OnLeaveState(int alNextStateId)\n\t{\n LogNewLine("NI_HANDHELD_LEAVE physical="+VR_PhysicalTablet());',1)
 put(p,s)
 return menu
