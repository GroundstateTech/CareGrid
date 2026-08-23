import threading,time
try:
    from sdc11073 import wsdiscovery
except Exception:
    wsdiscovery=None
class SDCAdapter:
    def __init__(self,on_record):self.on_record=on_record;self.running=False;self.last_error='';self.discovered=[]
    def start(self):
        if self.running:return
        if not wsdiscovery:raise RuntimeError('sdc11073 is not installed')
        self.running=True;threading.Thread(target=self._discover,daemon=True).start()
    def stop(self):self.running=False
    def _discover(self):
        discovery=None
        try:
            discovery=wsdiscovery.WSDiscovery();discovery.start();started=time.time()
            while self.running and time.time()-started<10:
                services=discovery.searchServices();self.discovered=[]
                for service in services:
                    try:xaddrs=service.getXAddrs()
                    except Exception:xaddrs=[]
                    for addr in xaddrs:
                        if addr not in self.discovered:self.discovered.append(addr)
                time.sleep(2)
        except Exception as e:self.last_error=str(e)
        finally:
            self.running=False
            try:
                if discovery:discovery.stop()
            except Exception:pass
