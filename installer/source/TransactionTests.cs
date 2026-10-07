using System;using System.IO;using System.Linq;using System.Collections.Generic;
public static class TransactionTests {
 static Dictionary<string,string> Snapshot(string root){return Directory.GetFiles(root,"*",SearchOption.AllDirectories).ToDictionary(p=>p.Substring(root.Length),p=>Engine.Hash(p));}
 public static int Main(string[] a){try{
  Engine.Initialize();string root=Path.GetFullPath(a[0]);Directory.CreateDirectory(root);
  Engine.Install(root,a[1],"",s=>{},-1);
  File.WriteAllText(Path.Combine(root,"hpl3vr_vr_settings.ini"),"personal=keep");
  File.WriteAllText(Path.Combine(root,"save.keep"),"untouched");
  foreach(int point in new int[]{0,1,12,80}){
   var before=Snapshot(root);bool failed=false;
   try{Engine.Install(root,a[1],"",s=>{},point);}catch(IOException e){failed=e.Message.Contains("rolled back");if(!failed)Console.WriteLine(e);}
   if(!failed)throw new Exception("Missing injected rollback at "+point);
   var after=Snapshot(root);if(before.Count!=after.Count||before.Any(p=>!after.ContainsKey(p.Key)||after[p.Key]!=p.Value))throw new Exception("Rollback content differs at "+point);
  }
  bool rejected=false;try{Engine.Safe(root,"../escape");}catch(IOException){rejected=true;}
  if(!rejected)throw new Exception("Path traversal accepted");
  Console.WriteLine("PASS: four interrupted-update rollback points restore every file; path traversal rejected.");return 0;
 }catch(Exception e){Console.WriteLine(e);return 1;}}
}
