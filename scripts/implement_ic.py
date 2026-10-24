from pathlib import Path
r=Path(__file__).resolve().parents[1]
p=r/'source/roomscale_hr.inc';s=p.read_text()
s=s.replace('static i32 g_s26hrRoomPending;','''static i32 g_s26hrRoomPending;
// Excluded physical motion is a locomotion baseline, NOT a camera-origin write.
// This keeps hands/view unchanged when leaving a terminal, pause or script.
static i32 g_s26icRoomSuspend,g_s26icRoomSample;
static u32 g_s26icRoomEpoch;
static float g_s26icRoomNeutral[2],g_s26icRoomHead[2];''')
s=s.replace('g_s26hrRoomPending=0;return 1;','g_s26hrRoomPending=0;g_s26icRoomSuspend=1;return 1;',1)
s=s.replace('{g_s26hrRoomPending=0;return 0;}','{g_s26hrRoomPending=0;g_s26icRoomSuspend=1;return 0;}',1)
s=s.replace('''        g_s26hrRoomFrame=g_frameCounter;g_s26hrRoomPending=0;
        volatile float* head=p2_eye_mid();float x=head[0]-origin[0],z=head[2]-origin[2];
        float length=h10_len3(x,0,z);if(!h9_good(length,1.0f)||length<=.10f)return 0;''','''        u32 gap=g_frameCounter-g_s26hrRoomFrame;
        g_s26hrRoomFrame=g_frameCounter;g_s26hrRoomPending=0;
        volatile float* head=p2_eye_mid();float x=head[0]-origin[0],z=head[2]-origin[2];
        if(!h9_good(x,32.0f)||!h9_good(z,32.0f)){
            g_s26icRoomSuspend=1;g_s26icRoomSample=0;return 0;
        }
        if(g_s26icRoomEpoch!=g_h5735RecenterRequests){
            g_s26icRoomNeutral[0]=g_s26icRoomNeutral[1]=0;
            g_s26icRoomSample=0;g_s26icRoomEpoch=g_h5735RecenterRequests;
        }
        i32 discontinuity=g_s26icRoomSample && (gap>4u ||
            h10_len3(head[0]-g_s26icRoomHead[0],0,head[2]-g_s26icRoomHead[1])>.50f);
        g_s26icRoomHead[0]=head[0];g_s26icRoomHead[1]=head[2];g_s26icRoomSample=1;
        if(g_s26icRoomSuspend || discontinuity){
            g_s26icRoomNeutral[0]=x;g_s26icRoomNeutral[1]=z;
            g_s26icRoomSuspend=0;return 0;
        }
        x-=g_s26icRoomNeutral[0];z-=g_s26icRoomNeutral[1];
        float length=h10_len3(x,0,z);if(!h9_good(length,64.0f)||length<=.10f)return 0;''')
p.write_text(s)
p=r/'runtime/script/helpers/helper_vr_roomscale_hr.hps'
s=p.read_text();start=s.index('        else {');end=s.index('\n        if(cMath_Vector3Dist',start)
s=s[:start]+'''        else {
            // Native overlap correction supplies a contact direction. Slide in
            // its horizontal tangent, never a fixed world-X/world-Z order.
            // Every candidate is checked; ambiguous/vertical-only contact stops.
            cVector3f slide=step;
            for(int plane=0;plane<2;plane++){
                push.y=0;
                float n2=push.x*push.x+push.z*push.z;
                if(!(n2>.0000000001f && n2<100.0f))break;
                float dot=slide.x*push.x+slide.z*push.z;
                if(dot>=0)break;
                slide=slide-push*(dot/n2);
                if(!(slide.Length()>.000001f && slide.Length()<=step.Length()+.000001f))break;
                next=at+slide;
                if(body.CheckCharacterFits(next,false,-1,push)){at=next;break;}
            }
        }'''+s[end:];p.write_text(s)
for rel in ['source/s26n.c','scripts/build_store.py','runtime/script/modules/MenuHandler.hps']:
 p=r/rel;p.write_bytes(p.read_bytes().replace(b'S26IA',b'S26IC'))
for n in ['Build.ps1','Installer.cs','CurrentUpgradeTests.cs']:
 p=r/'installer/source'/n;p.write_bytes(p.read_bytes().replace(b'S26IB',b'S26IC').replace(b'2026102303',b'2026102304'))
(r/'build').mkdir(exist_ok=True);(r/'installer/output').mkdir(exist_ok=True)
print('IC candidate changes prepared')
