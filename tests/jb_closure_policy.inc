/* Private policy prototype. No engine callbacks or retained engine pointers.
   One opening per actual squeeze edge, bounded in seconds, never a held-grip retry.
   Caller must consume BEFORE dispatch, including a denied native transaction. */
typedef struct { float remaining; unsigned lastStep; int armed; } JBClosureWindow;
static void jb_closure_cancel(JBClosureWindow* w){w->remaining=0;w->armed=0;}
static int jb_closure_step(JBClosureWindow* w,unsigned step,float dt,int edge,
                          int eligible,int gripHeld,int transactionStarted,
                          int closing,int currentContact){
 if(!eligible||!gripHeld||transactionStarted||!(dt>0&&dt<=.05f)){
  jb_closure_cancel(w);w->lastStep=step;return 0;
 }
 if(edge){w->remaining=.20f;w->armed=1;w->lastStep=step;return 0;}
 if(!w->armed)return 0;
 if((unsigned)(step-w->lastStep)!=1u){jb_closure_cancel(w);return 0;}
 w->lastStep=step;w->remaining-=dt;
 if(w->remaining<=0||!closing){jb_closure_cancel(w);return 0;}
 if(!currentContact)return 0;
 jb_closure_cancel(w);return 1;
}
