import threading
try:
    import serial
    import serial.tools.list_ports
except Exception:
    serial=None
class SerialAdapter:
    def __init__(self,on_record,port='COM3',baud=9600):self.on_record=on_record;self.port=port;self.baud=int(baud);self.running=False;self.ser=None;self.last_error=''
    @staticmethod
    def ports():
        if not serial:return []
        try:return [p.device for p in serial.tools.list_ports.comports()]
        except Exception:return []
    def start(self):
        if self.running:return
        if not serial:raise RuntimeError('pyserial is not installed')
        self.running=True;threading.Thread(target=self._run,daemon=True).start()
    def stop(self):
        self.running=False
        try:
            if self.ser:self.ser.close()
        except Exception:pass
    def _run(self):
        try:
            self.ser=serial.Serial(self.port,self.baud,timeout=1)
            while self.running:
                raw=self.ser.readline()
                if not raw:continue
                text=raw.decode(errors='ignore').strip()
                if text:self.on_record({'source_type':'serial','source_name':self.port,'device_type':'Serial','device_id':self.port,'event':'Serial frame','context':text})
        except Exception as e:self.last_error=str(e);self.running=False
        finally:
            try:
                if self.ser:self.ser.close()
            except Exception:pass
