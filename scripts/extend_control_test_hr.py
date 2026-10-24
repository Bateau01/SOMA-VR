from pathlib import Path
p=Path('tests/test_registered_controls_hr.py');s=p.read_text().replace("b=s.index('\\nstatic void s26z_retire',a)","b=s.index('// One first-hit ray',a)");s=s.replace('used,active,blocked,frontAxis;','used,active,blocked,frontAxis,handMask;');s=s.replace('float tip[3]={0,.01,0},dir[3]={0,-1,0};','float tip[3]={0,.01,0},dir[3]={0,-1,0};');s=s.replace('printf("PASS %d registered', '''// Explicit palm path preserves permission and rejects back-facing contact.
 for(auto&r:g_s26yRocker){r.blocked=0;r.handMask=0;}
 calls=0;float badDir[3]={0,1,0};
 C(s26hr_control_contact(0,childW[0],&owner[0],tip,badDir,0,.005f)==1);C(calls==0);
 C(s26hr_control_contact(0,childW[0],&owner[0],tip,dir,0,.005f)==1);C(calls==1);
 C(s26hr_control_contact(0,childW[1],&owner[0],tip,dir,0,.005f)==1);C(calls==1);
 printf("PASS %d registered''');p.write_text(s)
