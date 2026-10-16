from pathlib import Path
import subprocess,sys,ast
R=Path(__file__).resolve().parents[1];B=R/'build';B.mkdir(exist_ok=True);s=(R/'source/s26n.c').read_text()
tree=ast.parse((R/'tests/test_carrier_handoff_gl.py').read_text());head=next(n.value.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='head' for t in n.targets))
a=s.index('static void h576av_update_theta_handoff(');b=s.index('/* BJ:',a);handoff=s[a:b]
a=s.index('static i32 s26eu_arm_chip_handoff(');b=s.index('static i32 h576k_try_latch_upgrade_chip_after_interact',a);arm=s[a:b]
extra=r"""
typedef struct {const void*newtonBody;u32 physicsStep;} H25PendingInteract;
static u32 g_h576kChipPickupTokens,g_h5755haGripEdgeStep[2];static int g_h576kChipPickupPending;
static const void*g_h576kChipPickupRaw;static void*g_h576kChipPickupOwner;static char g_h576kChipPickupName[96];
static void h5748n_copyz(char*d,unsigned n,const char*s){snprintf(d,n,"%s",s);}
static void prep(int h){reset();g_h576avThetaPendingHand=-1;g_s26gkThetaSourceBody=0;g_h14GripBody[0]=g_h14GripBody[1]=0;g_lastSqueezeActive[h]=1;g_lastSqueeze[h]=1;g_h5755haGripEdgeStep[h]=100;g_h576kChipPickupTokens=2;g_h576kChipPickupPending=1;g_h576kChipPickupRaw=item.raw;g_h576kChipPickupOwner=item.owner;strcpy(g_h576kChipPickupName,"chip");}
"""
main=r"""
int main(void){for(rate=1;rate<=2;rate++)for(int h=0;h<2;h++){
 H25PendingInteract p={(void*)2,100};
 prep(h);mass=0;C(s26eu_arm_chip_handoff(h,&p,1));g_h14PhysicsSteps++;h576av_update_theta_handoff();C(!g_h14GripBody[h]&&g_h576avThetaPendingHand==h);mass=.2f;g_h14PhysicsSteps++;h576av_update_theta_handoff();C(g_h14GripBody[h]==(void*)2&&g_h576avThetaPendingHand==-1);
 prep(h);p.newtonBody=(void*)1;C(s26eu_arm_chip_handoff(h,&p,1));g_h14PhysicsSteps++;h576av_update_theta_handoff();C(g_h14GripBody[h]==(void*)2);
 prep(h);C(!s26eu_arm_chip_handoff(h,&p,2));
 prep(h);g_lastSqueeze[h]=0;C(!s26eu_arm_chip_handoff(h,&p,1));
 prep(h);g_h14GripBody[h]=(void*)9;C(!s26eu_arm_chip_handoff(h,&p,1));
 prep(h);g_h14GripBody[1-h]=(void*)2;C(!s26eu_arm_chip_handoff(h,&p,1));
 prep(h);item.stowed=1;C(!s26eu_arm_chip_handoff(h,&p,1));
 prep(h);g_h576kChipPickupOwner=(void*)99;C(!s26eu_arm_chip_handoff(h,&p,1));
 prep(h);p.physicsStep=99;C(!s26eu_arm_chip_handoff(h,&p,1));p.physicsStep=100;
 prep(h);C(s26eu_arm_chip_handoff(h,&p,1));g_lastSqueeze[h]=0;g_h14PhysicsSteps++;h576av_update_theta_handoff();C(!g_h14GripBody[h]&&g_h576avThetaPendingHand==-1);
 prep(h);C(s26eu_arm_chip_handoff(h,&p,1));mass=0;g_h14PhysicsSteps+=12*rate+1;h576av_update_theta_handoff();C(!g_h14GripBody[h]&&g_h576avThetaPendingHand==-1);
 }printf("PASS %d same/replacement-body handoff checks, both hands, 60/120 Hz\n",checks);return 0;}
"""
c=B/'pickup_chain_gp.c';c.write_text(head+extra+handoff+arm+main);exe=c.with_suffix('.exe');subprocess.run([sys.argv[1],'cc','-O2',str(c),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
