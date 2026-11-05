"""Native acquisition with controlled head pitch; not physical gamepad validation."""
from pathlib import Path
import sys,re,json
r=Path(__file__).resolve().parents[1]
s=(r/'tests/test_native_input_capture.py').read_text()
if '--store-cpu65' in sys.argv:
 s=s.replace("'build/store-cpu65'","'build/store-ja-test'").replace("assert '--production-payload' in sys.argv and '--movement-replay' not in sys.argv","assert '--movement-replay' not in sys.argv").replace("dict(raw['options'],production=True)","dict(raw['options'],production=False)")
needle=" # Replace a leftover old fixture script"
inject=r''' grabPath=G/'script/player/PlayerState_Interact_Grab.hps'
 grab=grabPath.read_text(encoding='utf-8-sig')
 probe="""
 void _Global_JAProbe(){
  cCamera@ cam=mBaseObj.mpPlayer.GetCamera();iPhysicsBody@ body=cLux_ID_Body(mBodyID);
  if(body is null){LogNewLine("JA_NO_BODY");return;}
  cMatrixf rotation=HPL3VR_GrabCameraRotation(cam);
  cVector3f expectedForward=cam.GetForward();
  float basisError=(cMath_MatrixMul(rotation,cVector3f(0,0,-1))-expectedForward).Length();
  cVector3f local=mbUseCustomOffset ? mvCustomPositionOffset+cVector3f(0,0,-mfDepth) : mvLocalBodyOffset+cVector3f(0,0,-mfDepth);
  cVector3f goal=cam.GetPosition()+cMath_MatrixMul(rotation,local);
  float positionError=(goal-body.GetLocalPosition()).Length();
  cMatrixf before=m_mtxBodyRotation;
  bool forwarded=OnAnalogInput(eAnalogType_GamepadRotate,cVector3f(0.2f,0.3f,0));
  float changed=(before.GetForward()-m_mtxBodyRotation.GetForward()).Length();
  LogNewLine("JA_ROTATE forwarded="+forwarded+" changed="+changed);
  LogNewLine("JA_HELD basisError="+basisError+" positionError="+positionError+" state="+Player_GetCurrentStateName());
 }
"""
 grab=grab.replace('void SetupGrab()',probe+'\nvoid SetupGrab()',1) if 'void SetupGrab()' in grab else grab.replace('void OnMapEnter(',probe+'\nvoid OnMapEnter(',1)
 if '--baseline-grab' in sys.argv:grab=grab.replace('return cMath_MatrixInverse(cam.GetViewMatrix()).GetRotation();','return cMath_MatrixRotateXYZ(cVector3f(cam.GetPitch(),cam.GetYaw(),cam.GetRoll()));')
 put(grabPath,grab)
'''
s=s.replace(needle,inject+needle,1)
s=s.replace('Map_AddTimer("NI_SPAWN",8.0f','Map_AddTimer("NI_SPAWN",1.0f')
s=s.replace('cCamera@ cam=cLux_GetPlayer().GetCamera();cMatrixf pose=', 'cScript_RunGlobalFunc("NITEST","","HEAD_UP");cCamera@ cam=cLux_GetPlayer().GetCamera();cMatrixf pose=')
s=s.replace('cScript_RunGlobalFunc("NITEST","","CHECK");Map_AddTimer("NI_RELEASE",0.5f', 'cScript_RunGlobalFunc("NITEST","","CHECK");Map_AddTimer("JA_VERIFY",1.0f')
s=s.replace('}else if(name=="NI_RELEASE"){','}else if(name=="JA_VERIFY"){cScript_RunGlobalFunc("State_Interact_Grab","","_Global_JAProbe");cScript_RunGlobalFunc("NITEST","","HEAD_RESET");Map_AddTimer("NI_RELEASE",0.5f,"NIAcquire");}else if(name=="NI_RELEASE"){')
s=s.replace('LogNewLine("IU_STAGE|"+phase','if(phase==0)cScript_RunGlobalFunc("NITEST","","HEAD_UP");LogNewLine("IU_STAGE|"+phase')
s=s.replace('void NIAcquire(const tString &in name){','float jaP=0,jaY=0;void NIAcquire(const tString &in name){')
s=s.replace('}else if(name=="NI_DONE"){','}else if(name=="JA_LOOK_DONE"){cCamera@ cam=cLux_GetPlayer().GetCamera();LogNewLine("JA_LOOK pitch="+jaP+"->"+cam.GetPitch()+" yaw="+jaY+"->"+cam.GetYaw());}else if(name=="NI_DONE"){cCamera@ cam=cLux_GetPlayer().GetCamera();jaP=cam.GetPitch();jaY=cam.GetYaw();cScript_RunGlobalFunc("NITEST","","LOOK");Map_AddTimer("JA_LOOK_DONE",0.2f,"NIAcquire");')
if '--head-down' in sys.argv:s=s.replace('HEAD_UP','HEAD_DOWN')
ns={'__file__':str(r/'tests/test_native_input_capture.py'),'__name__':'__main__'}
exec(compile(s,str(r/'tests/test_native_input_capture.py'),'exec'),ns)
out=ns['out'];log=(out/'hpl.log').read_text(errors='replace');vr=(out/'hpl3vr.log').read_text(errors='replace')
rows=re.findall(r'JA_HELD basisError=([\d.e+-]+) positionError=([\d.e+-]+) state=(\S+)',log)
assert rows,'No held transform evidence'
rot=re.findall(r'JA_ROTATE forwarded=false changed=([\d.e+-]+)',log)
assert rot and all(float(v)>.001 for v in rot),'Native object rotation input was lost'
for basis,pos,state in rows:assert (float(basis)>.2 if '--baseline-grab' in sys.argv else float(basis)<.002) and float(pos)<.2 and state=='State_Interact_Grab',(basis,pos,state)
look=re.findall(r'JA_LOOK pitch=([\d.e+-]+)->([\d.e+-]+) yaw=([\d.e+-]+)->([\d.e+-]+)',log)
assert look,'No delayed native camera observation'
for p0,p1,y0,y1 in look:assert abs(float(p1)-float(p0))<1e-5 and abs(float(y1)-float(y0))>1e-4,(p0,p1,y0,y1)
(out/'ja-result.json').write_text(json.dumps(dict(held=rows,look=look,scope=__doc__),indent=2))
print('JA PASS',rows,look)
