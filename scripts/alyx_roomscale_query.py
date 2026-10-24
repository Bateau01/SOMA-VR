import urllib.request,json,sys
from pathlib import Path
u='http://127.0.0.1:8001/mcp';h={'Content-Type':'application/json','Accept':'application/json, text/event-stream'}
init={'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'roomscale-audit','version':'1'}}}
with urllib.request.urlopen(urllib.request.Request(u,data=json.dumps(init).encode(),headers=h),timeout=15) as response:
 h['Mcp-Session-Id']=response.headers['mcp-session-id'];response.read()
def req(method,params,ident=2):
 p={'jsonrpc':'2.0','method':method,'params':params,'id':ident}
 r=urllib.request.urlopen(urllib.request.Request(u,data=json.dumps(p).encode(),headers=h),timeout=180);raw=r.read().decode()
 data=[json.loads(x[6:]) for x in raw.splitlines() if x.startswith('data: ')]
 return data[-1] if data else raw
if sys.argv[1]=='list':v=req('tools/list',{})
else:v=req('tools/call',{'name':sys.argv[1],'arguments':json.loads(sys.argv[2])})
p=Path(__file__).resolve().parents[1]/'audit/alyx-roomscale';p.mkdir(parents=True,exist_ok=True)
(p/(sys.argv[3] if len(sys.argv)>3 else 'tools.json')).write_text(json.dumps(v,indent=2))
print(json.dumps(v.get('result',{}).get('structuredContent',v)))
