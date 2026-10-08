using System;using System.IO;
public static class CurrentUpgradeTests {
 public static int Main(string[] a){try{
 Engine.Initialize();string root=Path.GetFullPath(a[0]);Directory.CreateDirectory(root);
 Engine.Install(root,a[1],"",Console.WriteLine,-1);
 string previousVersion=Engine.Load(root).Version;
 File.WriteAllText(Path.Combine(root,"hpl3vr_item_grips.dat"),"personal grips");
 File.WriteAllText(Path.Combine(root,"hpl3vr_frame_finger_rest.dat"),"personal calibration");
 Engine.Install(root,a[2],"",Console.WriteLine,-1);
 if(Engine.Load(root).Version!="1.06-S26FH")throw new Exception("Wrong version");
 if(File.ReadAllText(Path.Combine(root,"hpl3vr_frame_finger_rest.dat"))!="personal calibration")throw new Exception("Personal file changed");
 if(File.ReadAllText(Path.Combine(root,"hpl3vr_item_grips.dat"))!="personal grips")throw new Exception("Personal grips changed");
 if(!File.ReadAllText(Path.Combine(root,"script/modules/MenuHandler.hps")).Contains("FINGER TRACKING"))throw new Exception("Missing toggle");
 if(!File.Exists(Path.Combine(root,"hpl3vr-store.dll")))throw new Exception("Missing store runtime");
 Console.WriteLine("PASS: "+previousVersion+" to 1.06-S26FH; personal data preserved; store runtime installed");return 0;
 }catch(Exception e){Console.WriteLine(e);return 1;}}
}

