"""Native retention hinge load test, authentic scaled entities. Synthetic external force, no controller contacts."""
from pathlib import Path
import sys
hz=int(sys.argv[1]);assert hz in (60,120)
variant=sys.argv[2];assert variant in ('baseline','stiff')
r=Path(__file__).resolve().parents[1]
s=(r/'tests/probe_jb_env_geometry.py').read_text()
s=s.replace("out=R/'audit/jb-env-geometry'", "out=R/'audit/je-latch-load'")
a=s.index(" fixture='");b=s.index(" i=s.index",a)
fixture=r"""
 [nosave] float mfJELoadTime=0,mfJEMax=0;[nosave] bool mbJEInit=false;[nosave] cVector3f mvJEPivot,mvJELocal;
 void JBProbe(float dt){mfJELoadTime+=dt;if(mfJELoadTime<3)return;
 cLuxProp@ prop=Map_GetProp("JERetention");
 if(prop is null){cMatrixf m=cMatrixf_Identity;m.SetTranslation(cVector3f(2.2f,4.9f,-96.5f));cLux_GetCurrentMap().CreateEntity("JERetention","entities/station/gameplay/electric_switch/retention_mechanism.ent",m,cVector3f(.35f,.25f,.25f));return;}
 iPhysicsBody@ b=prop.GetMainBody();iPhysicsJoint@ j=prop.GetJoint(0);
 if(!mbJEInit){mbJEInit=true;cLux_GetPlayer().GetCharacterBody().SetFeetPosition(cVector3f(2.2f,3.4f,-95.5f),false);cEngine_SetUpdatesPerSec(HZ);mvJEPivot=j.GetPivotPoint();mvJELocal=cMath_MatrixMul(cMath_MatrixInverse(b.GetWorldMatrix()),mvJEPivot);LogNewLine("JE_LOAD_BEGIN|variant=VARIANT|hz=HZ|mass="+b.GetMass());}
 if(mfJELoadTime>4 && mfJELoadTime<5){prop.WakeUp();b.AddForce(cVector3f(100,100,100));}
 float err=cMath_Vector3Dist(cMath_MatrixMul(b.GetWorldMatrix(),mvJELocal),mvJEPivot);if(err>mfJEMax)mfJEMax=err;
 if(mfJELoadTime<7)return;
 LogNewLine("JE_LOAD_END|variant=VARIANT|hz=HZ|max="+mfJEMax+"|settled="+err+"|angle="+cPhysics_ToJointHinge(j).GetAngle());LogNewLine("IL_DONE|NONCE");cEngine_Exit();}
""".replace('HZ',str(hz)).replace('VARIANT',variant)
setup=""
if variant=='stiff':
 setup=" p=G/'entities/station/gameplay/electric_switch/retention_mechanism.ent';asset=p.read_text(encoding='utf-8-sig');assert 'Stiffness=\"0\"' in asset;put(p,asset.replace('Stiffness=\"0\"','Stiffness=\"1\"'))\n"
s=s[:a]+setup+' fixture='+repr(fixture)+'.replace("NONCE",nonce)\n'+s[b:]
s=s.replace("'JB_ENV' in x", "'JE_' in x")
exec(compile(s,str(r/'tests/probe_jb_env_geometry.py'),'exec'))
