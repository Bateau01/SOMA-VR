#!/usr/bin/env python3
from __future__ import annotations
import hashlib, struct, sys
from pathlib import Path
EXPECTED_INPUT_SHA='f17f2048c7625705e3867c7ca9e106c3c343053deefc716e67f210ca647f74ed'
IMAGE_BASE=0x388740000
NEW_SECTION_RVA=0x7B000
NEW_SECTION_VA=IMAGE_BASE+NEW_SECTION_RVA
SECTION_NAME=b'.s6s26n'
EXT={
 'ext_OrigInit':0x388753550,
 'ext_OrigCreateInstanceAndSystem':0x388752BC0,
 'ext_OrigLoadThread':0x388752190,
 'ext_OrigBegin':0x388753750,
 'ext_Log':0x388744320,
 'ext_OrigGetHandPose':0x388741EC0,
 'ext_OrigDrawHandMesh':0x388742D40,
 'ext_OrigDrawHands':0x388751210,
 'ext_Cosf':0x3887621F0,
 'ext_Sinf':0x3887622C0,
 'ext_Sqrtf':0x388761F40,
 'ext_glIsEnabled':0x388756880,
 'ext_glDisable':0x3887568C8,
 'ext_glEnable':0x3887568B8,
 'ext_glDrawArrays':0x3887568C0,
 'ext_glGetIntegerv':0x388756890,
 'ext_glBindTexture':0x3887568F8,
 'ext_GetModuleFileNameA':0x388767CB0,
 'ext_GetAsyncKeyState':0x388767D30,
 'ext_fopen':0x388767A70,
 'ext_fread':0x388767A88,
 'ext_fwrite':0x388767AA8,
 'ext_fclose':0x388767A60,
 'ext_malloc':0x388767AC0,
 'ext_free':0x388767A90,
 'ext_GetModuleHandleA':0x388767CA8,
 'ext_GetProcAddress':0x388767C90,
 'ext_MH_CreateHook':0x388755070,
 'ext_MH_EnableHook':0x3887554E0,
 '___chkstk_ms':0x388761270,
 'ext_g_cameraObj':0x3887820C0,
 'ext_g_xrOriginSet':0x388782084,
 'ext_g_xrOrigin':0x388782088,
 'ext_g_headMode':0x388782094,
 'ext_g_playerYaw':0x388780FCC,
 'ext_g_camUp':0x38876A300,
 'ext_g_camRight':0x38876A310,
 'ext_g_camFwd':0x38876A320,
}
INIT_CALL_RVA=0xCA8B
LOAD_THREAD_LEA_RVA=0x127DD
LOAD_THREAD_OLD_RVA=0x12190
CAMERA_DETOUR_LEA_RVA=0x5157
CAMERA_DETOUR_OLD_RVA=0x6970
BEGIN_CALL_RVAS=(0xE443,0x117CB)
GET_HAND_CALL_RVAS=(0x1131D,0x11368)
DRAW_HAND_CALL_RVAS=(0x11475,0x11488)
DRAW_HANDS_CALL_RVA=0x116B2
DRAW_HANDS_OLD_RVA=0x11210
# H57.55EQ: EP's prime-blit marker never fired in hardware; alternate-eye prime
# already bypasses this capture tail. Keep this call pristine and fail closed if
# it changed. Instead intercept both exact d_Render->o_Render indirect calls to
# sample the temporary per-eye camera at the actual scene-entry boundary.
PRIME_BLIT_CALL_RVA=0x11B68
PRIME_BLIT_EXPECTED=bytes.fromhex('ff15aaf10200')
SCENE_ENTRY_CALLS={
 0x11694:bytes.fromhex('ff1546f80200'),
 0x11C56:bytes.fromhex('ff1584f20200'),
}
# H57.55EO: retire P2 diagnostic GPU timing. These are not rendering calls;
# they only timestamp/read back profiling queries and accumulated historical ms.
GPU_COLLECT_RVA=0x15A0
GPU_QUERY_COUNTER_CALLS={
 0xD388:bytes.fromhex('ff15023b0300'),
 0xD4EA:bytes.fromhex('ff15a0390300'),
 0x116E2:bytes.fromhex('ff15a8f70200'),
 0x11BFF:bytes.fromhex('ff158bf20200'),
}
SET_SCREEN_DETOUR_LEA_RVA=0x1244F
SET_SCREEN_OLD_RVA=0x43E0
LOWLEVEL_DETOUR_LEA_RVA=0x124A3
LOWLEVEL_OLD_RVA=0xA1A0
CREATE_SWAPCHAINS_CALL_RVA=0x135B7
CREATE_SWAPCHAINS_OLD_RVA=0x13210
SUBMIT_EYE_CALL_RVAS=(0xD315,0xD338,0xF6FC,0xF721)
SUBMIT_EYE_OLD_RVA=0x139F0
BANNER_OLD=b'hpl3vr S5-P2 %s %s  \x00'
BANNER_NEW=b'hpl3vr S26EC_ %s %s \x00'
KEYHELP_REPLACEMENTS=(
 (b'Keys:  F2  = engine hook (enable this first)', b'Keys:  legacy keyboard debug lockout active'),
 (b'       F10 = native stereo, side by side     F11 = swap halves', b'       Gameplay VR controls are OpenXR-controller native.'),
 (b'       F1 / F4 = IPD down / up               F8  = FOV pulse (sanity check)', b'       World scale uses hpl3vr_vr_settings.ini; all F-keys inert.        '),
 (b'       F12 = head pose sweep (full 6DOF: yaw, pitch, roll, position)', b'       Old renderer/camera/head-pose keyboard probes disabled.'),
 (b'       F6  = census every projection the engine submits (not just UI)', b'       Controller Y remains the production recenter control.'),
 (b'       F5  = physics force scan (VR hands groundwork)', b' '),
 (b"       T   = find SOMA's logic-timer step   Y = set it to 90 Hz", b' '),
 (b'       F3  = synthetic hand: held object follows a point, not your view', b' '),
 (b"       F9  = draw Simon's hand meshes in the world", b' '),
 (b'       G / H = close / open the fingers   J = curl axis   K = curl direction', b' '),
 (b'       N   = contact grip (fingers stop where they touch the object)', b' '),
 (b'       M   = rotate the view before Render vs during it (culling test)', b' '),
 (b'       V   = freeze the head pose (isolates rotation from projection)', b' '),
 (b"       ;   = HOLD the F12 sweep at its current angle   ' = creep forward", b' '),
 (b'       [ / ] = camera-level yaw test, 30 deg steps (works with F2 alone)', b' '),
 (b'       \\   = camera hook on/off (A/B against the old frustum path)', b' '),
 (b'       Q   = refresh the stale camera position the lighting reads', b' '),
 (b'       W   = apply the head pose before light setup (lighting test)', b' '),
 (b'       E   = projection substitution on/off (diagnostic, camera hook only)', b' '),
 (b'       R   = fit the render viewport to the projection (object scale)', b' '),
 (b'       X   = cycle which framebuffer the eyes are captured from', b' '),
 (b'       Z   = one eye per frame WITH post processing vs two without', b' '),
 (b'       C   = print the addresses to breakpoint (finding the camera)', b' '),
 (b'       , / . = cull margin down / up (fixes objects vanishing when you', b' '),
 (b'               look away from where the game camera points)', b' '),
 (b'       U / I = thumb axis / direction    O / [ = thumb wrap across palm', b' '),
 (b'       L / R / B = adjust left hand, right hand, or both', b' '),
 (b'       1/2 3/4 5/6 = rotate selected hand X / Y / Z   P = print values', b' '),
 (b'       7/8 = reach, 9/0 = spread, +/- = height  (numpad also works)', b' '),
 (b'       F7  = start OpenXR session (headset + runtime required)', b' '),
 (b'Retired: F1 alternating-eye (superseded by F10), F9 double-BeginRendering', b' '),
 (b'(rested on a misreading), F5/F6 (only affected F1).', b' '),
 (b'Nothing is reported until F2 installs the engine hook -- silence before', b' '),
 (b'that is expected, not a fault. A marker square should appear at once:', b' '),
 (b'  GREEN = injected and the frame hook is live', b' '),
 (b'  BLUE  = F2 on, engine hook installed', b' '),
 (b'  RED / BLUE alternating = F1 stereo (blends to purple at high fps)', b' '),
)
PERIODIC_REPORT_LOG_CALL_RVAS=(
  0xCD0C,
  0xCDF2,
  0xCE64,
  0xCF4D,
  0xCFD9,
  0xD05A,
  0xD277,
  0xD5B2,
  0xD5BE,
  0xD606,
  0xD649,
  0xD68C,
  0xD703,
  0xD791,
  0xD862,
  0xD8EB,
  0xD969,
  0xD975,
  0xD986,
  0xD9A1,
  0xD9F3,
  0xDA8D,
  0xDA95,
  0xDAAE,
  0xDACA,
  0xDADD,
  0xDAE9,
  0xDB07,
  0xDB13,
  0xDB1F,
  0xDB2B,
  0xDB37,
  0xDB43,
  0xDB8F,
  0xDBC9,
  0xDCFE,
  0xDD4D,
  0xDD65,
  0xDDEA,
  0xDE57,
  0xDE63,
  0xDE81,
  0xDED8,
  0xDF12,
  0xDFAA,
  0xDFF7,
  0xE04E,
  0xE05A,
  0xE07E,
  0xE13E,
  0xE18E,
  0xE1D2,
  0xE1DE,
  0xE230,
  0xE24F,
  0xE2A7,
  0xE2C7,
  0xE352,
  0xE480,
  0xE4D7,
  0xE513,
  0xE560,
  0xE589,
  0xE5C0,
  0xE5F8,
  0xE62D,
  0xE6FA,
  0xE78A,
  0xE7D5,
  0xE828,
  0xE860,
  0xE898,
  0xE8EB,
  0xE920,
  0xE964,
  0xE9E3,
  0xEACA,
  0xEB39,
  0xEC07,
  0xEC32,
  0xECB9,
  0xED3B,
  0xED83,
  0xEE17,
  0xEE38,
  0xEE8B,
  0xEEA2,
  0xEEAE,
  0xEEBA,
  0xEEC6,
  0xEED2,
  0xEEDE,
  0xEEEA,
  0xEEF6,
  0xEF02,
  0xEF0E,
  0xEF1A,
  0xEF26,
  0xEF32,
  0xEF3E,
  0xEF4A,
  0xEF66,
  0xEF79,
  0xEF8A,
  0xEF9B,
  0xEFAC,
  0xF05E,
  0xF08C,
  0xF202,
  0xF223,
  0xF2C3,
  0xF3F5,
  0xF4D5,
  0xF50C,
  0xF558,
  0xF59D,
  0xF5C2,
  0xF5DF,
  0xF608,
  0xF620,
  0xF646,
  0xF6A3,
  0xF74D,
  0xF7F5,
  0xF806,
  0xF88A,
  0xF8E7,
)
# H57.55DC: DA's 127-site list stopped at RVA 0xF8E7, but the same legacy
# once-per-600-frame report has three later direct Log calls plus three old-section
# tail-call trampolines. Hardware DB still emitted exactly these report lines.
PERIODIC_REPORT_TAIL_LOG_CALL_RVAS=(0xF94C,0xFE87,0x10037)
PERIODIC_REPORT_TAIL_JMP_LOG_RVAS=(0x781A5,0x781E4,0x7910C)

