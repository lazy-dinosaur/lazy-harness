"""Private FD IPC: stdout/stderr are never an auth/prompt transport or log."""
import json
import os
from pathlib import Path
import socket
import subprocess
import time
import controller as c

class NodeBridge:
    def __init__(self,config,deadline,guard,evidence_directory):
        self.config,self.deadline,self.guard=config,deadline,guard
        self.evidence_directory=Path(evidence_directory)
    def argv(self,fd):
        # Official existing Source resolver, only after full admission; no new resolver.
        from writer_transport import runtime_path
        from native_services import public_source_roots
        public_source_roots()
        return ['node',str(Path(__file__).with_suffix('.mjs')),str(fd),str(runtime_path())]
    def exchange(self,payload,expected,quote,wire,*,validate,quote_for=None):
        from native_services import NativeStop
        parent,child=socket.socketpair()
        process=None; result=None; failed=True; stream=None
        left=self.deadline.remaining()
        if payload['kind']=='sdk' and wire.sdk_quota is not None:
            left=min(left,wire.sdk_quota.call_seconds)
        try:
            self.guard.spawning=True
            try:
                process=subprocess.Popen(self.argv(child.fileno()),pass_fds=(child.fileno(),),
                    stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                    env={'PATH':os.defpath,'PI_OFFLINE':'1'})
            finally: self.guard.spawning=False
            child.close()
            parent.settimeout(self.deadline.remaining())
            stream=parent.makefile('rwb',buffering=0)
            def put(value):
                raw=json.dumps(value,ensure_ascii=False,allow_nan=False).encode()+b'\n'
                parent.sendall(raw)
            def get():
                parent.settimeout(self.deadline.remaining())
                raw=stream.readline(16*1024*1024+1)
                c.require(raw.endswith(b'\n') and len(raw)<=16*1024*1024,'native IPC truncated/oversized STOP')
                return json.loads(raw)
            cfg=self.config
            put({**payload,'bodyRaw':expected.body.decode() if expected else None,
                 'authModule':cfg.auth_module,'authSHA':cfg.auth_sha,
                 'deadlineMs':max(1,int(left*1000))})
            message=get()
            c.require(set(message)==({'type','url','body','profileSHA'} if payload.get('sdkProfile') is not None else {'type','url','body'}) and message['type']=='wire'
                      and message['url']==payload['url'],'native wire IPC/URL drift')
            raw=message['body'].encode()
            body=json.loads(raw)
            if payload['kind']=='sdk':
                c.require(body.get('model')=='gpt-6-luna','native SDK model drift')
                binding=payload.get('identityBinding',{})
                expected=c.Request('sdk','openai','gpt-6-luna',payload['role'],raw,0,
                                   binding.get('inputBinding',''),binding.get('sourceBinding',''))
                if payload.get('sdkProfile') is not None:
                    c.require(message.get('profileSHA')==payload['profileSHA'] and wire.sdk_quota is not None
                              and payload['profileSHA']==wire.sdk_quota.profile_sha, 'runtime SDK profile observation drift')
                quote=quote_for(expected)
            else:
                c.require(raw==expected.body,'native final body projection drift')
            def send(request):
                # WireBoundary/Ledger has already reserved before this grant.
                put({'type':'permit','requestSHA':c.digest(c.request_identity(request)),
                     'bodySHA':c.sha(raw),'timeoutMs':max(1,int(min(self.deadline.remaining(),quote.call_seconds if type(quote) is c.SubscriptionQuota else self.deadline.remaining())*1000))})
                answer=get()
                c.require(set(answer)=={'type','result'} and answer['type']=='done','native SDK/HTTP uncertain STOP')
                return validate(answer['result'])
            result=wire.attempt(expected,quote,send)
            parent.shutdown(socket.SHUT_WR)
            process.wait(timeout=self.deadline.remaining())
            c.require(process.returncode==0,'native process failure STOP')
            failed=False
            return result
        except BaseException:
            wire.stopped=True
            raise NativeStop('native IPC/wire failure; retain reserve; no retry') from None
        finally:
            if stream is not None: stream.close()
            parent.close(); child.close()
            if process is not None:
                if process.poll() is None: process.kill()
                process.wait(timeout=max(.01,self.deadline.end-time.monotonic()))
                receipt={'pid':process.pid,'exit_code':process.returncode,'uncertain':failed,
                         'stdout':'discarded','stderr':'discarded','secret_logs':0}
                (self.evidence_directory/f'native-child-{process.pid}.json').write_text(json.dumps(receipt)+'\n')
