from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'source/s26n.c';s=p.read_text()
marker='static i32 s26v_is_area(void* entity)'
assert s.count(marker)==1 and 'static float s26hr_shell_ray_gap' not in s
s=s.replace(marker,'// Distance along the normalized ray avoids world-coordinate cancellation at\n// the exact 4-cm endpoint (including native zero-distance interior hits).\nstatic float s26hr_shell_ray_gap(float dist){float gap=dist-H483_CURTAIN_RAY_M*0.5f;return gap<0.0f?-gap:gap;}\n'+marker)
a=s.index('static i32 s26v_authored_surface_shell(i32 hand,const float* handM,i32 commit){')
b=s.index('/* H57.55bk source cleanup',a)
chunk=s[a:b]
old='float dx=hit[0]-center[0],dy=hit[1]-center[1],dz=hit[2]-center[2],gap=h10_len3(dx,dy,dz);'
assert chunk.count(old)==2
chunk=chunk.replace(old,'float gap=s26hr_shell_ray_gap(dist);')
p.write_text(s[:a]+chunk+s[b:])