def sha256(b): return hashlib.sha256(b).hexdigest()
def align(v,a): return (v+a-1)&~(a-1)
def pe_checksum(data,off):
 c=0
 for i in range(0,len(data),2):
  if off<=i<off+4:w=0
  elif i+1<len(data):w=data[i]|(data[i+1]<<8)
  else:w=data[i]
  c+=w;c=(c&0xffff)+(c>>16)
 c=(c&0xffff)+(c>>16)
 return (c+len(data))&0xffffffff

def parse_pe(data):
 pe=struct.unpack_from('<I',data,0x3c)[0]
 if data[pe:pe+4]!=b'PE\0\0':raise ValueError('not PE')
 coff=pe+4;n=struct.unpack_from('<H',data,coff+2)[0];optsz=struct.unpack_from('<H',data,coff+16)[0]
 opt=coff+20;st=opt+optsz;secs=[]
 for i in range(n):
  o=st+i*40;name=data[o:o+8].rstrip(b'\0').decode('ascii','replace')
  vs,va,rs,rp=struct.unpack_from('<IIII',data,o+8);secs.append(dict(name=name,vs=vs,va=va,rs=rs,rp=rp,off=o))
 return pe,coff,opt,st,n,secs

def rva_to_file(data,rva):
 *_,secs=parse_pe(data)
 for s in secs:
  if s['va']<=rva<s['va']+max(s['vs'],s['rs']):return s['rp']+(rva-s['va'])
 pe,coff,opt,st,n,secs=parse_pe(data)
 if rva<struct.unpack_from('<I',data,opt+60)[0]:return rva
 raise ValueError(hex(rva))

