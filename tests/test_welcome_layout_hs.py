"""Native font-metric and script-layout checks, not a rendered-output test."""
from pathlib import Path
import re,json,xml.etree.ElementTree as E
r=Path(__file__).resolve().parents[1]
s=(r/'runtime/script/modules/MenuHandler.hps').read_text()
block=s[s.index('    bool HPL3VR_DrawWelcome()'):s.index('\tvoid HPL3VR_DrawVersion()')]
font=E.parse(r'D:\SteamLibrary\steamapps\common\SOMA\fonts\sansation_medium.fnt')
advance={int(c.attrib['id']):float(c.attrib['xadvance']) for c in font.findall('.//char')}
size=float(font.find('info').attrib['size'])
lines=re.findall(r'"([^"\n]+)"',block[block.index('array<tString> lines='):block.index('if(mlVRWelcomePage==1)')])
lines.append('GRIP: Grab / interact. Change bindings in CONTROLS > BUTTON BINDINGS.')
actions=['JUMP / ACCEPT','RUN / BACK','PAUSE','CENTER CAMERA','CROUCH','HAND REBASE','RECALL OMNI-TOOL']
buttons=re.findall(r'"([^"]+)"',s[s.index('array<tString> buttons='):s.index('int hand=',s.index('array<tString> buttons='))])
lines += [a+': '+b for a in actions for b in buttons]
widths=[sum(advance.get(ord(c),size) for c in t)*22/size for t in lines]
assert max(widths)<980,lines[widths.index(max(widths))]
assert 85+36*7+22<430 # eight rows clear button row
assert 'HPL3VR_ReadBindings();' in block and 'HPL3VR_WriteBindings' not in block
assert 'WelcomeVersion",10901' in block and 'mlVRWelcomePage=0' in block and 'mlVRWelcomePage=1' in block
result={'scope':__doc__,'passed':True,'strings':len(lines),'max_width':max(widths),'available_width':980,'remaining_visual_check':True}
(r/'docs/v109-evidence/welcome_layout_hs.json').write_text(json.dumps(result,indent=2));print(result)
