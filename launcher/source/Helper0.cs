using System;
using System.Runtime.InteropServices;
using System.Text;
public static class SomaVrLaunch {
 [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
 public struct STARTUPINFO { public int cb; public string reserved,desktop,title; public int x,y,cx,cy,xc,yc,fill,flags; public short show,reserved2; public IntPtr reservedPtr,stdin,stdout,stderr; }
 [StructLayout(LayoutKind.Sequential)]
 public struct PROCESS_INFORMATION { public IntPtr process,thread; public uint pid,tid; }
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)]
 [return:MarshalAs(UnmanagedType.Bool)]
 public static extern bool CreateProcessW(string application,StringBuilder command,IntPtr pa,IntPtr ta,bool inherit,uint flags,IntPtr env,string directory,ref STARTUPINFO si,out PROCESS_INFORMATION pi);
 [DllImport("kernel32.dll",SetLastError=true)] public static extern uint ResumeThread(IntPtr thread);
 [DllImport("kernel32.dll")] public static extern bool CloseHandle(IntPtr handle);
 [DllImport("kernel32.dll")] public static extern bool TerminateProcess(IntPtr process,uint code);
}