"""Native HPL VM/camera test; synthetic conversation and VR-session flag.
No headset, story dialogue, position-based walk-up or roomscale validation.
Only the existing isolated game is edited temporarily and restored in finally.
"""
from pathlib import Path
import argparse, subprocess, json, hashlib, time, ctypes
p=argparse.ArgumentParser();p.add_argument('--game',type=Path,required=True)
p.add_argument('--repeated',action='store_true');p.add_argument('--walking',action='store_true');p.add_argument('--candidate',action='store_true');p.add_argument('--baseline',type=Path);p.add_argument('--readables',action='store_true');p.add_argument('--controls',action='store_true');p.add_argument('--guides',action='store_true');p.add_argument('--roomscale',action='store_true');a=p.parse_args()
R=Path(__file__).resolve().parents[1];G=a.game.resolve()
assert 'validation' in G.parts and (G/'config/pump_lab_init.cfg').is_file()
active=subprocess.run(['powershell','-NoProfile','-Command','@(Get-Process Soma,Soma_NoSteam -ErrorAction SilentlyContinue).Count'],capture_output=True,text=True)
assert active.stdout.strip()=='0','Close existing game first'
saved={};proc=None
def put(path,data):
    if path not in saved:saved[path]=path.read_bytes() if path.exists() else None
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data if isinstance(data,bytes) else data.encode('utf-8'))
try:
    src=(a.baseline or R/'runtime/script/player/PlayerState_Conversation.hps').read_text(encoding='utf-8-sig')
    identity=hashlib.sha256(src.encode()).hexdigest()
    # Substitute runtime availability only; exercise real script methods/camera.
    if 'bool HPL3VR_ConversationActive()' in src:
        start=src.index('bool HPL3VR_ConversationActive()');end=src.index('const float gfConvHeadRotateAcc',start)
        src=src[:start]+'bool gHRTestVR=false; bool HPL3VR_ConversationActive(){return gHRTestVR;}\n'+src[end:]
    else:src='bool gHRTestVR=false;\n'+src
    old='Dialog_CharacterIsActive(msVoiceCharacter)==false &&'
    assert old in src
    src=src.replace(old,'false && '+old,1) # No sound scene: keep the test conversation active.
    test=r'''
    void _Global_HRConversationTest(){
        int errors=0;
        for(int mode=0;mode<2;mode++)for(int rate=0;rate<2;rate++){
            gHRTestVR=mode==1;
            Init();msFocusEntity="PowerStation";mlHeadBoneIndex=-1;
            mvFocusOffset=cVector3f_Zero;mfMaxMoveDist=2;
            mePositionState=ePositionState_Ready;
            cCamera@ cam=cLux_GetPlayer().GetCamera();
            cam.SetYawLimits(0,0);cam.SetPitchLimits(0,0);
            OnEnterState(ePlayerState_Normal);
            mvFocusPos=CalcCameraTarget();mfDirectLookCount=0.001f;
            Update(rate==0 ? 1.0f/60.0f : 1.0f/120.0f);
            float span=cam.GetYawMaxLimit()-cam.GetYawMinLimit();
            if(gHRTestVR){if(cMath_Abs(span)>0.0001f)errors++;}
            else if(cMath_Abs(span-cMath_ToRad(40))>0.0001f)errors++;
            // Conversation still owns its authored action restrictions.
            if(OnAction(eAction_Jump,true)||OnAction(eAction_Crouch,true))errors++;
            OnLeaveState(ePlayerState_Normal);
            if(cam.GetYawMinLimit()!=0 || cam.GetYawMaxLimit()!=0)errors++;
        }
        LogNewLine("HR_CONVERSATION|failures="+errors);
    }
'''
    src=src.replace('void SetupConversation()',test+'\n void SetupConversation()',1)
    put(G/'script/player/PlayerState_Conversation.hps',src)
    if a.readables:
        readable=(R/'runtime/script/props/Prop_Readable.hps').read_text(encoding='utf-8-sig')
        readable=readable.replace('mbVRIndependentRead=cScript_RunGlobalFunc("VRREAD","","S");','mbVRIndependentRead=true; // fixture: emulate remote callback scope')
        readable=readable.replace('cScript_RunGlobalFunc("VRREAD","","REMOTE")','mbHRRemote /* fixture: authorized remote callback scope */')
        readable=readable.replace('cScript_RunGlobalFunc("VRREAD","","B");','// fixture: no injected bridge publication')
        readable=readable.replace('if(pVRReadBody !is apBody) cScript_RunGlobalFunc("VRREAD","","C");','// fixture: no injected bridge publication')
        readable=readable.replace('cScript_RunGlobalFunc("VRREAD",mbVRIndependentRead ? "I" : "","P");','// fixture: no injected bridge publication')
        probe=r'''
        bool mbHRRemote=true;
        void _Global_HRReadableProbe(){
            iPhysicsBody@ b=mBaseObj.GetMainBody();
            bool ok=VR_BeginPhysicalRead(b,b.GetWorldPosition());
            LogNewLine("HR_READABLE|name="+mBaseObj.GetName()+"|ok="+ok+"|file="+GetBase().GetFileName()+"|openFile="+msOpenEntityFile+"|hasOpen="+(mpOpenEntity !is null)+"|mass="+b.GetMass());
            if(mpOpenEntity !is null)for(int i=0;i<mpOpenEntity.GetBodyNum();i++){
                iPhysicsBody@ v=mpOpenEntity.GetBody(i);
                LogNewLine("HR_READABLE_DISPLAY|body="+v.GetName()+"|collide="+v.GetCollide()+"|mass="+v.GetMass());
            }
            _Global_VRClosePhysicalRead();
            // Same object, continued history: direct read creates its usual
            // display, remote re-use must retire that display, then direct
            // reading must still restore it. The independent-hand scope is
            // held constant to isolate the remote presentation condition.
            mbHRRemote=false;
            bool direct=VR_BeginPhysicalRead(b,b.GetWorldPosition());
            bool directDisplay=mpOpenEntity !is null && mpOpenEntity.IsActive();
            _Global_VRClosePhysicalRead();
            mbHRRemote=true;
            bool remoteAgain=VR_BeginPhysicalRead(b,b.GetWorldPosition());
            bool remoteDisplay=mpOpenEntity !is null && mpOpenEntity.IsActive();
            _Global_VRClosePhysicalRead();
            mbHRRemote=false;
            bool directAgain=VR_BeginPhysicalRead(b,b.GetWorldPosition());
            bool restoredDisplay=mpOpenEntity !is null && mpOpenEntity.IsActive();
            _Global_VRClosePhysicalRead();
            LogNewLine("HR_READABLE_HISTORY|name="+mBaseObj.GetName()+"|direct="+direct+"|directDisplay="+directDisplay+"|remote="+remoteAgain+"|remoteDisplay="+remoteDisplay+"|directAgain="+directAgain+"|restoredDisplay="+restoredDisplay);
        }
'''
        readable=readable.replace('bool VR_BeginPhysicalRead(',probe+'\n bool VR_BeginPhysicalRead(',1)
        put(G/'script/props/Prop_Readable.hps',readable)
    if a.controls:
        moving=(R/'runtime/script/props/Prop_MovingButton.hps').read_text(encoding='utf-8-sig')
        probe=r'''
        void _Global_HRControlProbe(){
            iPhysicsBody@ main=mBaseObj.GetMainBody();
            LogNewLine("HR_CONTROL|main="+main.GetName()+"|simple="+mbSimplePressInteraction);
            for(int i=0;i<mBaseObj.GetBodyNum();i++){
                iPhysicsBody@ b=mBaseObj.GetBody(i);
                LogNewLine("HR_CONTROL_BODY|name="+b.GetName()+"|can="+CanInteract(0,b)+"|collide="+b.GetCollide());
            }
            bool before=mbSwitchedOn;
            bool accepted=OnInteract(0,main,main.GetWorldPosition(),"");
            LogNewLine("HR_CONTROL_RESULT|accepted="+accepted+"|changed="+(before!=mbSwitchedOn)+"|cooldownReject="+(!CanInteract(0,main)));
        }
'''
        moving=moving.replace('bool CanInteract(',probe+'\n bool CanInteract(',1)
        put(G/'script/props/Prop_MovingButton.hps',moving)
    menu=(R/'runtime/script/modules/MenuHandler.hps').read_text(encoding='utf-8-sig')
    menu=menu.replace('void GuiMainMenuSelection()','bool mbHRTestStarted=false;\n void GuiMainMenuSelection()',1)
    needle='void GuiMainMenuSelection()\n\t{';assert needle in menu
    menu=menu.replace(needle,needle+'\n if(!mbHRTestStarted){mbHRTestStarted=true;ClickNewGame();}',1)
    menu=menu.replace('mpConfig.GetBool("Main", "ShowPreMenu", true)','false')
    put(G/'script/modules/MenuHandler.hps',menu)
    put(G/'script/modules/HintHandler.hps',(R/'runtime/script/modules/HintHandler.hps').read_text(encoding='utf-8-sig'))
    m=G/'maps/vr_pump_lab/vr_pump_lab.hps';text=m.read_text(encoding='utf-8-sig')
    assert '// Same charge' in text
    readprobe='LogNewLine("IJ_SAVE|ok="+cScript_RunGlobalFunc("VRCOMFORT","STUTTER","SAVE"));'
    if a.roomscale:
        normal=(R/'runtime/script/player/MoveState_Normal.hps').read_text(encoding='utf-8-sig')
        normal=normal.replace('if(!cScript_GetGlobalReturnBool()) return false;', 'if(false) return false; // fixture: emulate active VR only')
        normal=normal.replace('void _Global_VRRoomscaleStepReset()', r"""
        void _Global_IFCrouchProbe(){
            iCharacterBody@ b=mBaseObj.mpPlayer.GetCharacterBody();
            cVector3f feet=b.GetFeetPosition();cVector3f cam=mBaseObj.mpPlayer.GetCamera().GetPosition();
            bool oldDisabled=mbCrouchingDisabled;mbCrouchingDisabled=true;
            HPL3VR_PhysicalCrouchDown();bool denied=!mbVRPhysicalCrouch;
            mbCrouchingDisabled=oldDisabled;
            HPL3VR_PhysicalCrouchDown();bool down=mbVRPhysicalCrouch && mbCrouching;
            cVector3f low=mBaseObj.mpPlayer.GetCamera().GetPosition();
            HPL3VR_PhysicalCrouchUp();bool up=!mbVRPhysicalCrouch && !mbCrouching;
            cVector3f after=mBaseObj.mpPlayer.GetCamera().GetPosition();
            LogNewLine("IF_CROUCH|denied="+denied+"|down="+down+"|up="+up+"|cameraDown="+(low.y-cam.y)+"|cameraReturn="+(after.y-cam.y)+"|feetDrift="+cMath_Vector3Dist(feet,b.GetFeetPosition()));
        }
        void _Global_VRRoomscaleStepReset()""")
        normal=normal.replace('void FootSound(eFootSound aType, float afSpeed)', 'int mlIESteps=0;\n void FootSound(eFootSound aType, float afSpeed)')
        normal=normal.replace('if(mbFootstepSoundsDisabled) return;', 'if(mbFootstepSoundsDisabled) return; if(aType==eFootSound_Step)mlIESteps++;')
        normal=normal.replace('extraData.mpSoundEntry.SetParam("movement", moveType);','extraData.mpSoundEntry.SetParam("movement", moveType);\n            LogNewLine("IE_STEP_SOUND|played=true");')
        normal=normal.replace('void _Global_VRRoomscaleStepReset()', r"""
        void _Global_IEFootstepProbe(){
            mvVRRoomStepTravel=cVector3f(0);int before=mlIESteps;
            for(int i=0;i<100;i++){
                cScript_SetGlobalArgVector3f(0,cVector3f(.0001f,0,0));_Global_VRRoomscaleStep();
                cScript_SetGlobalArgVector3f(0,cVector3f(-.0001f,0,0));_Global_VRRoomscaleStep();
            }
            LogNewLine("IE_STEP_NOISE|silent="+(mlIESteps==before));
            for(int i=0;i<14;i++){
                cScript_SetGlobalArgVector3f(0,cVector3f(.05f,0,0));_Global_VRRoomscaleStep();
            }
            LogNewLine("IE_STEP_TRAVEL|count="+(mlIESteps-before));
            _Global_VRRoomscaleStepReset();
        }
        void _Global_VRRoomscaleStepReset()""")
        put(G/'script/player/MoveState_Normal.hps',normal)
        put(G/'script/helpers/helper_vr_roomscale_hr.hps' ,(R/'runtime/script/helpers/helper_vr_roomscale_hr.hps').read_bytes())
        player=(R/'runtime/script/player/Player.hps').read_text(encoding='utf-8-sig')
        probe=r"""
        int mlIETick=0;
        void IETrace(const tString &in phase){
            if(mlIETick<100 || mlIETick>106)return;
            cVector3f b=mBaseObj.GetCharacterBody().GetPosition();
            cVector3f c=mBaseObj.GetCamera().GetPosition();
            LogNewLine("IE_TIMING|tick="+mlIETick+"|phase="+phase+"|body="+b.x+","+b.y+","+b.z+"|camera="+c.x+","+c.y+","+c.z+"|speed="+mBaseObj.GetCharacterBody().GetVelocity(1.0f/60.0f).Length()+"|moved="+mBaseObj.GetCharacterBody().GetMovedLastUpdate());
        }
        """
        player=player.replace('void Update(float afTimeStep)',probe+'\n void Update(float afTimeStep)',1)
        player=player.replace('HPL3VR_UpdateRoomscale();','mlIETick++; if(mlIETick>=80 && mlIETick<110)mBaseObj.GetCharacterBody().SetForceVelocity(cVector3f(.6f,0,0)); IETrace("pre"); if(mlIETick==102){cVector3f d=HPL3VR_RoomscaleMove(mBaseObj.GetCharacterBody(),cVector3f(.05f,0,0));LogNewLine("IE_ACCEPT|x="+d.x);} IETrace("after_move");',1)
        player=player.replace('void PostUpdate(float afTimeStep)\n\t{','void PostUpdate(float afTimeStep)\n\t{\n IETrace("post");',1)
        player=player.replace('void VariableUpdate(float afTimeStep)\n\t{','void VariableUpdate(float afTimeStep)\n\t{\n IETrace("variable");',1)
        if a.candidate:
            player=player.replace('cVector3f d=HPL3VR_RoomscaleMove(mBaseObj.GetCharacterBody(),cVector3f(.05f,0,0));LogNewLine("IE_ACCEPT|x="+d.x);','bool ok=cScript_RunGlobalFunc("VRROOM","","TESTAPPLY");LogNewLine("IE_ACCEPT|native="+ok);')
        if a.repeated: player=player.replace('if(mlIETick==102)', 'if(mlIETick>=100 && mlIETick<=106)')
        if a.walking:
            player=player.replace('SetForceVelocity(cVector3f(.6f,0,0))','Move(eCharDir_Right,1.0f)')
        put(G/'script/player/Player.hps',player)
        text='#include "helpers/helper_vr_roomscale_hr.hps"\n'+text
        readprobe=r'''
        cScript_RunGlobalFunc("MoveState_Normal","","_Global_IEFootstepProbe");
        cScript_RunGlobalFunc("MoveState_Normal","","_Global_IFCrouchProbe");
        iCharacterBody@ character=cLux_GetPlayer().GetCharacterBody();
        cVector3f before=character.GetPosition();
        cVector3f forceBefore=character.GetForceVelocity();
        cVector3f push;
        bool free=character.CheckCharacterFits(before+cVector3f(0,100,0),false,-1,push);
        bool currentFit=character.CheckCharacterFits(before,false,-1,push);
        bool adjacentFit=character.CheckCharacterFits(before+cVector3f(.01f,0,0),false,-1,push);
        LogNewLine("HR_ROOM_GROUND|current="+currentFit+"|adjacent="+adjacentFit+"|push="+push.x+","+push.y+","+push.z);
        cLuxProp@ fixture=cast<cLuxProp>(cLux_GetCurrentMap().GetEntityByName("PowerStation",eLuxEntityType_Prop,""));
        bool blocked=false;
        if(fixture !is null && fixture.GetMainBody() !is null)
            blocked=!character.CheckCharacterFits(fixture.GetMainBody().GetWorldPosition(),false,-1,push);
        bool unchanged=cMath_Vector3Dist(before,character.GetPosition())<.000001f &&
            cMath_Vector3Dist(forceBefore,character.GetForceVelocity())<.000001f;
        LogNewLine("HR_ROOM_QUERY|free="+free+"|blocked="+blocked+"|unchanged="+unchanged);
        cVector3f accepted=HPL3VR_RoomscaleMove(character,cVector3f(.05f,0,0));
        bool moved=cMath_Abs(accepted.x-.05f)<.0001f && cMath_Abs(accepted.y)<.0001f;
        bool momentum=cMath_Vector3Dist(forceBefore,character.GetForceVelocity())<.000001f;
        cVector3f rejected=HPL3VR_RoomscaleMove(character,cVector3f(1,0,0));
        bool bounded=rejected.Length()<.000001f;
        bool obstacle=false;
        if(fixture !is null){
            cVector3f center=fixture.GetMainBody().GetWorldPosition();
            for(int side=0;side<4 && !obstacle;side++){
                cVector3f axis=side==0?cVector3f(1,0,0):(side==1?cVector3f(-1,0,0):(side==2?cVector3f(0,0,1):cVector3f(0,0,-1)));
                cVector3f testStart=center+axis*3.0f;testStart.y=before.y;
                if(!character.CheckCharacterFits(testStart,false,-1,push))continue;
                character.SetPosition(testStart,false);
                float travelled=0;bool safe=true;
                for(int j=0;j<65;j++){
                    cVector3f motion=HPL3VR_RoomscaleMove(character,axis*-.05f);
                    travelled+=motion.Length();
                    if(!character.CheckCharacterFits(character.GetPosition(),false,-1,push))safe=false;
                    if(motion.Length()<.001f){obstacle=safe && travelled<3.0f;break;}
                }
            }
        }
        character.SetPosition(before,false);
        bool micro=true;
        for(int i=0;i<20;i++){
            cVector3f f=HPL3VR_RoomscaleMove(character,cVector3f(.001f,0,0));
            cVector3f b=HPL3VR_RoomscaleMove(character,cVector3f(-.001f,0,0));
            if(cMath_Abs(f.x-.001f)>.00001f || cMath_Abs(b.x+.001f)>.00001f)micro=false;
        }
        micro=micro && cMath_Vector3Dist(before,character.GetPosition())<.00005f;
        LogNewLine("ID_ROOM_MICRO|roundTrip="+micro);
        character.SetPosition(before,false);
        LogNewLine("HR_ROOM_MOVE|moved="+moved+"|momentum="+momentum+"|bounded="+bounded);
        LogNewLine("HR_ROOM_OBSTACLE|stopped="+obstacle);
'''
    if a.readables:
        readprobe+='''
        cMatrixf readableFixture=cMatrixf_Identity;
        readableFixture.SetTranslation(cLux_GetPlayer().GetCharacterBody().GetPosition()+cVector3f(0,3,0));
        cLux_GetCurrentMap().CreateEntity("HRNotepad","entities/urban/ornament/notepad/notepad.ent",readableFixture,cVector3f(1));
        cScript_RunGlobalFunc("HRNotepad","","_Global_HRReadableProbe");
        readableFixture.SetTranslation(readableFixture.GetTranslation()+cVector3f(1,0,0));
        cLux_GetCurrentMap().CreateEntity("HRBook","entities/urban/ornament/book_brain/book_brain01.ent",readableFixture,cVector3f(1));
        cScript_RunGlobalFunc("HRBook","","_Global_HRReadableProbe");
'''
    if a.guides:
        for script in ('modules/PlayerToolHandler.hps','custom_depth/prop_omnitool_slot.hps'):
            source=(R/'runtime/script'/script).read_text(encoding='utf-8-sig')
            if script.startswith('modules/'):
                # Substitute runtime/held availability, not permission or use callbacks.
                start=source.index('bool _HPL3VR_RuntimeActive_ToolHandler()')
                end=source.index('enum eToolState',start)
                source=source[:start]+'bool gHRGuideRuntime=false; bool gHRGuideHeld=false; bool _HPL3VR_RuntimeActive_ToolHandler(){return gHRGuideRuntime;}\n'+source[end:]
                source=source.replace('cScript_RunGlobalFunc("VRGUIDE","","ACTIVE")','gHRGuideRuntime')
                source=source.replace('cScript_RunGlobalFunc("VROMNIHELD",tool.msPickedEntityName,"Q")','gHRGuideHeld')
                probe=r'''
                void _Global_HRGuidePermissionProbe(){
                    cToolData tool;tool.msPickedEntityName="HRTool";tool.msHandAnimationSuffix="omnitool";
                    tool.msCanBeUsedCallback="HRGuideCan";tool.msUseCallback="HRGuideUse";
                    mvInventory.insertLast(tool);
                    bool ok=true;
                    for(int mode=0;mode<5;mode++){
                        gHRGuideRuntime=mode!=0;gHRGuideHeld=mode!=1;
                        cScript_SetGlobalArgString(0,mode==3 ? "MissingSlot" : "HRGuideSlot");
                        if(mode==4)mvInventory[mvInventory.length()-1].msCanBeUsedCallback="HRGuideDeny";
                        _Global_VRCanGuideOmniSlot();
                        LogNewLine("HR_GUIDE_MODE|mode="+mode+"|allowed="+cScript_GetGlobalReturnBool());
                        ok=ok && (cScript_GetGlobalReturnBool()==(mode==2));
                    }
                    mvInventory[mvInventory.length()-1].msCanBeUsedCallback="HRGuideCan";
                    cToolData@ current=mvInventory[mvInventory.length()-1];
                    mlVRItemGuideUsed=0;
                    VR_ShowItemGuide(current,"HRGuideSlot","HRTool","entities/station/gameplay/chip_environment_storage/chip_environment_storage.dae");
                    bool meshOK=mlVRItemGuideUsed==1 && mvVRItemGuides.length()==1 && mvVRItemGuides[0].Live();
                    VR_ShowItemGuide(current,"HRGuideSlot","HRTool","entities/station/gameplay/chip_environment_storage/chip_environment_storage.dae","","MissingStage");
                    meshOK=meshOK && mlVRItemGuideUsed==1;
                    current.msVRPhysicalCarrierName="HRTool";
                    current.msPickedEntityName="Tracer_Fluid";
                    VR_ShowItemGuide(current,"HRGuideSlot","HRTool","entities/station/gameplay/chip_environment_storage/chip_environment_storage.dae");
                    meshOK=meshOK && mlVRItemGuideUsed==1;
                    current.msPickedEntityName="HRTool";current.msCanBeUsedCallback="HRGuideDeny";
                    current.msPickedEntityName="StunRod";
                    VR_ShowItemGuide(current,"HRGuideSlot","HRTool","entities/station/gameplay/chip_environment_storage/chip_environment_storage.dae");
                    meshOK=meshOK && mlVRItemGuideUsed==1;
                    current.msPickedEntityName="HRTool";
                    VR_ShowItemGuide(current,"HRGuideSlot","HRTool","entities/station/gameplay/chip_environment_storage/chip_environment_storage.dae");
                    meshOK=meshOK && mlVRItemGuideUsed==1;
                    current.msCanBeUsedCallback="HRGuideCan";

                    VR_HideItemGuides();
                    for(uint k=0;k<mvVRItemGuides.length();k++)mvVRItemGuides[k].Dispose(cLux_GetCurrentMap().GetWorld());
                    mvVRItemGuides.resize(0);
                    LogNewLine("HR_GUIDE|itemMesh="+meshOK);
                    mvInventory.removeAt(mvInventory.length()-1);
                    gHRGuideRuntime=false;gHRGuideHeld=false;
                    LogNewLine("HR_GUIDE|permission="+ok);
                }
'''
                source=source.replace('void _Global_VRCanGuideOmniSlot()',probe+'\n void _Global_VRCanGuideOmniSlot()',1)
            put(G/'script'/script,source)
        put(G/'script/helpers/helper_vr_guidance_hr.hps',(R/'runtime/script/helpers/helper_vr_guidance_hr.hps').read_bytes())
        for asset in ('guide.mat','guide.dds'):
            put(G/'entities/soma_vr/guidance'/asset,(R/'runtime/entities/soma_vr/guidance'/asset).read_bytes())
        text='#include "helpers/helper_vr_guidance_hr.hps"\n'+text
        # Map-level callbacks: count native permission dispatch and detect any use.
        brace=text.index('{',text.index('class '))
        text=text[:brace+1]+'''
        int mlHRGuideCan=0;int mlHRGuideUse=0;
        bool HRGuideCan(const tString &in tool,const tString &in target){mlHRGuideCan++;LogNewLine("HR_GUIDE_ARGS|tool="+tool+"|target="+target);return tool=="HRTool" && target=="HRGuideSlot";}
        bool HRGuideDeny(const tString &in tool,const tString &in target){mlHRGuideCan++;return false;}
        bool HRGuideUse(const tString &in tool,const tString &in target){mlHRGuideUse++;return true;}
'''+text[brace+1:]
        readprobe+='''
        cLux_GetCurrentMap().CreateEntity("HRGuideSlot","entities/station/panels/omnislot_inside/omnislot_inside.ent",cMatrixf_Identity,cVector3f(1));
        cScript_SetGlobalArgString(0,"HRGuideSlot");
        cScript_SetGlobalReturnBool(true);
        cScript_RunGlobalFunc("PlayerToolHandler","","_Global_VRCanGuideOmniSlot");
        LogNewLine("HR_GUIDE|inactiveDenied="+(!cScript_GetGlobalReturnBool()));
        cLux_GetCurrentMap().CreateEntity("HRTool","entities/station/gameplay/chip_environment_storage/chip_environment_storage.ent",cMatrixf_Identity,cVector3f(1));
        cScript_RunGlobalFunc("PlayerToolHandler","","_Global_HRGuidePermissionProbe");
        LogNewLine("HR_GUIDE|canCalls="+mlHRGuideCan+"|useCalls="+mlHRGuideUse);
        cVRGuideMesh guide;
        cWorld@ world=cLux_GetCurrentMap().GetWorld();
        bool ok=true;
        for(int n=0;n<12;n++){
            bool shown=guide.Show(world,"HRGuide","entities/station/gameplay/omnitool/omnitool.dae",cMatrixf_Identity);
            ok=ok && shown && guide.mpMesh !is null;
            if(guide.mpMesh !is null){
                ok=ok && !guide.mpMesh.GetScriptableIsSaved();
                // cMeshEntity exposes setters; flags are queried on its submeshes.
                for(int j=0;j<guide.mpMesh.GetSubMeshEntityNum();j++){
                    ok=ok && guide.mpMesh.GetSubMeshEntity(j).GetCustomMaterial() !is null;
                    ok=ok && !guide.mpMesh.GetSubMeshEntity(j).GetRenderFlagBit(eRenderableFlag_ShadowCaster);
                }
            }
            guide.Hide();
            ok=ok && guide.Show(world,"HRGuide","entities/station/gameplay/omnitool/omnitool_with_cortexchip.dae",cMatrixf_Identity);
            guide.Dispose(world);ok=ok && guide.mpMesh is null;
        }
        LogNewLine("HR_GUIDE|lifecycle="+ok);
'''
    text=text.replace('bool ready=false;', 'bool ready=false; bool ijStarted=false;')
    text=text.replace('// Same charge','if(!ijStarted){ijStarted=true;cScript_RunGlobalFunc("VRCOMFORT","STUTTER","START");}wait+=dt;if(wait>3){cScript_RunGlobalFunc("State_Conversation","","_Global_HRConversationTest");'+readprobe+'LogNewLine("HR_VM_DONE");cScript_RunGlobalFunc("VRCOMFORT","STUTTER","SAVE");cEngine_Exit();return;}\n  // Same charge',1)
    put(m,text)
    if a.controls:
        control='cLux_GetCurrentMap().CreateEntity("HRControl","entities/station/tech/control_board_pplant/control_board_pplant_button.ent",cMatrixf_Identity,cVector3f(1));cScript_RunGlobalFunc("HRControl","","_Global_HRControlProbe");'
        text=text.replace('LogNewLine("HR_VM_DONE")',control+'LogNewLine("HR_VM_DONE")')
        put(m,text)
    cfg=(G/'config/pump_lab_init.cfg').read_text().replace('SOMA_VR_PumpLab','SOMA_VR_HR_VM')
    cfg=cfg.replace('config/default_user_settings.cfg','config/hr_vm_user.cfg')
    defaults=(G/'config/default_user_settings.cfg').read_text()
    defaults+='\n<Screen Width="1280" Height="720" FullScreen="false" Vsync="false" RefreshRate="60" />\n<Engine LimitFPS="false" SleepWhenOutOfFocus="false" />\n<Main ShowMenu="false" FirstGameStart="false" SaveConfig="false" />\n'
    put(G/'config/hr_vm_user.cfg',defaults)
    put(G/'config/hr_vm_init.cfg',cfg)
    si=subprocess.STARTUPINFO();si.dwFlags=1;si.wShowWindow=0
    started=time.time()
    put(G/'hpl3vr-store.dll',(R/'build/store-roomscale-test/hpl3vr-store.dll').read_bytes())
    proc=subprocess.Popen([str(G/'Soma_NoSteam.exe'),'-user','HRTest','-cfg','config/hr_vm_init.cfg'],cwd=G,startupinfo=si,creationflags=4)
    injection=subprocess.run([str(G/'hpl3vr_inject.exe'),'Soma_NoSteam.exe','hpl3vr-store.dll'],cwd=G,input='\n',capture_output=True,text=True,timeout=25)
    assert 'SUCCESS' in injection.stdout, injection.stdout+injection.stderr
    resume=ctypes.WinDLL('ntdll').NtResumeProcess;resume.argtypes=[ctypes.c_void_p];resume.restype=ctypes.c_long
    assert resume(int(proc._handle))==0
    try:code=proc.wait(timeout=60)
    except subprocess.TimeoutExpired:proc.terminate();code=proc.wait(timeout=10)
    docs=subprocess.run(['powershell','-NoProfile','-Command',"[Environment]::GetFolderPath('MyDocuments')"],capture_output=True,text=True).stdout.strip()
    logfile=Path(docs)/'My Games/Soma/SOMA_VR_HR_VM/hpl.log'
    assert logfile.exists() and logfile.stat().st_mtime >= started, 'No fresh game log: run is invalid'
    log=logfile.read_text(errors='replace') if logfile.exists() else 'MISSING LOG'
    out=R/'docs/v109-evidence';out.mkdir(exist_ok=True)
    name=('roomscale_native_candidate_ie' if a.candidate else 'roomscale_native_baseline_ie') if a.roomscale else ('guide_vm_probe' if a.guides else ('control_vm_probe' if a.controls else ('readable_vm_probe' if a.readables else ('conversation_vm_baseline' if a.baseline else 'conversation_vm_candidate'))))
    if a.walking: name+='_walking'
    if a.repeated: name+='_repeated'
    (out/(name+'.log')).write_text(log)
    lines=[x for x in log.splitlines() if 'HR_' in x or 'ERR' in x or 'IE_' in x]
    result={'exit':code,'source_sha256':identity,'lines':lines,'scope':__doc__}
    (out/(name+'.json')).write_text(json.dumps(result,indent=2));print('\n'.join(lines))
    assert 'IE_TIMING|' in log and 'IE_ACCEPT|' in log, 'Timing probe did not execute'
    rows=[]
    for line in log.splitlines():
        if line.startswith('IE_TIMING|'):
            row=dict(x.split('=',1) for x in line.split('|')[1:]);row['body']=list(map(float,row['body'].split(',')));row['camera']=list(map(float,row['camera'].split(',')));rows.append(row)
    before=next(x for x in rows if x['tick']=='102' and x['phase']=='pre')
    after=next(x for x in rows if x['tick']=='102' and x['phase']=='after_move')
    bodyDelta=after['body'][0]-before['body'][0];cameraDelta=after['camera'][0]-before['camera'][0]
    assert abs(bodyDelta-.05)<.00001
    if a.candidate:
        assert 'IE_ACCEPT|native=true' in log
        assert abs(cameraDelta-bodyDelta)<.00001
        if not a.walking:
            for row in rows: assert abs((row['body'][0]-row['camera'][0])-.025)<.00001
        assert float(before['speed'])>.1
        assert abs(float(after['speed'])-float(before['speed']))<.0001
        assert after['moved']==before['moved']
        if a.walking: assert before['moved']=='true'
    else: assert cameraDelta-bodyDelta>.02
    if a.repeated:
        for tick in range(100,107):
            pre=next(x for x in rows if x['tick']==str(tick) and x['phase']=='pre')
            post=next(x for x in rows if x['tick']==str(tick) and x['phase']=='after_move')
            for k in range(3): assert abs((post['body'][k]-pre['body'][k])-(post['camera'][k]-pre['camera'][k]))<.00001
            assert abs(float(pre['speed'])-float(post['speed']))<.0001
            assert pre['moved']==post['moved']
    assert 'HR_CONVERSATION|failures=0' in log and 'HR_VM_DONE' in log
    if a.roomscale:
        assert 'IF_CROUCH|denied=true|down=true|up=true' in log
        assert 'IE_STEP_NOISE|silent=true' in log
        assert 'IE_STEP_TRAVEL|count=1' in log
        assert 'IE_STEP_SOUND|played=true' in log
        assert 'HR_ROOM_QUERY|free=true|blocked=true|unchanged=true' in log
        assert 'HR_ROOM_MOVE|moved=true|momentum=true|bounded=true' in log
        assert 'HR_ROOM_OBSTACLE|stopped=true' in log
        assert "Could not find script object 'VRROOM'" not in log
    if a.guides:
        assert 'HR_GUIDE|lifecycle=true' in log
        assert 'HR_GUIDE|inactiveDenied=true' in log
        assert 'HR_GUIDE|permission=true' in log
        assert 'HR_GUIDE|canCalls=4|useCalls=0' in log
        assert 'HR_GUIDE|itemMesh=true' in log
    if a.controls:
        assert 'HR_CONTROL_RESULT|accepted=true|changed=true|cooldownReject=true' in log
    if a.readables:
        assert 'HR_READABLE|name=HRNotepad|ok=true' in log and 'HR_READABLE|name=HRBook|ok=true' in log
        assert log.count('|hasOpen=false|mass=0.200000')==2
        assert log.count('|direct=true|directDisplay=true|remote=true|remoteDisplay=false|directAgain=true|restoredDisplay=true')==2
    import struct
    capture=G/'hpl3vr_stutter.bin'
    assert capture.stat().st_mtime >= started
    data=capture.read_bytes();header=struct.unpack_from('<8Q',data)
    assert header[4]>0 and len(data)==64+header[4]*header[2]
finally:
    if proc is not None and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
    for path,data in reversed(list(saved.items())):
        if data is None:path.unlink(missing_ok=True)
        else:path.write_bytes(data)


