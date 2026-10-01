using System;using System.IO;using System.Linq;
public static class UpgradeTests {
 public static int Main(string[] a){try{
 string root=Path.GetFullPath(a[0]);Directory.CreateDirectory(root);
 Engine.Initialize();Engine.Install(root,a[1],"",Console.WriteLine,-1);
 string[] retired=File.ReadAllLines(a[3]).Where(x=>x.Length>0).ToArray();
 foreach(string name in retired)if(!File.Exists(Path.Combine(root,name)))throw new Exception("Baseline missing "+name);
 Engine.Install(root,a[2],"",Console.WriteLine,-1);
 foreach(string name in retired)if(File.Exists(Path.Combine(root,name)))throw new Exception("Obsolete release notes retained: "+name);
 if(!File.Exists(Path.Combine(root,"hpl3vr_vr_settings.ini")))throw new Exception("Missing settings");
 if(Engine.Load(root).Version!="1.03-S26DF")throw new Exception("Wrong version");
 Console.WriteLine("PASS: S26DD to 1.03-S26DF removes all "+retired.Length+" unchanged managed release documents; settings remain.");
 return 0;}catch(Exception e){Console.WriteLine(e);return 1;}}
}

