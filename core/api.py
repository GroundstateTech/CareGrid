import json, threading, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

def start_rest_api(port,get_patients,get_alerts,get_rows,host='127.0.0.1'):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,fmt,*args):return
        def send_json(self,status,data):
            body=json.dumps(data,default=str).encode('utf-8');self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        def do_GET(self):
            path,_,query=self.path.partition('?');args=urllib.parse.parse_qs(query)
            if path=='/health':return self.send_json(200,{'status':'ok','service':'CareGrid'})
            if path=='/patients':return self.send_json(200,get_patients())
            if path=='/alerts':return self.send_json(200,get_alerts())
            if path=='/data':
                try:limit=int(args.get('limit',[200])[0])
                except Exception:limit=200
                return self.send_json(200,get_rows(limit))
            return self.send_json(404,{'error':'not found'})
    server=ThreadingHTTPServer((host,int(port)),Handler);threading.Thread(target=server.serve_forever,daemon=True).start();return server
