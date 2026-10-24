from pathlib import Path
r=Path('.');p=r/'runtime/maps/chapter01/01_03_upsilon_outside/01_03_upsilon_outside.hps';s=p.read_text(encoding='utf-8-sig')
s='#include "helpers/helper_vr_escape_hw.hps"\n'+s
s=s.replace('class cScrMap : iScrMap\n{','class cScrMap : iScrMap\n{\n    [nosave] cVREscapeGuideHW mVREscapeGuide;\n    bool mbVREscapeIntroOver=false;\n    bool mbVREscapeFinished=false;\n    void Update(float dt){mVREscapeGuide.Update(dt,mbVREscapeIntroOver,mbVREscapeFinished);}\n',1)
s=s.replace('bool IntroOver(const tString &in asEntity, int alDirection)\n\t{','bool IntroOver(const tString &in asEntity, int alDirection)\n\t{\n        mbVREscapeIntroOver=true;',1)
s=s.replace('void AreaClimbHole_OnPlayerInteract(const tString &in asEntity)\n\t{','void AreaClimbHole_OnPlayerInteract(const tString &in asEntity)\n\t{\n        mVREscapeGuide.Hide();',1)
s=s.replace('void HandAnimOver_ClimbedOut(const tString&in asAnim)\n\t{','void HandAnimOver_ClimbedOut(const tString&in asAnim)\n\t{\n        mbVREscapeFinished=true;mVREscapeGuide.Hide();',1)
s=s.replace('void OnLeave()\n\t{','void OnLeave()\n\t{\n        mVREscapeGuide.Dispose();',1)
p.write_text(s,encoding='utf-8')
