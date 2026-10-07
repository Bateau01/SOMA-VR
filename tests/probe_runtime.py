from pathlib import Path
import ctypes as c,json
R=Path(__file__).resolve().parents[1]
class Extension(c.Structure):
 _fields_=[('type',c.c_int),('next',c.c_void_p),('name',c.c_char*128),('version',c.c_uint)]
l=c.WinDLL('D:/SteamLibrary/steamapps/common/SOMA/openxr_loader.dll')
f=l.xrEnumerateInstanceExtensionProperties
f.argtypes=[c.c_char_p,c.c_uint,c.POINTER(c.c_uint),c.POINTER(Extension)];f.restype=c.c_int
n=c.c_uint();a=f(None,0,c.byref(n),None);assert a>=0,(a,n.value)
e=(Extension*n.value)()
for x in e:x.type=2
b=f(None,n.value,c.byref(n),e);assert b>=0,b
names={x.name.decode():x.version for x in e}
r={'extensions':names,'depth':'XR_KHR_composition_layer_depth' in names,'reprojection_control':'XR_MSFT_composition_layer_reprojection' in names,'foveation':[x for x in names if 'foveat' in x]}
(R/'build/runtime_capabilities.json').write_text(json.dumps(r,indent=2))
print(json.dumps({k:v for k,v in r.items() if k!='extensions'},indent=2))
