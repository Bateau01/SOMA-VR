from pathlib import Path
p=Path('tests/test_native_hand_scale.py');s=p.read_text();s=s.replace('static void h10_build_rig(int h){(void)h;}','static void h10_build_rig(int h){(void)h;}\nstatic int s26hr_guide_pose(void*m){(void)m;return 0;}');p.write_text(s)
