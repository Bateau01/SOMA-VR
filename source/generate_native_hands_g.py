"""Create native skinned COLLADA meshes from installed HND5 assets, without editing them."""
from pathlib import Path
import struct,subprocess,json,hashlib,xml.etree.ElementTree as E
import numpy as np
R=Path(__file__).resolve().parents[1];GAME=Path(r'/PATH/TO/SOMA')
OUT=R/'runtime/entities/soma_vr/s26f';OUT.mkdir(parents=True,exist_ok=True)
NS='http://www.collada.org/2005/11/COLLADASchema';E.register_namespace('',NS)
def el(p,t,attrs=None,text=None):
    q=E.SubElement(p,'{'+NS+'}'+t,attrs or {})
    if text is not None:q.text=text
    return q
def nums(a):return ' '.join(format(float(x),'.9g') for x in np.asarray(a).flat)
def source(p,id,a,stride,params,kind='float'):
    src=el(p,'source',{'id':id}); values=list(a) if kind=='Name' else np.asarray(a).flatten().tolist()
    el(src,kind+'_array',{'id':id+'-array','count':str(len(values))},' '.join(values) if kind=='Name' else nums(values))
    ac=el(el(src,'technique_common'),'accessor',{'source':'#'+id+'-array','count':str(len(values)//stride),'stride':str(stride)})
    for name,type in params:el(ac,'param',{'name':name,'type':type})
def material(root,name,cap=False):
    m=E.parse(GAME/'entities/character/player/hands'/f'{name}.mat').getroot() if not cap else E.fromstring('<Material><Main DepthTest="true" Type="SolidDiffuse" PhysicsMaterial="Default"/><TextureUnits><Diffuse File="entities/soma_vr/s26f/wrist_cap.dds" Type="2D" MipMaps="false" Wrap="Repeat"/></TextureUnits></Material>')
    for tex in m.findall('./TextureUnits/*'):
        f=tex.get('File','')
        if f and '/' not in f and '\\' not in f:tex.set('File','entities/character/player/hands/'+f)
    E.ElementTree(m).write(OUT/(name+'.mat'),encoding='utf-8',xml_declaration=True)
    el(root.find('{'+NS+'}library_images'),'image',{'id':name+'-image'},None)
    im=root.find('{'+NS+'}library_images')[-1];el(im,'init_from',{},'entities/soma_vr/s26f/'+name+'.dds')
    fx=el(root.find('{'+NS+'}library_effects'),'effect',{'id':name+'-fx'})
    pr=el(fx,'profile_COMMON');sf=el(el(pr,'newparam',{'sid':name+'-surface'}),'surface',{'type':'2D'});el(sf,'init_from',{},name+'-image')
    sa=el(el(pr,'newparam',{'sid':name+'-sampler'}),'sampler2D');el(sa,'source',{},name+'-surface')
    ph=el(el(pr,'technique',{'sid':'common'}),'phong');el(el(ph,'diffuse'),'texture',{'texture':name+'-sampler','texcoord':'UVSET0'})
    el(el(root.find('{'+NS+'}library_materials'),'material',{'id':name,'name':name}),'instance_effect',{'url':'#'+name+'-fx'})
    # Loader derives the .mat from the diffuse image path; the referenced DDS
    # is copied too, so either native material resolution route is valid.
    if not cap:
        tex=m.find('./TextureUnits/Diffuse').get('File')
        (OUT/(name+'.dds')).write_bytes((GAME/tex).read_bytes())
def write_cap_dds():
    header=[124,0x100f,1,1,4,0,0]+[0]*11+[32,0x41,0,32,0x00ff0000,0x0000ff00,0x000000ff,0xff000000,0x1000,0,0,0,0]
    assert len(header)==31
    (OUT/'wrist_cap.dds').write_bytes(b'DDS '+struct.pack('<31I',*header)+bytes([148,173,217,255]))
write_cap_dds();report=[]
for family,label in enumerate(['human','diving','deepsea','deepsea_mutilated']):
  for hand,side in enumerate(['left','right']):
    name=f'hand_{label}_{side}';src=GAME/(f'hand_{side}.skin' if family==0 else name+'.skin');b=src.read_bytes()
    magic,nv,nj,*pivot=struct.unpack_from('<3I3f',b);assert magic==0x484e4435 and nj<=32
    off=24+nv*64;assert len(b)==off+nj*148
    joints=[struct.unpack_from('<2i35f',b,off+j*148) for j in range(nj)]
    parents=[j[0] for j in joints];invbind=[np.array(j[21:37]).reshape(4,4) for j in joints]
    assert all(-1<=p<j for j,p in enumerate(parents))
    raw=R/'build'/(name+'.vertices')
    if family==3 and hand==0:raw.write_bytes(b[24:off]);count,capstart,capnum=nv,nv,0
    else:
        run=subprocess.run([str(R/'build/export_wrist.exe'),str(src),str(raw),str(family),str(hand)],capture_output=True,text=True,check=True)
        count,capstart,capnum=map(int,run.stdout.split());assert capstart+capnum==count and capnum>0
    data=raw.read_bytes();verts=np.frombuffer(data,dtype='<f4').reshape(-1,16).copy();ids=np.frombuffer(data,dtype='<i4').reshape(-1,16)[:,8:12]
    assert len(verts)==count and np.isfinite(verts[:,:8]).all()
    weights=verts[:,12:16];assert np.max(abs(weights.sum(axis=1)-1))<.002
    assert np.all((ids>=0)&(ids<nj))
    C=np.eye(4);C[:3,:3]*=.01;C[:3,3]=-np.array(pivot)*.01
    P=np.diag([.01,.01,.01,1]);Pi=np.linalg.inv(P);Ci=np.linalg.inv(C)
    bindworld=[C@np.linalg.inv(x)@Pi for x in invbind]
    bindlocal=[w if p<0 else np.linalg.inv(bindworld[p])@w for w,p in zip(bindworld,parents)]
    invnative=[P@x@Ci for x in invbind]
    # Prove the change of units/pivot preserves the existing weighted skinning.
    world=[]
    for j,rec in enumerate(joints):
        m=np.array(rec[5:21]).reshape(4,4);p=parents[j];world.append(m if p<0 else world[p]@m)
    maxerr=0.
    for i in range(0,count,max(1,count//250)):
        v=np.r_[verts[i,:3],1.];old=np.zeros(4);new=np.zeros(4)
        for k in range(4):
            j=ids[i,k];w=float(weights[i,k]);old+=w*(world[j]@invbind[j]@v);new+=w*((C@world[j]@Pi)@invnative[j]@C@v)
        maxerr=max(maxerr,float(np.max(abs(C@old-new))))
    assert maxerr<1e-6,maxerr
    root=E.Element('{'+NS+'}COLLADA',{'version':'1.4.1'})
    asset=el(root,'asset');el(asset,'unit',{'meter':'1','name':'meter'});el(asset,'up_axis',{},'Y_UP')
    for lib in ['images','effects','materials','geometries','controllers','visual_scenes']:el(root,'library_'+lib)
    mat='hands_human_skin' if family==0 else ('hands_diving' if family==1 else ('hands_deepsea_mutilated' if family==3 and hand==0 else 'hands_deepsea'))
    material(root,mat);material(root,'wrist_cap',True)
    scene=el(root.find('{'+NS+'}library_visual_scenes'),'visual_scene',{'id':'Scene','name':'Scene'});nodes=[]
    bone_names=[f'VR_J{j:02d}' for j in range(nj)]
    for j,p in enumerate(parents):
        node=el(scene if p<0 else nodes[p],'node',{'id':bone_names[j],'sid':bone_names[j],'name':bone_names[j],'type':'JOINT'});el(node,'matrix',{'sid':'transform'},nums(bindlocal[j]));nodes.append(node)
    # HPL's COLLADA loader accepts one material/triangles set per geometry.
    # Split the cap into its own geometry and controller, with local indices.
    for part,start,num,mt in [('Hand',0,capstart,mat),('WristCap',capstart,capnum,'wrist_cap')]:
        if num==0:continue
        gid=part+'Geometry';cid=part+'Skin'
        mesh=el(el(root.find('{'+NS+'}library_geometries'),'geometry',{'id':gid,'name':gid}),'mesh')
        vv=verts[start:start+num];ii=ids[start:start+num];ww=weights[start:start+num]
        pos=vv[:,:3]*.01-np.array(pivot)*.01
        source(mesh,part+'positions',pos,3,[(x,'float') for x in ['X','Y','Z']])
        source(mesh,part+'normals',vv[:,3:6],3,[(x,'float') for x in ['X','Y','Z']])
        uv=vv[:,6:8].copy();uv[:,1]=1-uv[:,1]
        if part=='WristCap':
            # A constant-colour texture still needs nondegenerate UVs for HPL's tangent builder.
            axes=np.argsort(np.ptp(pos,axis=0))[-2:]
            uv=pos[:,axes]*20.0
        source(mesh,part+'uv',uv,2,[('S','float'),('T','float')])
        el(el(mesh,'vertices',{'id':part+'vertices'}),'input',{'semantic':'POSITION','source':'#'+part+'positions'})
        tri=el(mesh,'triangles',{'count':str(num//3),'material':mt})
        for sem,ref,offset in [('VERTEX','vertices',0),('NORMAL','normals',1),('TEXCOORD','uv',2)]:
            attr={'semantic':sem,'source':'#'+part+ref,'offset':str(offset)}
            if sem=='TEXCOORD':attr['set']='0'
            el(tri,'input',attr)
        el(tri,'p',{},' '.join(str(i) for i in range(num) for _ in range(3)))
        skin=el(el(root.find('{'+NS+'}library_controllers'),'controller',{'id':cid}),'skin',{'source':'#'+gid})
        el(skin,'bind_shape_matrix',{},nums(np.eye(4)))
        source(skin,part+'joints',bone_names,1,[('JOINT','Name')],'Name')
        source(skin,part+'bindposes',invnative,16,[('TRANSFORM','float4x4')])
        source(skin,part+'weights',ww,1,[('WEIGHT','float')])
        j=el(skin,'joints')
        el(j,'input',{'semantic':'JOINT','source':'#'+part+'joints'})
        el(j,'input',{'semantic':'INV_BIND_MATRIX','source':'#'+part+'bindposes'})
        vw=el(skin,'vertex_weights',{'count':str(num)})
        el(vw,'input',{'semantic':'JOINT','source':'#'+part+'joints','offset':'0'})
        el(vw,'input',{'semantic':'WEIGHT','source':'#'+part+'weights','offset':'1'})
        el(vw,'vcount',{},' '.join(['4']*num))
        el(vw,'v',{},' '.join(f'{int(ii[i,k])} {i*4+k}' for i in range(num) for k in range(4)))
        meshnode=el(scene,'node',{'id':part,'name':part,'type':'NODE'})
        ctrl=el(meshnode,'instance_controller',{'url':'#'+cid})
        for j,p in enumerate(parents):
            if p<0:el(ctrl,'skeleton',{},'#'+bone_names[j])
        bm=el(el(ctrl,'bind_material'),'technique_common')
        el(el(bm,'instance_material',{'symbol':mt,'target':'#'+mt}),'bind_vertex_input',{'semantic':'UVSET0','input_semantic':'TEXCOORD','input_set':'0'})
    el(el(root,'scene'),'instance_visual_scene',{'url':'#Scene'})
    E.ElementTree(root).write(OUT/(name+'.dae'),encoding='utf-8',xml_declaration=True)
    report.append({'mesh':name,'source_sha256':hashlib.sha256(b).hexdigest(),'vertices':count,'cap_vertices':capnum,'bones':nj,'coordinate_equivalence_error':maxerr})
(R/'audit/native_hand_assets.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
