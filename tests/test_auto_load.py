"""Execute the production no-recap completion method with engine state mocks."""
from pathlib import Path
import subprocess,sys,json
R=Path(__file__).resolve().parents[1]
s=(R/'runtime/script/modules/MenuHandler.hps').read_text()
a=s.index('void HPL3VR_FinishAutoLoad()');b=s.index('\n\tvoid Update',a)
method=s[a:b].replace('cLux_GetSaveHandler().','save.')
header=r'''
#include <cstdio>
#include <cstdlib>
bool mbHPL3VRAutoLoadPending,done,loaded,changing,visible;
int handoffs,starts,checks;
#define CHECK(x) do{checks++;if(!(x)){printf("FAIL %d\n",__LINE__);exit(1);}}while(0)
struct Save{bool IsDoneLoadingSavedGame(){return done;}void StartLoadedGame(){CHECK(handoffs==starts+1);starts++;}}save;
bool cLux_MapIsLoaded(){return loaded;}
bool cLux_IsChangingMap(){return changing;}
bool LoadScreen_IsVisible(){return visible;}
void cScript_RunGlobalFunc(const char*,const char*,const char*){handoffs++;}
void LogNewLine(const char*){}
'''
body=r'''
int main(){
for(int p=0;p<2;p++)for(int d=0;d<2;d++)for(int l=0;l<2;l++)for(int c=0;c<2;c++)for(int v=0;v<2;v++){
mbHPL3VRAutoLoadPending=p;done=d;loaded=l;changing=c;visible=v;handoffs=starts=0;
HPL3VR_FinishAutoLoad();bool expected=p&&d&&l&&!c&&!v;
CHECK(handoffs==expected&&starts==expected);
CHECK(mbHPL3VRAutoLoadPending==(p&&!expected));
HPL3VR_FinishAutoLoad();CHECK(handoffs==expected&&starts==expected);
}
printf("PASS %d no-recap completion checks: readiness, one-shot handoff, start ordering\n",checks);
}
'''
start=s[s.index('void Start(const tString &in asEntry)'):s.index('void CleanUp()')]
assert 'ContinueLoading(!bVRLoad)' in start
assert start.index('CleanUp();')<start.index('mbHPL3VRAutoLoadPending = bVRLoad;')
update=s[s.index('void Update(float afTimeStep)',a):]
assert update.index('HPL3VR_FinishAutoLoad();')<update.index('if (!(_HPL3VR_RuntimeActive_Menu()')
B=R/'build';B.mkdir(exist_ok=True);cpp=B/'auto_load.cpp';exe=B/'auto_load.exe';cpp.write_text(header+method+body)
subprocess.run([sys.argv[1],'c++','-O2',str(cpp),'-o',str(exe)],check=True)
result=subprocess.run([str(exe)],capture_output=True,text=True);print(result.stdout+result.stderr)
(R/'audit/auto_load_tests.json').write_text(json.dumps({'exit':result.returncode,'output':result.stdout,'scope':'Production script helper translated to C++ with engine mocks; native VM tested separately.'},indent=2))
raise SystemExit(result.returncode)
