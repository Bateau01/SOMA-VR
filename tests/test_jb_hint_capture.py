from pathlib import Path
import sys
r=Path(__file__).resolve().parents[1]
s=(r/'tests/test_native_input_capture.py').read_text()
needle=" menu=menu.replace('    void HPL3VR_UpdateComfort(float dt)',probe"
idx=s.index(needle)
s=s[:idx]+' probe=probe.replace(\'HPL3VR_PublishComfort();\',\'HPL3VR_PublishComfort();cScript_RunGlobalFunc("HintHandler","cScrHintHandler","JBTestHint");\')\n hp=G/\'script/modules/HintHandler.hps\';hs=hp.read_text(encoding=\'utf-8-sig\');hs=hs.replace(\'    void ResetVRHints(){\',\'    void JBTestHint(){StartMessage(cHint("HintHeaders","Hint","VRHints","13",false,cColor(1),10,false));}\\n    void ResetVRHints(){\');put(hp,hs)\n'+s[idx:]
if '--subtitle-probe' in sys.argv:
 s=s.replace('HPL3VR_PublishComfort();cScript_RunGlobalFunc("HintHandler","cScrHintHandler","JBTestHint");','HPL3VR_PublishComfort();LogNewLine("JB_VOICE_ACCEPTED "+Voice_Play("2_DatamineMaggie",-1,"",100));')
 # Native subtitle setting is independent of voice acceptance. Keep the
 # fixture override isolated rather than altering the user's configuration.
 s=s.replace("defaults=(G/'config/default_user_settings.cfg').read_text()", "defaults=(G/'config/default_user_settings.cfg').read_text().replace('ShowSubtitles=\"false\"','ShowSubtitles=\"true\"')")
exec(compile(s,str(r/'tests/test_native_input_capture.py'),'exec'))
