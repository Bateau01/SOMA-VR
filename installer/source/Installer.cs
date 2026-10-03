using System;
using System.IO;
using System.IO.Compression;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Web.Script.Serialization;
using System.Windows.Forms;
using Microsoft.Win32;

public class Record { public string Path; public string Hash; public bool Original; public string OriginalHash; }
public class Receipt { public int Schema=1; public long Build; public string Version; public string Root; public List<Record> Files=new List<Record>(); }
public class Payload { public long Build; public string Version; public Dictionary<string,string> Files; }
public class Options { public string SettingsDirectory; public string OwnerSid; }

public static class Engine {
 static Engine() { AppContext.SetSwitch("Switch.System.IO.UseLegacyPathHandling",false); AppContext.SetSwitch("Switch.System.IO.BlockLongPaths",false); }
 public static void Initialize() {}
 public const string Version="2.0-S26ED";
 public const string Meta=".soma-vr-installer";
 public static JavaScriptSerializer Json=new JavaScriptSerializer();
 public static string Hash(string path) { using(var s=File.OpenRead(path)) using(var sha=SHA256.Create()) return BitConverter.ToString(sha.ComputeHash(s)).Replace("-","").ToLowerInvariant(); }
 public static string Root(string path) { return Path.GetFullPath(path).TrimEnd(Path.DirectorySeparatorChar); }
 public static string Safe(string root,string relative) {
  if(String.IsNullOrWhiteSpace(relative)||Path.IsPathRooted(relative)||relative.Contains(":")) throw new IOException("Invalid manifest path: "+relative);
  string full=Path.GetFullPath(Path.Combine(root,relative.Replace('/',Path.DirectorySeparatorChar)));
  if(!full.StartsWith(Root(root)+Path.DirectorySeparatorChar,StringComparison.OrdinalIgnoreCase)) throw new IOException("Path escapes installation: "+relative);
  string cursor=full;
  while(!String.IsNullOrEmpty(cursor)) {
   if((File.Exists(cursor)||Directory.Exists(cursor)) && (File.GetAttributes(cursor)&FileAttributes.ReparsePoint)!=0) throw new IOException("Linked folders/files are not supported by this test installer: "+cursor);
   cursor=Path.GetDirectoryName(cursor);
  }
  return full;
 }
 public static void Atomic(string destination,byte[] data) {
  Directory.CreateDirectory(Path.GetDirectoryName(destination));
  string temp=Path.Combine(Path.GetDirectoryName(destination),"svr-"+Guid.NewGuid().ToString("N")+".tmp");
  try { File.WriteAllBytes(temp,data); if(File.Exists(destination)) File.Replace(temp,destination,null); else File.Move(temp,destination); }
  finally { if(File.Exists(temp)) File.Delete(temp); }
 }
 public static bool Personal(string p) { return p.Equals("hpl3vr_vr_settings.ini",StringComparison.OrdinalIgnoreCase)||p.Equals("hpl3vr_hand_calibration.ini",StringComparison.OrdinalIgnoreCase); }
 public static Receipt Load(string root) {
  string path=Safe(root,Meta+"/receipt.json");
  if(!File.Exists(path)) return null;
  Receipt r=Json.Deserialize<Receipt>(File.ReadAllText(path));
  if(r==null||r.Schema!=1||!String.Equals(Root(r.Root),Root(root),StringComparison.OrdinalIgnoreCase)) throw new IOException("Installer receipt belongs to another location or format. Keep its backup folder and use the original location.");
  var seen=new HashSet<string>(StringComparer.OrdinalIgnoreCase);
  foreach(var f in r.Files) {Safe(root,f.Path); if(!seen.Add(f.Path)||f.Path.StartsWith(Meta+"/",StringComparison.OrdinalIgnoreCase)) throw new IOException("Invalid receipt entry.");}
  return r;
 }
 public static void ValidateGame(string root) {
  string exe=Safe(root,"Soma.exe");
  if(!File.Exists(exe)||!Directory.Exists(Safe(root,"script"))||!File.Exists(Safe(root,"config/default_user_settings.cfg"))) throw new IOException("Select the SOMA game folder containing Soma.exe, script and config. This is not a standalone game installer.");
  if(Hash(exe)!="7c424e6055dda5b3aa41d4b3a9d6ffdebb8f4b50fa8a38769dee82d080b79113") throw new IOException("This test installer supports the verified S26CM Steam executable only. Detecting a GOG/Epic folder does not establish executable compatibility. No files were installed.");
  EnsureClosed();
 }
 public static void EnsureClosed() {if(System.Diagnostics.Process.GetProcessesByName("Soma").Length>0||System.Diagnostics.Process.GetProcessesByName("Soma_NoSteam").Length>0) throw new IOException("Close SOMA before installing or removing the mod. The installer will not stop your game.");}
 // Back up every affected file before writing anything. Retain the transaction if rollback fails.
 public static void Commit(string root, Dictionary<string,byte[]> changes,Action<string> log,int failAfter) {
  string meta=Safe(root,Meta); Directory.CreateDirectory(meta);
  string pending=Path.Combine(meta,"pending-transaction");
  if(Directory.Exists(pending)) throw new IOException("An interrupted transaction needs recovery. Use Recover interrupted install before continuing.");
  Directory.CreateDirectory(pending);
  var before=new Dictionary<string,bool>(StringComparer.OrdinalIgnoreCase);
  try {
   foreach(var c in changes) {string dest=Safe(root,c.Key); bool exists=File.Exists(dest); before.Add(c.Key,exists); if(exists) {string backup=Safe(pending,c.Key); Directory.CreateDirectory(Path.GetDirectoryName(backup)); File.Copy(dest,backup);}}
   File.WriteAllText(Path.Combine(pending,"transaction.json"),Json.Serialize(before));
  } catch(Exception e) { // No destination has been changed yet. Keep evidence for diagnosis.
   throw new IOException("Cannot stage backups. No destination files changed. Backup staging: "+pending+". Cause: "+e.Message,e);
  }
  try {
   int n=0;
   foreach(var c in changes) {
    if(failAfter>=0 && n++==failAfter) throw new IOException("Injected transaction failure for tests.");
    string dest=Safe(root,c.Key);
    if(c.Value==null) { if(File.Exists(dest)) File.Delete(dest); } else Atomic(dest,c.Value);
   }
   // Mark completion before cleanup so recovery never undoes a committed transaction.
   File.WriteAllText(Path.Combine(pending,"committed"),"1");
   try { CleanupTransaction(pending); } catch(Exception e) {log("Completed; temporary transaction cleanup deferred: "+e.Message);}
  } catch(Exception original) {
   try { Recover(root,log); } catch(Exception recovery) {throw new IOException(original.Message+" Rollback incomplete: "+recovery.Message+". Preserve "+pending);}
   throw new IOException("Installation was rolled back: "+original.Message,original);
  }
 }
 static void CleanupTransaction(string pending) {
  // pending is validated by Safe before this method; reject links before recursive cleanup.
  foreach(string p in Directory.GetFileSystemEntries(pending,"*",SearchOption.AllDirectories)) if((File.GetAttributes(p)&FileAttributes.ReparsePoint)!=0) throw new IOException("Unexpected link in transaction.");
  Directory.Delete(pending,true);
 }
 public static void Recover(string root,Action<string> log) {
  string pending=Safe(root,Meta+"/pending-transaction");
  if(!Directory.Exists(pending)) {log("No interrupted transaction.");return;}
  if(File.Exists(Path.Combine(pending,"committed"))) {CleanupTransaction(pending);return;}
  string journal=Path.Combine(pending,"transaction.json");
  if(!File.Exists(journal)) {CleanupTransaction(pending); log("Removed incomplete backup staging; destination files were not changed.");return;}
  var before=Json.Deserialize<Dictionary<string,bool>>(File.ReadAllText(journal));
  foreach(var f in before) {
   string dest=Safe(root,f.Key);
   if(f.Value) Atomic(dest,File.ReadAllBytes(Safe(pending,f.Key)));
   else if(File.Exists(dest)) File.Delete(dest);
  }
  CleanupTransaction(pending); log("Restored the pre-transaction files.");
 }
 public static void Install(string root,string source,string settingsFolder,Action<string> log,int failAfter) {
  root=Root(root); Safe(root,Meta+"/receipt.json");
  Payload manifest=Json.Deserialize<Payload>(File.ReadAllText(Path.Combine(source,"installer-manifest.json")));
  var names=new HashSet<string>(StringComparer.OrdinalIgnoreCase);
  foreach(var f in manifest.Files) {
   if(!names.Add(f.Key)||f.Key.StartsWith(Meta+"/",StringComparison.OrdinalIgnoreCase)) throw new IOException("Invalid payload manifest.");
   if(Hash(Safe(source,f.Key))!=f.Value) throw new IOException("Payload checksum mismatch: "+f.Key);
   Safe(root,f.Key);
  }
  Receipt previous=Load(root);
  if(previous!=null && previous.Build>manifest.Build) throw new IOException("A newer installer-managed build is present. Downgrading is blocked; use the newer installer.");
  var records=previous==null?new List<Record>():previous.Files;
  var map=records.ToDictionary(x=>x.Path,StringComparer.OrdinalIgnoreCase);
  var changes=new Dictionary<string,byte[]>(StringComparer.OrdinalIgnoreCase);
  var next=new Receipt {Version=manifest.Version,Build=manifest.Build,Root=root};
  foreach(var f in manifest.Files) {
   string dest=Safe(root,f.Key); Record rec;
   if(!map.TryGetValue(f.Key,out rec)) {
    rec=new Record {Path=f.Key,Original=File.Exists(dest)};
    if(rec.Original) {rec.OriginalHash=Hash(dest); changes.Add(Meta+"/original/"+f.Key,File.ReadAllBytes(dest));}
   }
   if(Personal(f.Key)&&File.Exists(dest)) {rec.Hash=Hash(dest);log("Preserved preferences: "+f.Key);}
   else {
    if(map.ContainsKey(f.Key)&&File.Exists(dest)&&Hash(dest)!=rec.Hash) {
     string saved=Meta+"/modified/"+DateTime.UtcNow.ToString("yyyyMMddTHHmmss")+"-"+Guid.NewGuid().ToString("N")+"/"+f.Key;
     changes.Add(saved,File.ReadAllBytes(dest));log("Backing up modified managed file: "+saved);
    }
    changes.Add(f.Key,File.ReadAllBytes(Safe(source,f.Key)));rec.Hash=f.Value;
   }
   next.Files.Add(rec);
  }
  foreach(var old in records.Where(x=>!names.Contains(x.Path))) {
   string dest=Safe(root,old.Path);
   if(Personal(old.Path)||(File.Exists(dest)&&Hash(dest)!=old.Hash)) {next.Files.Add(old);log("Retained modified obsolete file: "+old.Path);continue;}
   changes[old.Path]=Original(root,old);
  }
  var options=new Options {SettingsDirectory=settingsFolder??"",OwnerSid=WindowsIdentity.GetCurrent().User.Value};
  changes["SOMA-VR-Install-Options.json"]=Encoding.UTF8.GetBytes(Json.Serialize(options));
  changes[Meta+"/receipt.json"]=Encoding.UTF8.GetBytes(Json.Serialize(next));
  Commit(root,changes,log,failAfter);
  log("Installed "+manifest.Version+". Game executable, saves and Documents settings were not modified by installation.");
 }
 static byte[] Original(string root,Record r) {
  if(!r.Original) return null;
  string backup=Safe(root,Meta+"/original/"+r.Path);
  if(!File.Exists(backup)||Hash(backup)!=r.OriginalHash) throw new IOException("Original backup missing or damaged: "+r.Path);
  return File.ReadAllBytes(backup);
 }
 public static void Remove(string root,Action<string> log) {
  var r=Load(root); if(r==null) throw new IOException("No installer-managed installation at this location.");
  var changes=new Dictionary<string,byte[]>(StringComparer.OrdinalIgnoreCase);
  var keep=new Receipt {Root=Root(root),Build=r.Build,Version=r.Version+" (remaining modified files)"};
  foreach(var f in r.Files) {
   string dest=Safe(root,f.Path);
   if(Personal(f.Path)) {log("Preserved personal settings: "+f.Path);continue;}
   if(File.Exists(dest)&&Hash(dest)!=f.Hash) {keep.Files.Add(f);log("Preserved modified file and its backup: "+f.Path);continue;}
   changes[f.Path]=Original(root,f);
  }
  changes[Meta+"/receipt.json"]=keep.Files.Count==0?null:Encoding.UTF8.GetBytes(Json.Serialize(keep));
  Commit(root,changes,log,-1);
  log("Removed unchanged managed files and restored pre-installer originals. Preferences, saves and original backups retained. For a prior manual mod installation, this restores that manual installation, not vanilla SOMA.");
 }
 public static List<string> Discover() {
  var result=new List<string>(); var libraries=new List<string>();
  Action<string> add=p=> {try {if(!String.IsNullOrEmpty(p)&&File.Exists(Path.Combine(p,"Soma.exe"))&&!result.Contains(Root(p))) result.Add(Root(p));}catch{}};
  add(AppDomain.CurrentDomain.BaseDirectory);
  using(var key=Registry.CurrentUser.OpenSubKey("Software\\Valve\\Steam")) if(key!=null) libraries.Add(Convert.ToString(key.GetValue("SteamPath")));
  using(var key=Registry.LocalMachine.OpenSubKey("SOFTWARE\\WOW6432Node\\Valve\\Steam")) if(key!=null) libraries.Add(Convert.ToString(key.GetValue("InstallPath")));
  foreach(var lib in libraries.ToArray()) {
   try {string vdf=Path.Combine(lib,"steamapps","libraryfolders.vdf"); if(File.Exists(vdf)) foreach(Match m in Regex.Matches(File.ReadAllText(vdf),"\"path\"\\s*\"([^\"]+)\"")) libraries.Add(m.Groups[1].Value.Replace("\\\\","\\"));}catch{}
  }
  foreach(string lib in libraries.Where(x=>!String.IsNullOrEmpty(x)).Distinct()) {
   add(Path.Combine(lib,"steamapps","common","SOMA"));
   try {string acf=Path.Combine(lib,"steamapps","appmanifest_282140.acf"); if(File.Exists(acf)) {var m=Regex.Match(File.ReadAllText(acf),"\"installdir\"\\s*\"([^\"]+)\""); if(m.Success) add(Path.Combine(lib,"steamapps","common",m.Groups[1].Value));}}catch{}
  }
  foreach(var hive in new[]{Registry.LocalMachine,Registry.CurrentUser}) foreach(var keyName in new[]{"SOFTWARE\\GOG.com\\Games","SOFTWARE\\WOW6432Node\\GOG.com\\Games"}) {
   using(var k=hive.OpenSubKey(keyName)) if(k!=null) foreach(string id in k.GetSubKeyNames()) using(var game=k.OpenSubKey(id)) if(game!=null&&Convert.ToString(game.GetValue("gameName")).IndexOf("SOMA",StringComparison.OrdinalIgnoreCase)>=0) add(Convert.ToString(game.GetValue("path")));
  }
  try {string epic=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData),"Epic","EpicGamesLauncher","Data","Manifests");if(Directory.Exists(epic))foreach(string file in Directory.GetFiles(epic,"*.item")){var d=Json.Deserialize<Dictionary<string,object>>(File.ReadAllText(file));if(d.ContainsKey("InstallLocation"))add(Convert.ToString(d["InstallLocation"]));}}catch{}
  using(var k=Registry.CurrentUser.OpenSubKey("Software\\Bateau\\SOMA-VR-Installer")) if(k!=null) add(Convert.ToString(k.GetValue("LastGameDirectory")));
  return result;
 }
}

