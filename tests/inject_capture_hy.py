"""Load a test observer into the child process created by the capture harness."""
import ctypes as C
from ctypes import wintypes as W
def inject(pid,dll):
 k=C.WinDLL('kernel32',use_last_error=True)
 def sig(n,ret,args):
  f=getattr(k,n);f.restype=ret;f.argtypes=args;return f
 op=sig('OpenProcess',W.HANDLE,[W.DWORD,W.BOOL,W.DWORD])
 va=sig('VirtualAllocEx',C.c_void_p,[W.HANDLE,C.c_void_p,C.c_size_t,W.DWORD,W.DWORD])
 wr=sig('WriteProcessMemory',W.BOOL,[W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)])
 gm=sig('GetModuleHandleW',W.HMODULE,[W.LPCWSTR]);gp=sig('GetProcAddress',C.c_void_p,[W.HMODULE,C.c_char_p])
 ct=sig('CreateRemoteThread',W.HANDLE,[W.HANDLE,C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,W.DWORD,C.c_void_p])
 wait=sig('WaitForSingleObject',W.DWORD,[W.HANDLE,W.DWORD]);close=sig('CloseHandle',W.BOOL,[W.HANDLE])
 free=sig('VirtualFreeEx',W.BOOL,[W.HANDLE,C.c_void_p,C.c_size_t,W.DWORD])
 h=op(0x43a,False,pid);assert h,C.get_last_error()
 buf=C.create_unicode_buffer(str(dll));p=va(h,None,C.sizeof(buf),0x3000,4);assert p
 assert wr(h,p,buf,C.sizeof(buf),None)
 t=ct(h,None,0,gp(gm('kernel32.dll'),b'LoadLibraryW'),p,0,None);assert t
 assert wait(t,10000)==0
 free(h,p,0,0x8000);close(t);close(h)
