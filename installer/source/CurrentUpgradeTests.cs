using System;using System.IO;
public static class CurrentUpgradeTests {
 public static int Main(string[] a){try{
 string root=Path.GetFullPath(a[0]);Directory.CreateDirectory(root);Engine.Initialize();
 Engine.Install(root,a[1],"",Console.WriteLine,-1);
 File.WriteAllText(Path.Combine(root,"hpl3vr_frame_finger_rest.dat"),"personal calibration");
 Engine.Install(root,a[2],"",Console.WriteLine,-1);
 if(Engine.Load(root).Version!="1.04-S26EE")throw new Exception("Wrong version");
 if(File.ReadAllText(Path.Combine(root,"hpl3vr_frame_finger_rest.dat"))!="personal calibration")throw new Exception("Personal file changed");
 if(!File.ReadAllText(Path.Combine(root,"script/modules/MenuHandler.hps")).Contains("FINGER TRACKING"))throw new Exception("Missing toggle");
 Console.WriteLine("PASS: 1.04-S26ED to 1.04-S26EE; personal data preserved");return 0;
 }catch(Exception e){Console.WriteLine(e);return 1;}}
}

