"""Synthetic sampled fingertip trajectories fed to real native ImGui widgets; no physical tracking or story validation."""
from pathlib import Path
import subprocess,sys,json
R=Path(__file__).resolve().parents[1]
scope={'__file__':str(R/'tests/test_fast_touch_jh.py')};text=(R/'tests/test_fast_touch_jh.py').read_text();exec(text[:text.index("p=R/'build/fast_touch_jh.cpp'")],scope)
head=scope['head'];old=(R/'tests/fixtures/jh/terminal_sweep_before.inc').read_text().replace('s26hr_terminal_sample','old_sample')
new=(R/'source/terminal_sweep_hr.inc').read_text()
main=r'''
int main(){for(int mode=0;mode<2;mode++)for(int k=0;k<4;k++){
 S26HRTerminalSample s={};float starts[4]={-.05f,.8f,.2f,.2f},ends[4]={.2f,1.1f,.5f,.7f};
 float u=starts[k],v=.5f,p=.06f;auto fn=mode?s26hr_terminal_sample:old_sample;
 fn(&s,&u,&v,&p,.008f,1,1,(void*)1,1);
 u=ends[k];p=k==2?.01f:-.06f;int hit=fn(&s,&u,&v,&p,.008f,2,1,(void*)1,1);
 printf("%d %.6f %.6f\n",hit,u*512,v*512);
 }return 0;}
'''
p=R/'build/fast_widget_jh.cpp';p.write_text(head+old+new+main)
subprocess.run([sys.argv[2],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
v=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True,check=True)
records=[line.split() for line in v.stdout.splitlines()];assert len(records)==8
(R/'audit/jh-fast-touch/widget-traces.json').write_text(json.dumps(records,indent=2))
trace='array<int> hits={'+','.join(x[0] for x in records)+'};array<float> xs={'+','.join(x[1]+'f' for x in records)+'};'
probe=trace+r'''array<float> expected={17.066667f,460.8f,225.28f,187.733333f};
for(int test=0;test<8;test++){
 gui.ClearStates();int accepted=0,wrong=0;
 for(int frame=0;frame<4;frame++){
 gui.Begin(1.0f/60.0f);gui.SetShowMouse(true);
 cVector2f pos(xs[test],256);gui.SendMouseVirtualPosition(pos,cVector2f(1));gui.SendMouseVirtualPosition(pos,cVector2f(1));
 bool down=hits[test]>0&&frame==1;gui.SendAction(eImGuiAction_MouseLeft,down,down);
 if(gui.DoButton("TARGET",tWString(""),data,cVector3f(expected[test%4]-8,240,1),cVector2f(16,32)))accepted++;
 if(gui.DoButton("NEIGHBOR",tWString(""),data,cVector3f(250,240,1),cVector2f(16,32)))wrong++;
 gui.End();}
 LogNewLine("JH_WIDGET|test="+test+"|accepted="+accepted+"|wrong="+wrong);
} '''
s=(R/'tests/test_widget_probe_hs.py').read_text()
a=s.index('for(int test=0;test<6;test++){');b=s.index('cGui_DestroyImGui(gui);',a)
s=s[:a]+probe.replace('\n',' ').replace("'","\\'")+s[b:]
a=s.index('  widget_ok=');b=s.index('\n  ok=',a)
s=s[:a]+'''  widget_ok=all(('JH_WIDGET|test='+str(i)+'|accepted=1|wrong=0') in log for i in range(4,8)) and all(('JH_WIDGET|test='+str(i)+'|accepted=0|wrong='+str(1 if i==2 else 0)) in log for i in range(4))'''+s[b:]
s=s.replace("out=R/'docs/v109-evidence'","out=R/'audit/jh-fast-touch'").replace('widget_probe_hs.json','native-widget.json')
s=s.replace("'HR_STORY' in x or", "'JH_WIDGET' in x or 'HR_STORY' in x or")
exec(compile(s,str(R/'tests/test_widget_probe_hs.py'),'exec'))
