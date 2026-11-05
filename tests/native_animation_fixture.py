"""Native tool asset/animation playback; not authored map progression or device-input proof."""
import json
from pathlib import Path

def prepare(root,game,put,menu,batch,family):
 inv=json.loads((root/'reference/native_input_animation_inventory.json').read_text())
 items=[x for x in inv['items'] if not x['entity'].startswith(('entities/vr/','entities/soma_vr/'))]
 cases=items[batch*5:batch*5+5];assert cases and family in (*inv['models'],'story')
 menu=menu.replace('phase>7','phase>'+str(len(cases)*2-1)).replace('/5000','/4500')
 menu=menu.replace('if(phase==2 || phase==6)','if(false)').replace('if(phase==3 || phase==7)','if(false)')
 menu=menu.replace('HPL3VR_SetAA(phase>=5 && phase<=6?2:0);mbVRDynamicFoveation=phase==3;','HPL3VR_SetAA(0);mbVRDynamicFoveation=false;')
 menu=menu.replace('  int iuNativePhase=0;', '  int iuNativePhase=0;cScript_SetGlobalArgInt(0,phase);cScript_RunGlobalFunc("PlayerToolHandler","","NIAnimationPhase");')
 tool=(game/'script/modules/PlayerToolHandler.hps').read_text(encoding='utf-8-sig')
 families=[('human' if x['suffix']=='tracer_fluid' else 'deepsea' if x['suffix']=='ark' else 'diving') if family=='story' else family for x in cases]
 assets=','.join('"'+x['entity']+'"' for x in cases)
 code=r'''[nosave] int niAnimationCase=-1;
 void NIAnimationPhase(){
  int phase=cScript_GetGlobalArgInt(0);array<tString> files={ASSETS};int index=phase/2;
  if(index>=int(files.length()))return;
  if(phase%2!=0){LogNewLine("NI_ANIM_HOLSTER case="+index);UnequipCurrentTool(false);return;}
  array<tString> models={FAMILIES};PlayerHands_SetHandModel("character/player/hands/hands_"+models[index]+".ent");
  tString name="NIAnim"+index;cMatrixf pose=cMatrixf_Identity;pose.SetTranslation(cLux_GetPlayer().GetCamera().GetPosition()+cVector3f(0,-20,0));
  cLux_GetCurrentMap().CreateEntity(name,files[index],pose,cVector3f(1));
  cScript_SetGlobalArgBool(0,true);cScript_SetGlobalArgBool(1,true);
  bool ok=cScript_RunGlobalFunc(name,"","_Global_PickUp");
  if(mlCurrentToolIndex>=0)mfAutoHideTimer=-1;
  LogNewLine("NI_ANIM_PICK case="+index+" asset="+files[index]+" callback="+ok+" current="+mlCurrentToolIndex+" inventory="+mvInventory.length());
 }
'''.replace('ASSETS',assets).replace('FAMILIES',','.join('"'+f+'"' for f in families))
 tool=tool.replace('    bool NI_PrepareInventory(float dt)',code+'    bool NI_PrepareInventory(float dt)',1);put(game/'script/modules/PlayerToolHandler.hps',tool)
 hands=(game/'script/modules/PlayerHandsHandler.hps').read_text(encoding='utf-8-sig')
 hands=hands.replace('void PostUpdate(float afTimeStep)','[nosave] float niAnimObserveTime=0; void PostUpdate(float afTimeStep)',1)
 needle='if(pEntity !is null) pEntity.SetMatrix(mtxHands);'
 report=needle+r'''
   niAnimObserveTime-=afTimeStep;if(niAnimObserveTime<=0){niAnimObserveTime=0.5f;
    cAnimationState@ anim=GetCurrentAnimationState();iLuxEntity@ item=cLux_ID_Entity(m_idCurrentAttachProp);
    LogNewLine("NI_ANIM_POSE name="+(anim is null ? "MISSING" : anim.GetName())+" scale="+fScale+" custom="+mbUseCustomPosition+" attached="+(item is null ? "NONE" : item.GetName()));
   }
'''
 assert needle in hands;hands=hands.replace(needle,report,1);put(game/'script/modules/PlayerHandsHandler.hps',hands)
 return menu,cases
