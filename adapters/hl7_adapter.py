import socket, threading
class HL7Server:
    def __init__(self,on_record,port=2575,host='127.0.0.1'):self.on_record=on_record;self.port=int(port);self.host=host;self.running=False;self.sock=None;self.last_error=''
    def start(self):
        if self.running:return
        self.running=True;threading.Thread(target=self._run,daemon=True).start()
    def stop(self):
        self.running=False
        try:
            if self.sock:self.sock.close()
        except Exception:pass
    def _run(self):
        try:
            self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM);self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);self.sock.bind((self.host,self.port));self.sock.listen(8);self.sock.settimeout(1)
            while self.running:
                try:conn,_=self.sock.accept()
                except socket.timeout:continue
                threading.Thread(target=self._client,args=(conn,),daemon=True).start()
        except Exception as e:self.last_error=str(e);self.running=False
    def _client(self,conn):
        with conn:
            conn.settimeout(2);buf=b''
            while self.running:
                try:chunk=conn.recv(8192)
                except socket.timeout:continue
                except Exception:break
                if not chunk:break
                buf+=chunk
                while b'\x1c\x0d' in buf:
                    packet,buf=buf.split(b'\x1c\x0d',1);packet=packet.lstrip(b'\x0b');self._parse(packet.decode(errors='ignore').replace('\r','\n'))
                    try:conn.sendall(b'\x0bMSA|AA\x1c\x0d')
                    except Exception:pass
            if buf.strip():self._parse(buf.decode(errors='ignore').replace('\r','\n'))
    def _parse(self,text):
        patient=''
        for line in text.splitlines():
            parts=line.split('|')
            if parts and parts[0]=='PID' and len(parts)>3:patient=parts[3]
            if parts and parts[0]=='OBX' and len(parts)>5:
                ident=parts[3].upper();value=parts[5];rec={'source_type':'hl7','source_name':f'{self.host}:{self.port}','patient_id':patient,'device_type':'HL7','event':f'HL7 OBX {parts[3]}','context':line}
                if 'SPO2' in ident or 'O2SAT' in ident:rec['spo2']=value
                elif 'HEART' in ident or ident.endswith('HR') or '^HR' in ident:rec['hr']=value
                elif 'RESP' in ident or ident.endswith('RR'):rec['rr']=value
                elif 'TEMP' in ident:rec['temp']=value
                elif 'BP' in ident and '/' in value:rec['bp_sys'],rec['bp_dia']=value.split('/',1)
                self.on_record(rec)
