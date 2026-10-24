from pathlib import Path
r=Path('.');p=r/'source/s26n.c';s=p.read_text();s=s.replace('1.0.9-S26HV','1.0.9-S26HW');s=s.replace('metric*(-.9f*V[a]+.75f*V[4+a]-1.65f*V[8+a])','metric*(-.9f*V[a]+.75f*V[4+a]-H5755DU_SUBTITLE_DISTANCE_M*V[8+a])')
needle='static i32 h5755fm_refresh_subtitle_final_translation(void* set,void* renderContext){'
diag='''// HW: observation only, bounded to twelve sampled frame pairs. No GL query,
// pose write, smoothing or interpolation. Multiple final passes are recorded
// without assuming pass order proves eye identity.
static void s26hw_subtitle_compare(const float* M){
    static float first[16];static u32 frame,epoch,logs;static u8 valid,reported;
    if(logs>=12u)return;
    if(!valid || epoch!=g_h5748oFrameSyncEpoch || frame!=g_frameCounter){
        if(valid && epoch==g_h5748oFrameSyncEpoch && (u32)(g_frameCounter-frame)<300u)return;
        h10_copy_f(first,M,16);frame=g_frameCounter;epoch=g_h5748oFrameSyncEpoch;valid=1;reported=0;return;
    }
    if(reported)return;reported=1;logs++;
    float rot=0,delta[3];for(i32 a=0;a<3;a++){
        delta[a]=M[a*4+3]-first[a*4+3];
        for(i32 b=0;b<3;b++){float d=h9_abs(M[a*4+b]-first[a*4+b]);if(d>rot)rot=d;}
    }
    ext_Log(">>> S26HW SUBTITLE FINAL PASS PAIR %u: frame %u rotation-max-delta %.6f translation-delta(%+.6f %+.6f %+.6f) distance %.2fm | observation only; pass identity not inferred",logs,frame,(double)rot,(double)delta[0],(double)delta[1],(double)delta[2],(double)H5755DU_SUBTITLE_DISTANCE_M);
}
'''
assert needle in s;s=s.replace(needle,diag+needle,1)
needle='float M[16];s26bb_subtitle_matrix(M,cx,cy,cz,fx,fz,apitch,h5755ea_world_units_per_meter());';assert needle in s;s=s.replace(needle,needle+'\n    s26hw_subtitle_compare(M);',1);p.write_text(s)
for path in ['runtime/script/modules/MenuHandler.hps','installer/source/Build.ps1','installer/source/Installer.cs','installer/source/CurrentUpgradeTests.cs']:
 p=r/path;p.write_bytes(p.read_bytes().replace(b'S26HV',b'S26HW').replace(b'2026102205',b'2026102206'))
p=r/'scripts/package_hw.py';s=(r/'scripts/package_hv.py').read_text().replace('S26HV','S26HW').replace('2026102205','2026102206');p.write_text(s)
