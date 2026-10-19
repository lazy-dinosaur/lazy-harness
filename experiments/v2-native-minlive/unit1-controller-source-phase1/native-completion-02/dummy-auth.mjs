// Synthetic callback only. No env, file, SDK or credential-store access.
export async function read(provider){if(!['openai','jev'].includes(provider))throw Error('fixture provider');return {type:'api_key',key:'SYNTHETIC_NEVER_LOG_KEY'};}