def parse_coff(obj):
 machine,nsec,_,symptr,nsyms,opt,_=struct.unpack_from('<HHIIIHH',obj,0)
 if machine!=0x8664 or opt!=0:raise ValueError('unexpected COFF')
 so=symptr+nsyms*18;ss=struct.unpack_from('<I',obj,so)[0];stab=obj[so:so+ss]
 def lname(off):
  e=stab.find(b'\0',off);e=len(stab) if e<0 else e
  return stab[off:e].decode('ascii','replace')
 secs=[]
 for i in range(nsec):
  o=20+i*40;n8=obj[o:o+8]
  name=lname(int(n8[1:].rstrip(b'\0') or b'0')) if n8.startswith(b'/') else n8.rstrip(b'\0').decode('ascii','replace')
  _,_,size,rp,relp,_,nr,_,ch=struct.unpack_from('<IIIIIIHHI',obj,o+8)
  secs.append(dict(name=name,size=size,rawptr=rp,relptr=relp,nrel=nr,chars=ch,index=i+1))
 syms={};i=0
 while i<nsyms:
  o=symptr+i*18;n8=obj[o:o+8]
  name=lname(struct.unpack_from('<I',n8,4)[0]) if n8[:4]==b'\0\0\0\0' else n8.rstrip(b'\0').decode('ascii','replace')
  value,secnum,_,_,naux=struct.unpack_from('<IhHBB',obj,o+8);syms[i]=(name,value,secnum)
  for j in range(1,naux+1):syms[i+j]=('<aux>',0,0)
  i+=1+naux
 return secs,syms

