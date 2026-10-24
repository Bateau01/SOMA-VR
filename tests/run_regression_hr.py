from pathlib import Path
import subprocess,sys,json,time
r=Path(__file__).resolve().parents[1];z=sys.argv[1];exe=r'D:\SteamLibrary\steamapps\common\SOMA\Soma.exe'
cases=[('test_terminal_queue_hr.py',['--zig',z]),('test_cursor_registration_hr.py',['--zig',z]),('test_height_capture_hr.py',['--zig',z]),('test_phone_tap_hr.py',[z]),('test_point_query_hr.py',[z]),('test_accessibility_hd.py',[z]),('test_readable_contact.py',[z]),('test_button_retention_hr.py',[z]),('test_area_ray_hr.py',[z]),('test_shell_precision_hr.py',[z]),('test_hint_matrix_hr.py',[z,exe]),('test_hint_route_hr.py',[z]),('test_terminal_sweep_hr.py',[z]),('test_terminal_pointer_hr.py',[z]),('test_registered_controls_hr.py',[z]),('test_roomscale_bridge_hr.py',[z]),('test_settings_pages_hf.py',[z]),('test_native_hand_scale.py',[z]),('test_human_mesh.py',[]),('test_native_gui.py',[z,exe])]
results=[]
for name,args in cases:
 t=time.time();p=subprocess.run([sys.executable,str(r/'tests'/name),*args],cwd=r,capture_output=True,text=True)
 result={'test':name,'exit':p.returncode,'seconds':round(time.time()-t,2),'output':p.stdout+p.stderr};results.append(result)
 (r/'docs/v109-evidence/regression_batch_hr.json').write_text(json.dumps(results,indent=2));print(name,p.returncode,(p.stdout+p.stderr)[-220:],flush=True)
raise SystemExit(any(x['exit'] for x in results))
