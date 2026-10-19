// Offline actual broker: synthetic FD messages/auth module/fetch only, no SDK/network.
import {mkdtemp,writeFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {runBridge} from '../unit1-controller-source-phase1/native_bridge.mjs';
const dir=await mkdtemp(join(tmpdir(),'fixture-native-broker-'));
const auth=join(dir,'fixture-auth.mjs');
const bytes='export const read=async provider=>provider==="openai"?({type:"oauth",access:"SYNTHETIC_FIXTURE_ONLY"}):({type:"api_key",key:"SYNTHETIC_FIXTURE_ONLY"});';
await writeFile(auth,bytes);
const sha=v=>createHash('sha256').update(v).digest('hex');
const body={model:'perplexity/pplx-embed-v1-0.6b',input:['synthetic target','synthetic identity']};
const raw=JSON.stringify(body);const trace=[];let calls=0;
const packet={kind:'embedding',role:'query',url:'https://openrouter.ai/api/v1/embeddings',body,bodyRaw:raw,authModule:auth,authSHA:sha(bytes),deadlineMs:1000};
const queue=[packet,{type:'permit',requestSHA:'synthetic-authorized-request',bodySHA:sha(raw),timeoutMs:500}];
const channel={get:async()=>{trace.push('get');return queue.shift();},put:v=>{trace.push(v.type);if(v.type==='wire'){assert.equal(v.body,raw);assert.equal(v.url,packet.url);}if(v.type==='done')assert.equal(v.result.body.data.length,2);}};
try {
 await runBridge(channel,'unused-runtime',{fetch:async(url,init)=>{
  calls++;trace.push('physical');assert.equal(url,packet.url);assert.equal(init.redirect,'error');assert.equal(init.body,raw);
  return new Response(JSON.stringify({model:body.model,data:body.input.map((_,index)=>({index,embedding:Array(1024).fill(0)})),usage:{cost:.000001}}),{status:200});
 }});
 assert.equal(calls,1);assert.deepEqual(trace,['get','wire','get','physical','done']);
 console.log('actual broker embedding: exact raw body, permit-before-single-fetch, redirects:error, response returned PASS');
 const model={provider:'openai',id:'gpt-6-luna',api:'openai-responses',baseUrl:'https://api.openai.com/v1',reasoning:true,contextWindow:272000,maxTokens:128000,cost:{input:.1,output:.5,cacheRead:.01,cacheWrite:.125}};
 const runtime=join(dir,'fixture-runtime.mjs');
 const runtimeBytes=`const model=${JSON.stringify(model)};
 export const ModelRuntime={create:async({credentials})=>{await credentials.read('openai');return {
 getError:()=>null,getPhysicalModel:()=>model,
 completeSimple:async(m,context,options)=>{
 if(options.maxTokens!==undefined)throw Error('unexpected quota output cap');
 options.transformHeaders({});
 const payload={model:m.id,store:false,stream:true,reasoning:{effort:'medium'},input:[{role:'system',content:context.systemPrompt},{role:'user',content:context.messages[0].content}]};
 options.onPayload(payload);
 const response=await options.fetch('https://api.openai.com/v1/responses',{method:'POST',body:JSON.stringify(payload)});await response.text();
 options.onProviderStreamEvent({type:'response.completed',response:{usage:{input_tokens:2,output_tokens:1,total_tokens:3}}});
 return {stopReason:'stop',content:[{type:'text',text:'synthetic output'}],usage:{input:2,output:1,cacheRead:0,cacheWrite:0,totalTokens:3,cost:{input:1,output:6,cacheRead:0,cacheWrite:0,total:7}}};
 }}}};`;
 await writeFile(runtime,runtimeBytes);
 const sdk={kind:'sdk',role:'write',url:'https://api.openai.com/v1/responses',authModule:auth,authSHA:sha(bytes),deadlineMs:1000,
 sdkProfile:model,runtimeSHA:sha(runtimeBytes),profileSHA:'e'.repeat(64),request:{schemaVersion:'unit-writer/1',stage:'write',binding:'fixture',inputBinding:'a'.repeat(64),sourceBinding:'b'.repeat(64),context:{systemPrompt:'synthetic system',messages:[{role:'user',content:'synthetic user',timestamp:0}]}}};
 let wire;let sdkCalls=0;let permitRequested=false;let result;
 const sdkChannel={get:async()=>{if(!wire)return sdk;permitRequested=true;return {type:'permit',requestSHA:'fixture-quota',bodySHA:sha(wire),timeoutMs:500};},
 put:v=>{if(v.type==='wire'){wire=v.body;assert.equal(v.profileSHA,sdk.profileSHA);}if(v.type==='done')result=v.result;}};
 await runBridge(sdkChannel,runtime,{fetch:async(url,init)=>{
  sdkCalls++;assert.equal(permitRequested,true);assert.equal(init.redirect,'error');assert.equal(url,sdk.url);assert.equal(JSON.parse(init.body).max_output_tokens,undefined);
  return new Response('data: '+JSON.stringify({type:'response.completed',response:{model:'gpt-6-luna',status:'completed',usage:{input_tokens:2,output_tokens:1,total_tokens:3}}})+'\n\n',{status:200});
 }});
 assert.equal(sdkCalls,1);assert.equal(result.cost,7);assert.equal(result.ok,true);
 console.log('actual broker SDK: public profile match, quota preview/permit, unchanged omitted output cap, raw metric7 PASS');
} finally {await rm(dir,{recursive:true,force:true});}