def build_blob(obj):
 secs,syms=parse_coff(obj);keep=[s for s in secs if s['name'] in ('.text','.rdata','.data','.bss')]
 order={'.text':0,'.rdata':1,'.data':2,'.bss':3};keep.sort(key=lambda s:order[s['name']])
 layouts={};blob=bytearray()
 for s in keep:
  off=align(len(blob),16);blob.extend(b'\0'*(off-len(blob)));layouts[s['index']]=off
  if s['name']=='.bss' or not s['rawptr']:blob.extend(b'\0'*s['size'])
  else:blob.extend(obj[s['rawptr']:s['rawptr']+s['size']])
 resolve=dict(EXT)
 for _,(name,val,secnum) in syms.items():
  if secnum in layouts and name!='<aux>':resolve[name]=NEW_SECTION_VA+layouts[secnum]+val
 for s in keep:
  base=layouts[s['index']];sva=NEW_SECTION_VA+base
  for j in range(s['nrel']):
   ro=s['relptr']+j*10;pos,si,rt=struct.unpack_from('<IIH',obj,ro);name=syms[si][0]
   if name not in resolve:raise SystemExit('unresolved '+name)
   loc=base+pos;S=resolve[name]
   if rt==0x0004:
    A=struct.unpack_from('<i',blob,loc)[0];P=sva+pos;d=S+A-(P+4)
    if not -(1<<31)<=d<(1<<31):raise SystemExit('rel32 range')
    struct.pack_into('<i',blob,loc,d)
   else:raise SystemExit(f'ASLR-unsafe/unsupported relocation {rt:#x} for {name}')
 return blob,resolve,layouts,keep

def rel32(src,dst,opcode=0xE8):
 d=dst-(src+5)
 if not -(1<<31)<=d<(1<<31):raise ValueError('rel32 range')
 return bytes([opcode])+struct.pack('<i',d)

def lea_r8_rip(src,dst):
 # 4C 8D 05 disp32 ; RIP is address after this 7-byte instruction.
 d=dst-(src+7)
 if not -(1<<31)<=d<(1<<31):raise ValueError('riprel32 range')
 return b'\x4c\x8d\x05'+struct.pack('<i',d)

def lea_rdx_rip(src,dst):
 # 48 8D 15 disp32
 d=dst-(src+7)
 if not -(1<<31)<=d<(1<<31):raise ValueError('riprel32 range')
 return b'\x48\x8d\x15'+struct.pack('<i',d)

