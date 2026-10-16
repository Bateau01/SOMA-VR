using System;using System.IO;using System.Security.Principal;
public static class UpdaterTests {
 public static int Main(string[] args){try{
  Engine.Initialize();string root=Path.GetFullPath(args[0]),payload=args[1];Directory.CreateDirectory(root);
  Directory.CreateDirectory(Path.Combine(root,"script"));Directory.CreateDirectory(Path.Combine(root,"config"));
  File.Copy(args[2],Path.Combine(root,"Soma.exe"),true);File.WriteAllText(Path.Combine(root,"config/default_user_settings.cfg"),"fixture");
  var current=Engine.Json.Deserialize<Payload>(File.ReadAllText(Path.Combine(payload,"installer-manifest.json")));
  Engine.Install(root,payload,"Z:\\Custom Documents\\Soma\\Main",Console.WriteLine,-1);
  File.WriteAllText(Path.Combine(root,"hpl3vr_simulation_rate.txt"),"120\n");
  bool rejected=false;try{Engine.UpdateFromLauncher(root,payload,current.Build+1,Console.WriteLine);}catch(IOException){rejected=true;}if(!rejected)throw new Exception("Wrong approved build accepted");
  Engine.UpdateFromLauncher(root,payload,current.Build,Console.WriteLine);
  var options=Engine.Json.Deserialize<Options>(File.ReadAllText(Path.Combine(root,"SOMA-VR-Install-Options.json")));
  if(options.SettingsDirectory!="Z:\\Custom Documents\\Soma\\Main")throw new Exception("Profile path lost");
  if(File.ReadAllText(Path.Combine(root,"hpl3vr_simulation_rate.txt"))!="120\n")throw new Exception("Preference lost");
  if(Engine.Load(root).Build!=current.Build)throw new Exception("Receipt mismatch");
  var changes=new System.Collections.Generic.Dictionary<string,byte[]>();string marker=Path.Combine(root,"rollback-test.txt");File.WriteAllText(marker,"before");changes["rollback-test.txt"]=System.Text.Encoding.UTF8.GetBytes("after");changes["rollback-extra.txt"]=new byte[]{1};
  try{Engine.Commit(root,changes,Console.WriteLine,1);}catch(IOException){}
  if(File.ReadAllText(marker)!="before"||File.Exists(Path.Combine(root,"rollback-extra.txt")))throw new Exception("Rollback failed");
  Console.WriteLine("PASS updater install, approved-build rejection, settings preservation and rollback");return 0;
 }catch(Exception e){Console.WriteLine(e);return 1;}}
}
