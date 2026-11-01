using System;
using System.IO;
using System.Linq;
public static class FullTests {
 public static int Main(string[] args) {try { Engine.Initialize();
  string root=Path.GetFullPath(args[0]),payload=Path.GetFullPath(args[1]);Directory.CreateDirectory(root);
  string personal=Path.Combine(root,"hpl3vr_vr_settings.ini");File.WriteAllText(personal,"body_slot_debug_visual=0\ncustom_player_setting=keep\n");
  string unrelated=Path.Combine(root,"player-save.keep");File.WriteAllText(unrelated,"SAVE");
  Engine.Install(root,payload,"",Console.WriteLine,-1);
  var receipt=Engine.Load(root);
  foreach(var f in receipt.Files) if(!Engine.Personal(f.Path)&&Engine.Hash(Engine.Safe(root,f.Path))!=f.Hash)throw new Exception("Bad installed hash: "+f.Path);
  Console.WriteLine("PASS: all "+receipt.Files.Count+" installed payload files verified.");
  Engine.Install(root,payload,"",Console.WriteLine,-1);
  if(!File.ReadAllText(personal).Contains("custom_player_setting=keep"))throw new Exception("Personal preferences lost");
  Console.WriteLine("PASS: full-payload repeat update preserves preferences.");
  Engine.Remove(root,Console.WriteLine);
  if(File.Exists(Path.Combine(root,"hpl3vr.dll"))||!File.Exists(unrelated)||!File.Exists(personal))throw new Exception("Uninstall mismatch");
  Console.WriteLine("PASS: full-payload uninstall removes mod DLL and retains unrelated data and preferences.");return 0;
 }catch(Exception ex){Console.WriteLine(ex);return 1;}}
}