public class SetupWindow:Form {
 ComboBox game=new ComboBox(); TextBox profile=new TextBox(); TextBox log=new TextBox(); Button install=new Button(); Button remove=new Button(); Button recover=new Button(); string source;
 void Say(string s){log.AppendText(s+Environment.NewLine);}

 System.Drawing.Color ink=System.Drawing.Color.FromArgb(215,229,229);
 System.Drawing.Color muted=System.Drawing.Color.FromArgb(139,167,171);
 System.Drawing.Color accent=System.Drawing.Color.FromArgb(92,183,190);
 System.Drawing.Image Art(string name) {
  var stream=System.Reflection.Assembly.GetExecutingAssembly().GetManifestResourceStream(name+".png");
  if(stream!=null) {using(stream)using(var image=System.Drawing.Image.FromStream(stream))return new System.Drawing.Bitmap(image);}
  string path=Path.Combine(Path.GetDirectoryName(source),"art",name+".png");
  if(File.Exists(path)) {using(var image=System.Drawing.Image.FromFile(path))return new System.Drawing.Bitmap(image);}
  return null;
 }
 Label Caption(string text,int x,int y,int width,int height,float size,System.Drawing.Color color) {
  var l=new Label {Text=text,Left=x,Top=y,Width=width,Height=height,ForeColor=color,BackColor=System.Drawing.Color.Transparent,Font=new System.Drawing.Font("Segoe UI",size)};Controls.Add(l);return l;
 }
 void StyleButton(Button b,bool primary) {
  b.FlatStyle=FlatStyle.Flat;b.FlatAppearance.BorderColor=primary?accent:System.Drawing.Color.FromArgb(50,77,83);
  b.FlatAppearance.MouseOverBackColor=System.Drawing.Color.FromArgb(35,76,83);b.FlatAppearance.MouseDownBackColor=System.Drawing.Color.FromArgb(48,91,99);
  b.BackColor=primary?System.Drawing.Color.FromArgb(25,67,74):System.Drawing.Color.FromArgb(13,28,34);b.ForeColor=ink;b.Font=new System.Drawing.Font("Segoe UI",10);b.UseVisualStyleBackColor=false;
 }
 Button Browse(Control target,int y){var b=new Button {Text="BROWSE",Left=895,Top=y,Width=105,Height=33};StyleButton(b,false);b.Click+=(s,e)=>{using(var d=new FolderBrowserDialog()){d.Description="Select the folder";d.SelectedPath=target.Text;if(d.ShowDialog()==DialogResult.OK)target.Text=d.SelectedPath;}};Controls.Add(b);return b;}
 public SetupWindow(string payload) {
  source=payload;Text="SOMA VR | 2.0-S26ED"; Icon=System.Drawing.Icon.ExtractAssociatedIcon(Application.ExecutablePath);AutoScaleMode=AutoScaleMode.Dpi;ClientSize=new System.Drawing.Size(1032,690);MinimumSize=new System.Drawing.Size(700,500);MaximizeBox=true;StartPosition=FormStartPosition.CenterScreen;AutoScroll=true;
  BackColor=System.Drawing.Color.FromArgb(8,18,23);ForeColor=ink;Font=new System.Drawing.Font("Segoe UI",10);DoubleBuffered=true;
  var artwork=Art("background");var title=Art("title");
  Paint+=(s,e)=>{
   var g=e.Graphics;var saved=g.Save();g.TranslateTransform(AutoScrollPosition.X,AutoScrollPosition.Y);
   g.ScaleTransform(layoutDpi,layoutDpi);g.InterpolationMode=System.Drawing.Drawing2D.InterpolationMode.HighQualityBicubic;
   // Cover the entire sidebar without distorting the original artwork.
   if(artwork!=null) {
    float scale=Math.Max(sidebarWidth/680f,layoutHeight/1080f);
    float sw=sidebarWidth/scale,sh=layoutHeight/scale;
    g.DrawImage(artwork,new System.Drawing.RectangleF(0,0,sidebarWidth,layoutHeight),new System.Drawing.RectangleF(1040+(680-sw)/2,(1080-sh)/2,sw,sh),System.Drawing.GraphicsUnit.Pixel);
   }
   using(var shade=new System.Drawing.Drawing2D.LinearGradientBrush(new System.Drawing.RectangleF(0,0,sidebarWidth,layoutHeight),System.Drawing.Color.FromArgb(40,0,10,14),System.Drawing.Color.FromArgb(230,0,8,13),90))g.FillRectangle(shade,0,0,sidebarWidth,layoutHeight);
   using(var pen=new System.Drawing.Pen(System.Drawing.Color.FromArgb(41,72,79)))g.DrawLine(pen,sidebarWidth,0,sidebarWidth,layoutHeight);
   if(title!=null)g.DrawImage(title,new System.Drawing.RectangleF((sidebarWidth-260)/2,38,260,72),new System.Drawing.RectangleF(0,35,787,219),System.Drawing.GraphicsUnit.Pixel);
   using(var pen=new System.Drawing.Pen(System.Drawing.Color.FromArgb(35,60,67))) {g.DrawLine(pen,sidebarWidth+35,132,layoutWidth-32,132);g.DrawLine(pen,sidebarWidth+35,415,layoutWidth-32,415);}g.Restore(saved);
  };
  FormClosed+=(s,e)=>{if(artwork!=null)artwork.Dispose();if(title!=null)title.Dispose();};
  // Artwork is painted by the form; transparent labels preserve the source image.
  Caption("V R   M O D",0,120,320,30,17,ink).TextAlign=System.Drawing.ContentAlignment.MiddleCenter;
  Caption("INSTALLATION / MAINTENANCE",0,159,320,35,9,muted).TextAlign=System.Drawing.ContentAlignment.MiddleCenter;

  Caption("2.0-S26ED",0,568,320,28,10,muted).TextAlign=System.Drawing.ContentAlignment.MiddleCenter;
  Caption("SOMA VR Mod created by Bateau1\nUNOFFICIAL COMMUNITY MOD\nSOMA artwork © Frictional Games",0,611,320,60,8,muted).TextAlign=System.Drawing.ContentAlignment.MiddleCenter;
  Caption("SOMA VR SETUP",355,31,600,40,24,ink);
  Caption("Install, update or repair your VR installation.",357,80,610,28,11,muted);
  Caption("01    GAME LOCATION",355,154,620,25,10,accent);
  game.SetBounds(355,185,525,33);game.DropDownStyle=ComboBoxStyle.DropDown;game.FlatStyle=FlatStyle.Flat;game.BackColor=System.Drawing.Color.FromArgb(17,35,42);game.ForeColor=ink;Controls.Add(game);Browse(game,181);
  foreach(string p in Engine.Discover())game.Items.Add(p);if(game.Items.Count>0)game.SelectedIndex=0;
  Caption("Select your SOMA folder. Existing personal settings are kept.",355,227,645,24,9,muted);
  Caption("02    USER CONFIGURATION",355,273,640,24,10,accent);
  profile.SetBounds(355,304,525,30);profile.BorderStyle=BorderStyle.FixedSingle;profile.BackColor=System.Drawing.Color.FromArgb(17,35,42);profile.ForeColor=ink;Controls.Add(profile);Browse(profile,300);
  string docs=Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments);
  Caption("Leave blank to use Windows Documents automatically.",355,345,645,22,9,muted);
  var detected=Caption("Detected: "+Path.Combine(docs,"My Games","Soma","Main"),355,369,645,36,8,muted);detected.AutoEllipsis=true;
  install.Text="INSTALL / UPDATE / REPAIR";install.SetBounds(355,436,645,43);StyleButton(install,true);
  remove.Text="UNINSTALL";remove.SetBounds(355,491,235,33);StyleButton(remove,false);
  recover.Text="RECOVER INTERRUPTED INSTALL";recover.SetBounds(603,491,397,33);StyleButton(recover,false);
  Controls.AddRange(new Control[]{install,remove,recover});
  Caption("ACTIVITY",355,548,630,20,9,accent);
  log.SetBounds(355,575,645,83);log.Multiline=true;log.ReadOnly=true;log.ScrollBars=ScrollBars.Vertical;log.BorderStyle=BorderStyle.None;log.BackColor=System.Drawing.Color.FromArgb(8,18,23);log.ForeColor=muted;log.Font=new System.Drawing.Font("Segoe UI",9);Controls.Add(log);
  game.TextChanged+=(s,e)=>ReadSelection();ReadSelection();
  install.Click+=(s,e)=>Work(false,false);remove.Click+=(s,e)=>Work(true,false);recover.Click+=(s,e)=>Work(false,true);
  foreach(Control c in Controls) layoutBounds[c]=c.Bounds;
  Resize+=(s,e)=>{ArrangeWindow();if(IsHandleCreated&&!resizeQueued){resizeQueued=true;BeginInvoke((MethodInvoker)delegate{resizeQueued=false;if(!IsDisposed)ArrangeWindow();});}};Scroll+=(s,e)=>Invalidate();
  Say("Ready. Files change only when you select an action. Saves are preserved.");Shown+=(s,e)=>{var area=Screen.FromControl(this).WorkingArea;Size=new System.Drawing.Size(Math.Min(Width,area.Width-20),Math.Min(Height,area.Height-20));ArrangeWindow();};
 }
 // Keep readable minimum content, with scrolling on smaller displays. Extra space
 // expands the artwork, fields, buttons and activity area rather than stretching text.
 Dictionary<Control,System.Drawing.Rectangle> layoutBounds=new Dictionary<Control,System.Drawing.Rectangle>();
 float layoutDpi=1,layoutWidth=1032,layoutHeight=690,sidebarWidth=320;
 bool arranging,resizeQueued;
 void ArrangeWindow() {
  if(arranging||layoutBounds.Count==0||!IsHandleCreated)return;
  arranging=true;SuspendLayout();
  try {
   using(var g=CreateGraphics())layoutDpi=g.DpiX/96f;
   AutoScrollMinSize=new System.Drawing.Size((int)(1032*layoutDpi),(int)(690*layoutDpi));
   layoutWidth=Math.Max(1032,ClientSize.Width/layoutDpi);layoutHeight=Math.Max(690,ClientSize.Height/layoutDpi);
   sidebarWidth=320+(layoutWidth-1032)*0.31f;
   float dx=sidebarWidth-320,extra=layoutWidth-1032-dx,dy=layoutHeight-690;
   var offset=AutoScrollPosition;
   foreach(var pair in layoutBounds) {
    var c=pair.Key;var r=pair.Value;float x=r.X,y=r.Y,w=r.Width,h=r.Height;
    if(r.X<320) {x=0;w=sidebarWidth;if(r.Y>=568)y+=dy;}
    else {
     x+=dx;
     if(c is Button && c.Text=="BROWSE")x+=extra;
     else if(c==remove)w+=extra*0.365f;
     else if(c==recover){x+=extra*0.365f;w+=extra*0.635f;}
     else w+=extra;
     if(c==log)h+=dy;
    }
    c.SetBounds((int)Math.Round(x*layoutDpi)+offset.X,(int)Math.Round(y*layoutDpi)+offset.Y,(int)Math.Round(w*layoutDpi),(int)Math.Round(h*layoutDpi));
   }
  } finally {ResumeLayout(false);arranging=false;Invalidate(true);}
 }
 void ReadSelection() {
  try {
   var receipt=Engine.Load(game.Text);Say(receipt==null?"No managed installation detected. Manual installs will be backed up.":"Installed: "+receipt.Version);
   string optionPath=Engine.Safe(game.Text,"SOMA-VR-Install-Options.json");
   profile.Text="";
   if(File.Exists(optionPath)) {var o=Engine.Json.Deserialize<Options>(File.ReadAllText(optionPath));if(o.OwnerSid==WindowsIdentity.GetCurrent().User.Value)profile.Text=o.SettingsDirectory;}
  }catch{}
 }
 void Work(bool uninstall,bool recovery) {
  install.Enabled=remove.Enabled=recover.Enabled=false;Cursor=Cursors.WaitCursor;
  try {
   string root=Engine.Root(game.Text);
   if(uninstall||recovery)Engine.EnsureClosed();else Engine.ValidateGame(root);
   if(!uninstall&&!recovery&&!String.IsNullOrWhiteSpace(profile.Text)&&!Directory.Exists(profile.Text))throw new IOException("The selected user config folder does not exist. Leave blank for automatic lookup or select an existing folder.");
   if(uninstall) {if(MessageBox.Show("Restore backed-up pre-installer files? Saves and personal settings will be kept.","Uninstall",MessageBoxButtons.YesNo)!=DialogResult.Yes)return;Engine.Remove(root,Say);}
   else if(recovery) Engine.Recover(root,Say);
   else {Engine.Install(root,source,profile.Text.Trim(),Say,-1);using(var k=Registry.CurrentUser.CreateSubKey("Software\\Bateau\\SOMA-VR-Installer"))k.SetValue("LastGameDirectory",root);Say("Start the game using Launch-SOMA-VR.cmd in the game folder.");MessageBox.Show(this,"The SOMA VR mod was successfully installed / updated.\n\nLocation: " + root + "\n\nStart VR using Launch-SOMA-VR.cmd in that folder.","SOMA VR - Installation complete",MessageBoxButtons.OK,MessageBoxIcon.Information);}
  } catch(Exception ex) {Say("ERROR: "+ex.Message);Say("Log details: "+ex.GetType().FullName+"; HRESULT "+ex.HResult);Say("For access errors, check folder permissions and Windows Security Protection history. Do not disable protection. Protected game folders may require running this installer as administrator; the game launcher should run normally.");}
  finally {Cursor=Cursors.Default;install.Enabled=remove.Enabled=recover.Enabled=true;try{string dir=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"SOMA-VR-Installer","Logs");Directory.CreateDirectory(dir);string p=Path.Combine(dir,DateTime.Now.ToString("yyyyMMdd-HHmmss")+".log");File.WriteAllText(p,log.Text);Say("Log: "+p);}catch{}}
 }
}

public static class Program {
 [STAThread] public static void Main(string[] args) {
  Engine.Initialize();Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);
  string stage=Path.Combine(Path.GetTempPath(),"SOMA-VR-Setup-"+Guid.NewGuid().ToString("N"));
  try {
   Directory.CreateDirectory(stage);
   using(var stream=System.Reflection.Assembly.GetExecutingAssembly().GetManifestResourceStream("payload.zip")) using(var zip=new ZipArchive(stream,ZipArchiveMode.Read)) {
    foreach(var entry in zip.Entries) {if(String.IsNullOrEmpty(entry.Name))continue;string dest=Engine.Safe(stage,entry.FullName);Directory.CreateDirectory(Path.GetDirectoryName(dest));using(var input=entry.Open())using(var output=File.Create(dest))input.CopyTo(output);}
   }
   Application.Run(new SetupWindow(stage));
  } catch(Exception ex) {MessageBox.Show(ex.Message,"SOMA VR setup could not start");}
  finally {try {if(Directory.Exists(stage))Directory.Delete(stage,true);}catch{}}
 }
}





