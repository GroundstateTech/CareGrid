import socketserver,threading
class _Handler(socketserver.BaseRequestHandler):
    def handle(self):
        text=self.request[0].decode(errors='ignore').strip()
        if text:self.server.owner.on_record({'source_type':'syslog','source_name':f'udp:{self.server.server_address[1]}','device_type':'Syslog','event':'Syslog message','context':text})
class SyslogAdapter:
    def __init__(self,on_record,port=5514,host='127.0.0.1'):self.on_record=on_record;self.port=int(port);self.host=host;self.server=None;self.running=False;self.last_error=''
    def start(self):
        if self.running:return
        try:self.server=socketserver.ThreadingUDPServer((self.host,self.port),_Handler);self.server.owner=self;threading.Thread(target=self.server.serve_forever,daemon=True).start();self.running=True
        except Exception as e:self.last_error=str(e);raise
    def stop(self):
        self.running=False
        if self.server:
            try:self.server.shutdown();self.server.server_close()
            except Exception:pass
            self.server=None
