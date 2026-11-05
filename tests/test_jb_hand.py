from pathlib import Path
r=Path(__file__).resolve().parents[1]
s=(r/'tests/test_native_input_capture.py').read_text()
s=s.replace("'build/cpu73' if '--movement-replay'", "'build/jb-hand' if '--movement-replay'")
needle=" if '--movement-replay' in sys.argv and (G/'cpu6_movement.bin').exists():"
s=s.replace(needle," if (G/'jb_hand_timing.bin').exists():(out/'jb_hand_timing.bin').write_bytes((G/'jb_hand_timing.bin').read_bytes())\n"+needle)
exec(compile(s,str(r/'tests/test_native_input_capture.py'),'exec'))

assert "JB_HAND_WRITE rows " in (out/"hpl3vr.log").read_text(errors="replace"), "No fresh observer write; reject stale file"
