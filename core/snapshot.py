import csv, datetime as dt, os, threading, time
try:
    import pandas as pd
except Exception:
    pd=None
class Snapshotter:
    def __init__(self,dirpath,datastore,interval_min=15):self.dirpath=dirpath;self.datastore=datastore;self.interval=max(1,int(interval_min))*60;self.running=False;self.thread=None
    def start(self):
        if self.running:return
        os.makedirs(self.dirpath,exist_ok=True);self.running=True;self.thread=threading.Thread(target=self._loop,daemon=True);self.thread.start()
    def stop(self):self.running=False
    def _loop(self):
        while self.running:
            for _ in range(self.interval):
                if not self.running:return
                time.sleep(1)
            self.write_snapshot()
    def write_snapshot(self):
        rows=self.datastore.tail(10000)
        if not rows:return
        path=os.path.join(self.dirpath,f"caregrid_snapshot_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        if pd:
            try:pd.DataFrame(rows).to_csv(path,index=False);return
            except Exception:pass
        with open(path,'w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
