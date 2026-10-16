"""Exercise production page gates and value preservation, without claiming UI validation."""
from pathlib import Path
import re, subprocess, sys
R=Path(__file__).resolve().parents[1]
s=(R/'runtime/script/modules/MenuHandler.hps').read_text()
def fn(name):
    a=re.search(r'    (?:int|bool) '+name+r'\(',s).start()
    b=s.index('{',a);d=1;i=b+1
    while d:
        d+=(s[i]=='{')-(s[i]=='}');i+=1
    return s[a:i].replace('const tString &in','const tString &').replace('array<tString> &in','std::vector<tString> &')
code=r'''
#include <string>
#include <vector>
#include <cassert>
#include <cstdio>
using tString=std::string;
int mlVRComfortCategory=-1,mvVRSettingsPages[11]={},mlActionHorizontal,kMainMenuButtonPos,draws,lastRow;
tString msVRSettingsSelected;
bool OptionMenu_ButtonOptions(const tString&,int,int row,tString&){draws++;lastRow=row;return true;}
tString OptionMenu_UpdateFocus(const tString& l,const tString&){return l;}
bool OptionMenu_ButtonOptionsToggle(const tString&,int,int row,tString&,bool value,int){draws++;lastRow=row;return !value;}
int OptionMenu_ButtonOptionsMultiSelect(const tString&,int,int row,tString&,std::vector<tString>&,int v,bool,int,const char*){draws++;lastRow=row;return v+1;}
float OptionMenu_ButtonOptionsSlider(const tString&,int,int row,tString&,float v,float step,int,const tString&){draws++;lastRow=row;return v+step;}
float cMath_Clamp(float v,float a,float b){return v<a?a:v>b?b:v;}
void ImGui_SetTransCategory(const char*){}
'''
for n in ['HPL3VR_Page','HPL3VR_RowVisible','HPL3VR_Navigation','HPL3VR_Option','HPL3VR_Toggle','HPL3VR_Multi','HPL3VR_Slider']:code+=fn(n)+'\n'
code+=r'''
int main(){int cases=0;std::vector<tString> values={"A","B"};
 for(int count=1;count<=40;count++)for(int page=0;page<(count+7)/8;page++){
  mlVRComfortCategory=0;mvVRSettingsPages[0]=page;int shown=0;
  for(int row=0;row<count;row++){
   bool visible=row/8==page;draws=0;msVRSettingsSelected="unchanged";
   assert(HPL3VR_Option("action",row)==visible);
   assert(HPL3VR_Toggle("toggle",row,true)==!visible);
   assert(HPL3VR_Multi("multi",row,values,0)==(visible?1:0));
   assert(HPL3VR_Slider("slider",row,3,10,"")==(visible?4:3));
   assert(draws==(visible?4:0));
   if(visible){assert(lastRow==row%8);shown++;}else assert(msVRSettingsSelected=="unchanged");cases++;
  }
  assert(shown<=8);draws=0;assert(HPL3VR_Navigation("BACK",shown+1));assert(draws==1);
 }
 // Child navigation must not overwrite its parent's page.
 mvVRSettingsPages[0]=1;mlVRComfortCategory=10;assert(HPL3VR_Page()==0);
 mlVRComfortCategory=0;assert(HPL3VR_Page()==1);
 printf("PASS %d page visibility/value/focus cases; navigation and parent-page retention\n",cases);
}
'''
b=R/'build/settings_pages_hf.cpp';b.write_text(code)
subprocess.run([sys.argv[1],'c++','-O2',str(b),'-o',str(b.with_suffix('.exe'))],check=True)
subprocess.run([str(b.with_suffix('.exe'))],check=True)
assert 'HPL3VR_Navigation("BACK",navigationRow)' in s
assert 'size.y=170+38*(visibleRows+' in s
print('Runtime script compilation and headset layout still require a game launch.')

assert 'PREVIOUS PAGE' not in s
for label,row in [('REMOTE GRAB',2),('TERMINAL LASER POINTER',3),('CALIBRATE STANDING HEIGHT',9),('CENTER CAMERA',10),('INTERACTION LASER POINTER',11),('BUTTON BINDINGS',7),('RESET FINGER TRACKING',8)]:
 assert re.search(r'HPL3VR_(?:Option|Toggle)\("'+re.escape(label)+r'",'+str(row)+r'[,)]',s),(label,row)
back=s[s.index('void HPL3VR_BackSettings()'):s.index('void HPL3VR_RequestSimulationMode')]
assert back.index('HPL3VR_Page()>0')<back.index('if(mlVRComfortCategory==9)')
assert 'mvVRSettingsPages[mlVRComfortCategory]--;' in back
assert 'InteractionLaser",false' in s
print('PASS requested row assignments, BACK-before-parent behavior and default-OFF interaction pointer')
