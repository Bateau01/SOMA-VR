using System;
using System.IO;
public static class ShaderCacheTests {
 public static int Main(string[] args) { try {
  Engine.Initialize();
  for(int test=0;test<3;test++) {
   string root=Path.Combine(args[1],"case"+test),directory=Path.Combine(root,"_shadersource");Directory.CreateDirectory(directory);
   foreach(string file in Directory.GetFiles(Path.Combine(args[0],"_shadersource")))File.Copy(file,Path.Combine(directory,Path.GetFileName(file)),true);
   string index=Path.Combine(directory,"shadercache.xml"),bank=Path.Combine(directory,"shadersource.hpss");
   string original=Engine.Hash(index+".soma-vr-original");
   if(test==1)File.AppendAllText(index,"\n<!-- unrelated later edit -->\n");
   if(test==2){byte[] data=File.ReadAllBytes(bank);data[0]^=1;File.WriteAllBytes(bank,data);}
   string before=Engine.Hash(index);long size=new FileInfo(bank).Length;
   Directory.CreateDirectory(Path.Combine(root,Engine.Meta));
   File.WriteAllText(Path.Combine(root,Engine.Meta,"receipt.json"),Engine.Json.Serialize(new Receipt {Root=Path.GetFullPath(root),Version="test",Build=1}));
   Engine.Remove(root,Console.WriteLine);
   if(Engine.Hash(index)!=(test==0?original:before))throw new Exception("Cache restoration/changed-file preservation failed");
   if(new FileInfo(bank).Length!=size)throw new Exception("Shader bank was truncated");
   if(test==0&&File.Exists(index+".soma-vr-receipt.json"))throw new Exception("Cache receipt was not cleaned up");
  }
  Console.WriteLine("PASS: shader cache uninstall restores exact original index; later index/bank edits preserved");return 0;
 }catch(Exception e){Console.WriteLine(e);return 1;} }
}
