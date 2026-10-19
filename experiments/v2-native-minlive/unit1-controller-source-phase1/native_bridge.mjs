// Controller-private FD protocol. No credentials, request text or SDK errors on stdio.
import net from 'node:net';
import tls from 'node:tls';
import http from 'node:http';
import https from 'node:https';
import child from 'node:child_process';
import {AsyncLocalStorage} from 'node:async_hooks';
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
import {createInterface} from 'node:readline';
import {realpathSync} from 'node:fs';
import {syncBuiltinESMExports} from 'node:module';
const sha=v=>createHash('sha256').update(v).digest('hex');
const need=(ok)=>{if(!ok)throw new Error('NATIVE_STOP');};
const source=new URL('../../../experiments/v2-knowledge-module-runner-01/scale-04/',import.meta.url);
export function sourceHosts() {
  return ['writer_host.mjs','active_worker_host.mjs'].map(name=> {
    const path=fileURLToPath(new URL(name,source));need(realpathSync(path)===path);return path;
  });
}
export function privateChannel(fd) {
  const socket=new net.Socket({fd,readable:true,writable:true});
  const lines=createInterface({input:socket,crlfDelay:Infinity})[Symbol.asyncIterator]();
  return {get:async()=>{const row=await lines.next();need(!row.done && row.value.length<=16*1024*1024);return JSON.parse(row.value);},
          put:v=>socket.write(JSON.stringify(v)+'\n'),close:()=>socket.end(()=>socket.destroy())};
}
export function denyEgress() {
  const broker=new AsyncLocalStorage();
  const deny=()=>{throw new Error('NATIVE_EGRESS_STOP');};
  globalThis.fetch=deny;
  for(const [obj,key] of [[net.Socket.prototype,'connect'],[tls,'connect'],[http,'request'],[https,'request']]) {
    const original=obj[key]; obj[key]=function(...args){need(broker.getStore()===true);return original.apply(this,args);};
  }
  for(const key of ['spawn','exec','execFile','fork','spawnSync','execSync','execFileSync'])child[key]=deny;
  syncBuiltinESMExports();
  return broker;
}
export async function runBridge(channel,runtimePath,{fetch:transport=globalThis.fetch}={}) {
  // Capture the native fetch before public process-scope deny. No private SDK patch.
  const broker=denyEgress();
  const packet=await channel.get();
  const initial=AbortSignal.timeout(packet.deadlineMs);
  const authBytes=await readFile(packet.authModule); need(sha(authBytes)===packet.authSHA);
  const auth=await import(pathToFileURL(resolve(packet.authModule)).href);
  need(typeof auth.read==='function');
  const credentials={read:async provider=>{
    const value=await auth.read(provider);
    if(packet.sdkProfile && provider==='openai')need(value?.type==='oauth');
    return value;
  },list:async()=>[],
                     modify:async()=>{throw new Error('NATIVE_AUTH_STOP');},delete:async()=>{throw new Error('NATIVE_AUTH_STOP');}};
  let sent=false,wire=null;
  async function controlledFetch(url,init) {
    need(!sent && String(url)===packet.url && init.method?.toUpperCase()==='POST' && typeof init.body==='string');
    need(wire!==null && JSON.stringify(JSON.parse(init.body))===JSON.stringify(wire));
    sent=true;
    channel.put({type:'wire',url:String(url),body:init.body,...(packet.sdkProfile?{profileSHA:packet.profileSHA}:{})});
    const permit=await channel.get();
    need(permit.type==='permit' && typeof permit.requestSHA==='string' && permit.bodySHA===sha(init.body));
    const signal=AbortSignal.any([initial,AbortSignal.timeout(permit.timeoutMs)]);
    return broker.run(true,async()=> {
      const response=await transport(url,{...init,redirect:'error',signal});
      need(response.ok); return response;
    });
  }
  if(['jev','embedding'].includes(packet.kind)) {
    wire=packet.body;
    if(packet.kind==='embedding') {
      need(packet.url==='https://openrouter.ai/api/v1/embeddings' && ['query','passage'].includes(packet.role)
        && Object.keys(wire).sort().join(',')==='input,model' && wire.model==='perplexity/pplx-embed-v1-0.6b'
        && Array.isArray(wire.input) && wire.input.length>0 && wire.input.length<=16
        && wire.input.every(t=>typeof t==='string' && t.trim().length>0));
    }
    const credential=await credentials.read('jev');
    need(credential?.type==='api_key' && typeof credential.key==='string' && credential.key.length>0);
    const response=await controlledFetch(packet.url,{method:'POST',body:packet.bodyRaw,
      headers:{Authorization:'Bearer '+credential.key,'Content-Type':'application/json'}});
    const body=await response.json(); need(!body.error);
    channel.put({type:'done',result:{body}});
  } else {
    need(packet.kind==='sdk');
    need(['extract','write','subject-name'].includes(packet.role));
    if(packet.role==='subject-name') {
      const binding=packet.identityBinding;
      need(binding && binding.provider==='openai' && binding.model==='gpt-6-luna' && binding.role===packet.role
        && packet.request.role===packet.role && packet.request.schemaVersion==='active-worker/1'
        && ['inputBinding','sourceBinding'].every(key=>/^[a-f0-9]{64}$/.test(binding[key]) && binding[key]===packet.request[key]));
    }
    const {ModelRuntime}=await import(pathToFileURL(resolve(runtimePath)).href);
    const runtime=await ModelRuntime.create({credentials,modelsPath:null,allowModelNetwork:false,refreshOnCreate:false});
    if(packet.sdkProfile) {
      need(sha(await readFile(runtimePath))===packet.runtimeSHA);
      const actual=runtime.getPhysicalModel('openai','gpt-6-luna');
      need(actual && Object.keys(packet.sdkProfile).every(k=>JSON.stringify(actual[k])===JSON.stringify(packet.sdkProfile[k])));
      need(actual.api==='openai-responses' && actual.provider==='openai' && actual.id==='gpt-6-luna' && actual.reasoning===true);
    }
    sourceHosts();  // real file containment before either dynamic host import
    const writer=await import(new URL('writer_host.mjs',source));
    const worker=await import(new URL('active_worker_host.mjs',source));
    let payloads=0,completed=false;
    const fetch=async(url,init)=>{
      const response=await controlledFetch(url,init);
      const decoder=new TextDecoder('utf-8',{fatal:true}); let buffer='';
      const check=()=>{let end;while((end=buffer.indexOf('\n\n'))>=0){const frame=buffer.slice(0,end);buffer=buffer.slice(end+2);
        const raw=frame.split('\n').filter(l=>l.startsWith('data:')).map(l=>l.slice(5).trimStart()).join('\n');
        if(!raw)continue; const event=JSON.parse(raw);need(event.type!=='error' && event.type!=='response.failed');
        if(event.type==='response.completed'){need(!completed && event.response?.model==='gpt-6-luna' && event.response.status==='completed' && event.response.usage);completed=true;}}};
      const stream=response.body.pipeThrough(new TransformStream({transform(chunk,controller){
        buffer+=decoder.decode(chunk,{stream:true});buffer=buffer.replaceAll('\r\n','\n');check();controller.enqueue(chunk);},
        flush(){buffer+=decoder.decode();check();need(!buffer.trim() && completed);}}));
      return new Response(stream,{status:response.status,headers:response.headers});
    };
    const options={fetch,signal:initial,onWire:payload=>{need(++payloads===1 && payload.model==='gpt-6-luna');wire=structuredClone(payload);}};
    const result=packet.request.schemaVersion==='unit-writer/1'
      ?await writer.completeIsolated(packet.request,runtime,writer.validateRequest,options)
      :await worker.completeRole(packet.request,runtime,options);
    need(sent && payloads===1 && completed && result.ok);
    channel.put({type:'done',result});
  }
}
if(process.argv[1] && resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  const channel=privateChannel(Number(process.argv[2]));
  try{await runBridge(channel,process.argv[3]);channel.close();}
  catch{channel.put({type:'error'});channel.close();process.exitCode=1;}
}