def main(inp,objp,outp):
 original=inp.read_bytes()
 if sha256(original)!=EXPECTED_INPUT_SHA:raise SystemExit('refusing input sha '+sha256(original))
 data=bytearray(original);pe,coff,opt,st,n,secs=parse_pe(data)
 fa=struct.unpack_from('<I',data,opt+36)[0];sa=struct.unpack_from('<I',data,opt+32)[0];hs=struct.unpack_from('<I',data,opt+60)[0]
 dirs_before=bytes(data[opt+112:opt+112+16*8])
 nh=st+n*40
 if nh+40>hs:raise SystemExit('no section header room')
 if any(data[nh:nh+40]):raise SystemExit('next section-header slot not empty')
 if any(s['va']==NEW_SECTION_RVA for s in secs):raise SystemExit('new section RVA occupied')
 blob,res,layouts,keep=build_blob(objp.read_bytes());rp=align(len(data),fa);rs=align(len(blob),fa)
 if len(data)<rp:data.extend(b'\0'*(rp-len(data)))
 data.extend(blob);data.extend(b'\0'*(rs-len(blob)))
 data[nh:nh+40]=struct.pack('<8sIIIIIIHHI',SECTION_NAME,len(blob),NEW_SECTION_RVA,rs,rp,0,0,0,0,0xE0000020)
 struct.pack_into('<H',data,coff+2,n+1)
 struct.pack_into('<I',data,opt+4,struct.unpack_from('<I',data,opt+4)[0]+rs)
 struct.pack_into('<I',data,opt+56,align(NEW_SECTION_RVA+len(blob),sa))
 # Arm family observation from P2's existing DLL-load worker, before F2/VR.
 # DllMain passes _ZL4InitPv (RVA 0x12190) as CreateThread's start routine.
 # Redirect only that LEA target to our wrapper; the wrapper calls the original worker first.
 loff=rva_to_file(data,LOAD_THREAD_LEA_RVA);lexpected=lea_r8_rip(LOAD_THREAD_LEA_RVA,LOAD_THREAD_OLD_RVA)
 if data[loff:loff+7]!=lexpected:raise SystemExit(f'unexpected load-thread LEA {data[loff:loff+7].hex()} expected {lexpected.hex()}')
 data[loff:loff+7]=lea_r8_rip(LOAD_THREAD_LEA_RVA,res['s6_h5748n_load_thread_wrapper']-IMAGE_BASE)
 # H57.53f: P2's single cCamera3D::UpdateViewMatrix MinHook remains the owner.
 # Redirect only the RIP-relative detour pointer passed to MH_CreateHook from the
 # historical Euler-add d_UpdateViewMatrix to our rigid quaternion composer.
 coff_cam=rva_to_file(data,CAMERA_DETOUR_LEA_RVA);cexpected=lea_rdx_rip(CAMERA_DETOUR_LEA_RVA,CAMERA_DETOUR_OLD_RVA)
 if data[coff_cam:coff_cam+7]!=cexpected:raise SystemExit(f'unexpected camera detour LEA {data[coff_cam:coff_cam+7].hex()} expected {cexpected.hex()}')
 data[coff_cam:coff_cam+7]=lea_rdx_rip(CAMERA_DETOUR_LEA_RVA,res['h5753h_update_view_detour']-IMAGE_BASE)
 # Redirect only the known P2 call sites. Original exported methods stay byte-identical.
 off=rva_to_file(data,INIT_CALL_RVA);expected=rel32(INIT_CALL_RVA,0x13550)
 if data[off:off+5]!=expected:raise SystemExit(f'unexpected Init call {data[off:off+5].hex()} expected {expected.hex()}')
 data[off:off+5]=rel32(INIT_CALL_RVA,res['s6_h11_init_wrapper']-IMAGE_BASE)
 for rva in BEGIN_CALL_RVAS:
  off=rva_to_file(data,rva);expected=rel32(rva,0x13750)
  if data[off:off+5]!=expected:raise SystemExit(f'unexpected Begin call at {rva:#x}: {data[off:off+5].hex()} expected {expected.hex()}')
  data[off:off+5]=rel32(rva,res['s6_h11_begin_wrapper']-IMAGE_BASE)
 # H57.50x captures the already-proven SetScreenSize self pointer by redirecting
 # only P2's MinHook detour LEA to our tiny wrapper. The wrapper calls the frozen
 # P2 d_SetScreenSize body, so its native-size override and original slot remain authoritative.
 off=rva_to_file(data,SET_SCREEN_DETOUR_LEA_RVA);expected=lea_rdx_rip(SET_SCREEN_DETOUR_LEA_RVA,SET_SCREEN_OLD_RVA)
 if data[off:off+7]!=expected:raise SystemExit(f'unexpected SetScreenSize detour LEA {data[off:off+7].hex()} expected {expected.hex()}')
 data[off:off+7]=lea_rdx_rip(SET_SCREEN_DETOUR_LEA_RVA,res['h5750x_set_screen_size_detour']-IMAGE_BASE)
 # H57.50x-r1 must seed g_nativeW/H before the frozen low-level graphics
 # detour executes, so HPL3 allocates its real deferred/offscreen targets at
 # the symmetric envelope from the start. Redirect only P2's MinHook detour LEA.
 off=rva_to_file(data,LOWLEVEL_DETOUR_LEA_RVA);expected=lea_rdx_rip(LOWLEVEL_DETOUR_LEA_RVA,LOWLEVEL_OLD_RVA)
 if data[off:off+7]!=expected:raise SystemExit(f'unexpected LowLevelInit detour LEA {data[off:off+7].hex()} expected {expected.hex()}')
 data[off:off+7]=lea_rdx_rip(LOWLEVEL_DETOUR_LEA_RVA,res['h5750xr1_lowlevel_init_detour']-IMAGE_BASE)
 # H57.51a preserves r3 dimension separation and uses runtime-authoritative single resolve at 1.00x pixel density; it separates the HPL3 native envelope from the OpenXR output size.
 # Route the single Session::Init -> CreateSwapchains direct call through a tiny
 # wrapper that temporarily intercepts xrCreateSwapchain and forces only the
 # output swapchains back to the immutable runtime-base dimensions captured
 # before LowLevelInit. The frozen CreateSwapchains body remains otherwise exact.
 off=rva_to_file(data,0x13593);expected=bytes.fromhex('e828f6ffff')
 assert data[off:off+5]==expected,'OpenXR instance call signature mismatch'
 data[off:off+5]=rel32(0x13593,res['s26q_instance_wrapper']-IMAGE_BASE)
 off=rva_to_file(data,CREATE_SWAPCHAINS_CALL_RVA);expected=rel32(CREATE_SWAPCHAINS_CALL_RVA,CREATE_SWAPCHAINS_OLD_RVA)
 if data[off:off+5]!=expected:raise SystemExit(f'unexpected CreateSwapchains call {data[off:off+5].hex()} expected {expected.hex()}')
 data[off:off+5]=rel32(CREATE_SWAPCHAINS_CALL_RVA,res['h5750xr2_create_swapchains_wrapper']-IMAGE_BASE)
 # Route every frozen direct Session::SubmitEye call through the H57.50x wrapper.
 # It calls the original method first, then expands only imageRect to the full
 # swapchain because the eye texture is already pre-cropped to the exact runtime FOV.
 for rva in SUBMIT_EYE_CALL_RVAS:
  off=rva_to_file(data,rva);expected=rel32(rva,SUBMIT_EYE_OLD_RVA)
  if data[off:off+5]!=expected:raise SystemExit(f'unexpected SubmitEye call at {rva:#x}: {data[off:off+5].hex()} expected {expected.hex()}')
  data[off:off+5]=rel32(rva,res['h5750x_submit_eye_wrapper']-IMAGE_BASE)
 # Redirect only the two DrawHands synthetic-position calls. The original
 # GetHandPose body remains untouched so F3/F5 physics is not silently changed.
 for rva in GET_HAND_CALL_RVAS:
  off=rva_to_file(data,rva);expected=rel32(rva,0x1EC0)
  if data[off:off+5]!=expected:raise SystemExit(f'unexpected GetHandPose call at {rva:#x}: {data[off:off+5].hex()} expected {expected.hex()}')
  data[off:off+5]=rel32(rva,res['s6_h11_visual_get_hand_pose']-IMAGE_BASE)
 # Likewise redirect only DrawHands' two mesh calls through a temporary-basis
 # wrapper. The original DrawHandMesh function stays byte-identical.
 for rva in DRAW_HAND_CALL_RVAS:
  off=rva_to_file(data,rva);expected=rel32(rva,0x2D40)
  if data[off:off+5]!=expected:raise SystemExit(f'unexpected DrawHandMesh call at {rva:#x}: {data[off:off+5].hex()} expected {expected.hex()}')
  data[off:off+5]=rel32(rva,res['s6_h11_visual_draw_hand_mesh']-IMAGE_BASE)
 # H57.55EN prime-lite: P2 d_Render contains exactly one original call to
 # DrawHands after its o_Render scene call. Route only that call through a tiny
 # wrapper which returns immediately during the discarded H57.50V prime and
 # otherwise tail-calls the byte-identical original DrawHands. This preserves
 # every real RIGHT/LEFT hand draw and all d_Render bookkeeping.
 off=rva_to_file(data,DRAW_HANDS_CALL_RVA);expected=rel32(DRAW_HANDS_CALL_RVA,DRAW_HANDS_OLD_RVA)
 if data[off:off+5]!=expected:raise SystemExit(f'unexpected d_Render DrawHands call {data[off:off+5].hex()} expected {expected.hex()}')
 data[off:off+5]=rel32(DRAW_HANDS_CALL_RVA,res['s6_h5755en_draw_hands_wrapper']-IMAGE_BASE)
 # H57.55EQ: restore/retain the exact pristine finished-eye blit. EP hardware
 # proved its prime-aware wrapper never fired because the discarded alternate-eye
 # path already bypasses this tail; wrapping the real-eye copy only added noise.
 poff=rva_to_file(data,PRIME_BLIT_CALL_RVA)
 if data[poff:poff+6]!=PRIME_BLIT_EXPECTED: raise SystemExit(f'unexpected pristine blit call {data[poff:poff+6].hex()} expected {PRIME_BLIT_EXPECTED.hex()}')
 # H57.55GL: GK hardware proved cFrustum+0x38 stays at the authored camera while
 # +0x158 view center follows HMD translation. Redirect both exact d_Render ->
 # o_Render slot calls to the scoped GL wrapper. It writes only +0x38/+0x3c/+0x40
 # during the real SOMA scene call and restores immediately after; the H57.50V
 # prime no-op slot remains authoritative.
 for srva,sexpected in SCENE_ENTRY_CALLS.items():
  soff=rva_to_file(data,srva)
  if data[soff:soff+6]!=sexpected: raise SystemExit(f'unexpected scene-entry call at {srva:#x}: {data[soff:soff+6].hex()} expected {sexpected.hex()}')
  data[soff:soff+6]=rel32(srva,res['s6_h5755gn_scene_entry_wrapper']-IMAGE_BASE)+b'\x90'
 # H57.55EO: remove the production GPU-timer diagnostic that EN accidentally
 # forced to reinitialize on every discarded prime. GpuCollect becomes an immediate
 # RET and every indirect glQueryCounter call is NOPed. This leaves actual scene,
 # post, capture, OpenXR and CPU pacing code untouched. Each byte is base-verified.
 goff=rva_to_file(data,GPU_COLLECT_RVA)
 if data[goff:goff+1]!=b'\x57': raise SystemExit(f'unexpected GpuCollect prologue {data[goff:goff+8].hex()}')
 data[goff:goff+1]=b'\xC3'
 for qrva,qexpected in GPU_QUERY_COUNTER_CALLS.items():
  qoff=rva_to_file(data,qrva)
  if data[qoff:qoff+len(qexpected)]!=qexpected: raise SystemExit(f'unexpected QueryCounter call at {qrva:#x}: {data[qoff:qoff+len(qexpected)].hex()} expected {qexpected.hex()}')
  data[qoff:qoff+len(qexpected)]=b'\x90'*len(qexpected)
 # H15 tracked-hand calibration defaults. These are original P2 data values, not code.
 # g_handSpread: 0.18 -> 0.20. H10 interprets (spread-0.18) as tracked-hand outward offset.
 spoff=rva_to_file(data,0x2A218)
 if data[spoff:spoff+4]!=struct.pack('<f',0.18): raise SystemExit('unexpected g_handSpread default')
 data[spoff:spoff+4]=struct.pack('<f',0.20)
 # Fine tracked-hand placement: reach/spread/height all become 1 cm per press.
 for fo,oldv,newv,label in [
   (0x31cf0,0.05,0.01,'reach'),(0x31d10,-0.05,-0.01,'reach'),
   (0x31d30,0.03,0.01,'spread'),(0x31d50,-0.03,-0.01,'spread'),
   (0x31d70,0.03,0.01,'height'),(0x31d90,-0.03,-0.01,'height')]:
  if data[fo:fo+4]!=struct.pack('<f',oldv): raise SystemExit(f'unexpected {label}-step value at {fo:#x}')
  data[fo:fo+4]=struct.pack('<f',newv)
 # Fine rotation calibration: six legacy +/- 15 degree table entries become +/- 5 degrees.
 for fo,oldv,newv in [
   (0x31dcc,0.2618,0.0872664626),(0x31de4,-0.2618,-0.0872664626),
   (0x31dfc,0.2618,0.0872664626),(0x31e14,-0.2618,-0.0872664626),
   (0x31e2c,0.2618,0.0872664626),(0x31e44,-0.2618,-0.0872664626)]:
  if data[fo:fo+4]!=struct.pack('<f',oldv): raise SystemExit(f'unexpected rotation-step value at {fo:#x}')
  data[fo:fo+4]=struct.pack('<f',newv)
 # Retire P2's old world-anchored GREEN diagnostic cube. F9 should now draw only the two hands.
 marker_rva=0x11463
 off=rva_to_file(data,marker_rva);expected=rel32(marker_rva,0x2BE0)
 if data[off:off+5]!=expected:raise SystemExit(f'unexpected green-marker call {data[off:off+5].hex()} expected {expected.hex()}')
 data[off:off+5]=b'\x90'*5
 # H57.36 retires synthetic W/A/S/D, but retain H16's already-shipped W-diagnostic
 # safety patch so this append-payload lineage changes no historical P2 bytes back.
 # Left-stick locomotion itself is now native and never emits VK_W.
 w_rva=0xB0E1
 off=rva_to_file(data,w_rva);expected=b'\xB9\x57\x00\x00\x00'
 if data[off:off+5]!=expected:raise SystemExit(f'unexpected W diagnostic poll {data[off:off+5].hex()} expected {expected.hex()}')
 data[off:off+5]=b'\xB9\x00\x00\x00\x00'
 # H57.55DB inherits DA: physically silence only the verified direct ext_Log calls in the
 # legacy once-per-600-frame P2 diagnostic report. Keep its control flow,
 # rolling-counter exchanges/resets, render/pacing state and all non-report code.
 # Every site is fail-closed against the pristine P2 base byte encoding.
 for rva in PERIODIC_REPORT_LOG_CALL_RVAS:
  off=rva_to_file(data,rva);expected=rel32(rva,EXT['ext_Log']-IMAGE_BASE)
  if data[off:off+5]!=expected:raise SystemExit(f'unexpected periodic-report Log call at {rva:#x}: {data[off:off+5].hex()} expected {expected.hex()}')
  data[off:off+5]=b'\x90'*5
 # H57.55DC finishes the proven tail of that same report. Direct calls can be
 # NOPed because the following reset/control flow is independent of Log.
 for rva in PERIODIC_REPORT_TAIL_LOG_CALL_RVAS:
  off=rva_to_file(data,rva);expected=rel32(rva,EXT['ext_Log']-IMAGE_BASE)
  if data[off:off+5]!=expected:raise SystemExit(f'unexpected periodic-report tail Log call at {rva:#x}: {data[off:off+5].hex()} expected {expected.hex()}')
  data[off:off+5]=b'\x90'*5
 # The old .s5i1/.s5p1 report helpers use `push continuation; jmp Log` rather
 # than CALL. Replace only the verified JMP with RET+NOP: RET consumes the
 # artificial continuation address, preserving the helper's counter resets and
 # exact next control-flow target without entering synchronous logging.
 for rva in PERIODIC_REPORT_TAIL_JMP_LOG_RVAS:
  off=rva_to_file(data,rva);expected=rel32(rva,EXT['ext_Log']-IMAGE_BASE,0xE9)
  if data[off:off+5]!=expected:raise SystemExit(f'unexpected periodic-report tail JMP Log at {rva:#x}: {data[off:off+5].hex()} expected {expected.hex()}')
  data[off:off+5]=b'\xC3\x90\x90\x90\x90'
 pos=data.find(BANNER_OLD)
 if pos<0 or data.find(BANNER_OLD,pos+1)>=0:raise SystemExit('unique S5-P2 marker not found')
 
 if len(BANNER_NEW)!=len(BANNER_OLD):raise SystemExit('banner replacement length mismatch')
 data[pos:pos+len(BANNER_OLD)]=BANNER_NEW
 # H57.55EC: the legacy P2 Keys() block is runtime-suppressed by a caller-
 # scoped GetAsyncKeyState hook. Replace its obsolete startup key legend too,
 # so the log cannot encourage use of retired debug hotkeys. Shorter text is
 # NUL-padded in-place; code/string RVAs remain unchanged.
 for old_s,new_s in KEYHELP_REPLACEMENTS:
  kp=data.find(old_s)
  if kp<0 or data.find(old_s,kp+1)>=0:raise SystemExit('unique legacy key-help string not found: '+repr(old_s))
  if len(new_s)>len(old_s):raise SystemExit('key-help replacement too long: '+repr(new_s))
  data[kp:kp+len(old_s)]=new_s+b'\0'*(len(old_s)-len(new_s))
 if bytes(data[opt+112:opt+112+16*8])!=dirs_before:raise SystemExit('data directories unexpectedly changed')
 co=opt+64;struct.pack_into('<I',data,co,0);cs=pe_checksum(bytes(data),co);struct.pack_into('<I',data,co,cs)
 outp.parent.mkdir(parents=True,exist_ok=True);outp.write_bytes(data)
 print('input ',len(original),sha256(original));print('output',len(data),sha256(data))
 print(f'new section RVA 0x{NEW_SECTION_RVA:x}, VSize 0x{len(blob):x}, raw 0x{rp:x}, rawsize 0x{rs:x}')
 print(f"load-time wrapper 0x{res['s6_h5748n_load_thread_wrapper']:x}")
 print(f"init wrapper 0x{res['s6_h11_init_wrapper']:x}")
 print(f"H5756U: authored Cortex trigger area + exact map focus target 0x{res['s6_h5755gn_scene_entry_wrapper']:x}")
 print(f"H5754p xrEndFrame wrapper 0x{res['h5754d_xr_end_frame']:x}")
 print(f"begin wrapper 0x{res['s6_h11_begin_wrapper']:x}")
 print(f"H5750x SetScreenSize detour 0x{res['h5750x_set_screen_size_detour']:x}")
 print(f"H5750x-r2 LowLevelInit detour 0x{res['h5750xr1_lowlevel_init_detour']:x}")
 print(f"H5750x-r3 CreateSwapchains wrapper 0x{res['h5750xr2_create_swapchains_wrapper']:x}")
 print(f"H5750x SubmitEye wrapper 0x{res['h5750x_submit_eye_wrapper']:x}")
 print(f"visual pose wrapper 0x{res['s6_h11_visual_get_hand_pose']:x}")
 print(f"visual mesh wrapper 0x{res['s6_h11_visual_draw_hand_mesh']:x}")
 print(f'checksum 0x{cs:08x}')
 for s in keep:print(f"  {s['name']} -> +0x{layouts[s['index']]:x} size 0x{s['size']:x}")
if __name__=='__main__':
 if len(sys.argv)!=4:raise SystemExit('usage: apply_s26an.py input.dll payload.o output.dll')
 main(Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]))






