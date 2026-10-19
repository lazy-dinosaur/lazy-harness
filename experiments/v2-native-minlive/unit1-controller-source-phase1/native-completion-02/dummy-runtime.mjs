// SYNTHETIC EXPORT MODULE. Never imports a real SDK or auth provider.
export const ModelRuntime={create:async options=>{
 if(options.modelsPath!==null || options.allowModelNetwork!==false || options.refreshOnCreate!==false)throw Error('fixture create contract');
 const model={provider:'openai',id:'gpt-6-luna',api:'openai-responses',reasoning:true,
              cost:{input:0,output:0,cacheRead:0,cacheWrite:0},contextWindow:300000,maxTokens:10000};
 return {getError:()=>null,getPhysicalModel:(provider,id)=>provider==='openai'&&id===model.id?model:undefined,
 completeSimple:async(m,context,opts)=>{
   if(opts.maxRetries!==0 || opts.reasoning!=='medium' || !opts.signal)throw Error('fixture SDK option contract');
   const credential=await options.credentials.read('openai');
   const headers=opts.transformHeaders({Authorization:'Bearer '+credential.key});
   const payload={model:m.id,input:[{role:'system',content:context.systemPrompt},{role:'user',content:context.messages[0].content}],
                  store:false,stream:true,reasoning:{effort:'medium'}};
   opts.onPayload(payload);
   const response=await opts.fetch('https://synthetic.invalid/responses',{method:'POST',headers,body:JSON.stringify(payload),signal:opts.signal});
   const text=await response.text();
   const events=text.split('\n\n').filter(Boolean).map(frame=>JSON.parse(frame.split('\n').find(l=>l.startsWith('data:')).slice(5)));
   const end=events.find(e=>e.type==='response.completed');if(!end)throw Error('fixture no completion');
   opts.onProviderStreamEvent(end);
   return {stopReason:'stop',content:[{type:'text',text:end.response.output_text}],
           usage:{input:1,output:1,cacheRead:0,cacheWrite:0,totalTokens:2,cost:{input:0,output:0,cacheRead:0,cacheWrite:0,total:0.000001}}};
 }};
}};
