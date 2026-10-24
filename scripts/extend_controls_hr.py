from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'runtime/script/props/Prop_MovingButton.hps'
s=p.read_text(encoding='utf-8-sig')
s=s.replace('file=="lightswitch_button.ent");','file=="lightswitch_button.ent" || file=="control_board_pplant_button.ent");',1)
s=s.replace('(body is paddle) ? "A" : "R"','file=="control_board_pplant_button.ent" ? "B" : ((body is paddle) ? "A" : "R")',1)
p.write_text(s,encoding='utf-8')
p=R/'source/s26n.c';s=p.read_text();s=s.replace('u32 id;i32 used,active,blocked;void *owner','u32 id;i32 used,active,blocked,frontAxis;void *owner',1);p.write_text(s)
p=R/'source/rocker_y.inc';s=p.read_text()
s=s.replace('i32 active=h5748t_sso_eq(cmd,"A",1u);','i32 power=h5748t_sso_eq(cmd,"B",1u);i32 active=power||h5748t_sso_eq(cmd,"A",1u);',1)
s=s.replace('r->used=1;r->id=id;r->active=active;','r->used=1;r->id=id;r->active=active;r->frontAxis=power?1:2;',1)
s=s.replace('if(!r->active||r->blocked||owner!=r->owner','if(!r->active||s26hr_control_blocked(r->owner)||owner!=r->owner',1)
s=s.replace('float front[3]={m[8],m[9],m[10]};','i32 axis=r->frontAxis*4;float front[3]={m[axis],m[axis+1],m[axis+2]};',1)
at='/* Called only for the first exact entity hit by the existing fingertip ray. */'
s=s.replace(at,'''// Children of one control share accepted-contact ownership.
static i32 s26hr_control_blocked(void* owner){
    for(i32 i=0;i<g_s26yCount;i++)if(g_s26yRocker[i].used&&g_s26yRocker[i].owner==owner&&g_s26yRocker[i].blocked)return 1;
    return 0;
}
'''+at,1)
p.write_text(s)
