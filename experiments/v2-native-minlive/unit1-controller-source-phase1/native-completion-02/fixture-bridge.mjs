import {privateChannel,runBridge} from '../native_bridge.mjs';
const channel=privateChannel(Number(process.argv[2]));
const mode=process.argv[4]||'ok';
const transport=async(url,init)=>{
 if(mode==='bypass')await globalThis.fetch('https://unbrokered.invalid');
 if(mode==='timeout')await new Promise((_,reject)=>{init.signal.addEventListener('abort',()=>reject(Error('fixture deadline')),{once:true});});
 const headers=new Headers(init.headers);
 if(headers.get('authorization')!=='Bearer SYNTHETIC_NEVER_LOG_KEY' || init.redirect!=='error' || !init.signal)throw Error('fixture broker contract');
 const body=JSON.parse(init.body);
 if(String(url).endsWith('/v1/systemone')) {
   const answers=Object.fromEntries(Object.entries(body.questions).map(([key,q])=>[key,q.type==='choice'
     ?{choice:Object.keys(q.criteria)[0],probabilities:Object.fromEntries(Object.keys(q.criteria).map((k,i)=>[k,i?0:1]))}
     :{[q.type]:0.99}]));
   return Response.json({model:body.model,answers,usage:{input_tokens:1,output_tokens:1,cost:0.000001}});
 }
 const env=JSON.parse(body.input[1].content);
 const answer=env.role==='extract'?{items:[{content:'fixture source',target_expression:'fixture',source_ranges:[[1,1]]}]}
   :{fact:'fixture sentence',keywords:['fixture'],source_ranges:[[1,1]],reason:'synthetic only'};
 const event={type:'response.completed',response:{status:'completed',model:mode==='wrongmodel'?'wrong':'gpt-6-luna',
              usage:{input_tokens:1,output_tokens:1,total_tokens:2},output_text:JSON.stringify(answer)}};
 const value='event: response.completed\ndata: '+JSON.stringify(event)+(mode==='truncated'?'':'\n\n');
 const data=new TextEncoder().encode(value);
 const stream=new ReadableStream({start(controller){for(let i=0;i<data.length;i+=7)controller.enqueue(data.slice(i,i+7));controller.close();}});
 return new Response(stream,{headers:{'Content-Type':'text/event-stream'}});
};
try{if(mode==='badipc')channel.put({type:'wire',url:'invalid-fixture-URL',body:'{'});
    else await runBridge(channel,process.argv[3],{fetch:transport});channel.close();}
catch{channel.put({type:'error'});channel.close();process.exitCode=1;}
