from pathlib import Path
r=Path(__file__).resolve().parents[1]
p=r/'tests/test_registered_controls_hr.py';s=p.read_text()
s=s.replace('int h5754h_pause_active(){return 0;}','int h5754h_pause_active(){return 0;}\nint terminal;unsigned g_s26huWorldControlAllowed;int h5730_exact_terminal_state(int,int,int,int){return terminal;}')
s=s.replace(' printf("PASS %d registered control assertions',r'''
 for(int h=0;h<2;h++){
  terminal=1;g_s26huWorldControlAllowed=0;
  for(auto&r:g_s26yRocker){r.blocked=0;r.handMask=0;}
  calls=0;s26hr_control_contact(h,childW[0],&owner[0],tip,dir,0,.005f);C(calls==0);
  g_s26huWorldControlAllowed=1;
  s26hr_control_contact(h,childW[0],&owner[0],tip,dir,0,.005f);C(calls==1);
  s26hr_control_contact(h,childW[0],&owner[0],tip,dir,0,.005f);C(calls==1);
  for(auto&r:g_s26yRocker){r.blocked=0;r.handMask=0;}
  permitted=false;s26hr_control_contact(h,childW[0],&owner[0],tip,dir,0,.005f);C(calls==1);
  permitted=true;
 }
 printf("PASS %d registered control assertions''')
s=s.replace('registered_controls_hr','registered_controls_hu');(r/'tests/test_registered_controls_hu.py').write_text(s)
p=r/'tests/test_native_hu.py';s=p.read_text();s=s.replace("if name=='05_01_phi_inside':","if name=='05_01_phi_inside':") # follow-up harness remains maps with seats
p.write_text(s)

