from escape_surface_hy import *
for k in range(11108,12145):
 t=tri[k];c=t.mean(axis=0);n=np.cross(t[1]-t[0],t[2]-t[0]);n/=np.linalg.norm(n)
 if 253<c[1]<254.5 and -131.7<c[2]<-129 and n[1]>.4:print(k,np.round(c,4),np.round(n,4))
