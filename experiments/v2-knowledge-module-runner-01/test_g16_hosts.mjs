// Explicit synthetic host and broker fixture entry. Never resolve an installed SDK.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import fsp from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {resolve,sep} from 'node:path';
import {syncBuiltinESMExports} from 'node:module';
import child from 'node:child_process';
import {sourceHosts} from '../v2-native-minlive/unit1-controller-source-phase1/native_bridge.mjs';
import * as writer from './scale-04/writer_host.mjs';
import * as worker from './scale-04/active_worker_host.mjs';

const moduleRoot=fileURLToPath(new URL('.',import.meta.url));
const repo=resolve(moduleRoot,'../..');
const temp=resolve(process.env.TMPDIR);
const allowed=[repo,temp];
const inside=(p,root)=>p===root||p.startsWith(root+sep);
const check=raw=>{const p=resolve(raw instanceof URL?fileURLToPath(raw):String(raw));
  if(!allowed.some(root=>inside(p,root)))throw Error('PRIVATE_READ_STOP');};
for(const [obj,key] of [[fs,'readFileSync'],[fs,'readFile'],[fsp,'readFile']]){
  const original=obj[key];obj[key]=function(path,...args){check(path);return original.call(this,path,...args);};
}
for(const key of ['spawn','exec','execFile','fork','spawnSync','execSync','execFileSync'])child[key]=()=>{throw Error('PROCESS_STOP');};
globalThis.fetch=()=>{throw Error('NETWORK_STOP');};
syncBuiltinESMExports();
assert.throws(()=>fs.readFileSync(resolve(process.env.HOME,'.pi/agent/auth.json')),/PRIVATE_READ_STOP/);
assert.throws(()=>child.spawn('unapproved'),/PROCESS_STOP/);
assert.throws(()=>globalThis.fetch('https://example.invalid'),/NETWORK_STOP/);
assert.deepEqual(sourceHosts(),['writer_host.mjs','active_worker_host.mjs'].map(n=>resolve(moduleRoot,'scale-04',n)));
assert.equal(typeof worker.validateRoleRequest,'function');
let calls=0,wires=0;
const model={provider:'openai',id:'gpt-6-luna',api:'openai-responses',reasoning:true,
  contextWindow:4000,maxTokens:1000,cost:{input:0,output:0,cacheRead:0,cacheWrite:0}};
const request={schemaVersion:'unit-writer/1',stage:'write',binding:'fixture',inputBinding:'a'.repeat(64),sourceBinding:'b'.repeat(64),
  context:{systemPrompt:'synthetic system',messages:[{role:'user',content:'synthetic user',timestamp:0}]}};
const runtime={getError:()=>null,getPhysicalModel:()=>model,completeSimple:async(m,ctx,options)=>{
  calls++;assert.equal(options.maxRetries,0);assert.equal(options.reasoning,'medium');options.transformHeaders({});
  options.onPayload({model:m.id,store:false,stream:true,reasoning:{effort:'medium'},input:[{role:'system',content:ctx.systemPrompt},{role:'user',content:ctx.messages[0].content}]});
  options.onProviderStreamEvent({type:'response.completed',response:{usage:{input_tokens:1,output_tokens:1,total_tokens:2}}});
  return {stopReason:'stop',content:[{type:'text',text:'synthetic response'}],usage:{input:1,output:1,cacheRead:0,cacheWrite:0,totalTokens:2,cost:{input:0,output:0,cacheRead:0,cacheWrite:0,total:0}}};
}};
assert.equal((await writer.completeIsolated(request,runtime,writer.validateRequest,{onWire:()=>wires++})).text,'synthetic response');
assert.equal(calls,1);assert.equal(wires,1);
// Includes both actual relocated dynamic hosts through a fake ModelRuntime and
// exact permit-before-one-fetch protocol; no network/model discovery/credentials.
await import('../v2-native-minlive/unit1-quota-embedding-source-01/test_broker.mjs');
console.log('PASS G16 synthetic JS source hosts, boundary canaries and injected broker (not SDK/live proof)');
