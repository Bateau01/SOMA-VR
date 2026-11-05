def transform(code,root,serial_cost=False,invert=False):
 policy=(root/('tests/cpu40_policy.inc' if serial_cost else 'tests/cpu38_policy.inc')).read_text()
 code='#ifndef C38_BLOCK_STEPS\n#define C38_BLOCK_STEPS 97u\n#endif\n'+policy+code
 old='#define C37_MODE(j) c37_mode()';assert code.count(old)==1
 code=code.replace(old,'#define C37_MODE(j) c38_select((j)->world,(unsigned)(j)->limit,g_h14PhysicsSteps,((g_h14PhysicsSteps/C38_BLOCK_STEPS)%4u==1u||(g_h14PhysicsSteps/C38_BLOCK_STEPS)%4u==2u),(u64)cpuFreq)')
 old='c37Counts[c->n==8?3:c->n==4?2:c->n==2?1:0]++;';assert code.count(old)==1
 code=code.replace(old,'detail|=(1u<<13)|(c38Enabled<<12);u64 largest=0;u64 cost=c->joined-c->start;if(c->n){cost=0;for(unsigned i=0;i<c->n;i++){u64 part=c->end[i]-c->begin[i];cost+=part;if(part>largest)largest=part;}}c38_observe(cost,largest,c->n);'+old)
 if invert:
  needle="((g_h14PhysicsSteps/C38_BLOCK_STEPS)%4u==1u||(g_h14PhysicsSteps/C38_BLOCK_STEPS)%4u==2u)"
  assert code.count(needle)==1
  code=code.replace(needle,"(!"+needle+")")
 return code
