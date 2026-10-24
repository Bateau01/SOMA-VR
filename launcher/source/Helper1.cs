using System;
using System.Runtime.InteropServices;
public static class SomaVrDisplay {
 [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
 public struct Mode {
  [MarshalAs(UnmanagedType.ByValTStr,SizeConst=32)] public string device;
  public ushort spec,driver,size,extra; public uint fields;
  public int x,y; public uint orientation,fixedOutput;
  public short color,duplex,yResolution,ttOption,collate;
  [MarshalAs(UnmanagedType.ByValTStr,SizeConst=32)] public string form;
  public ushort logPixels; public uint bits,width,height,flags,frequency;
  public uint icmMethod,icmIntent,media,dither,reserved1,reserved2,panningWidth,panningHeight;
 }
 [DllImport("user32.dll",CharSet=CharSet.Unicode)]
 public static extern bool EnumDisplaySettings(string device,int number,ref Mode mode);
}