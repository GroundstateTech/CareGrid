import datetime as dt
import subprocess
import time
from threading import RLock
try:
    import requests
except Exception:
    requests=None

class Notifier:
    def __init__(self,webhook='',command=''):self.webhook=webhook;self.command=command
    def alert(self,payload):
        try:print('\a',end='',flush=True)
        except Exception:pass
        if self.webhook and requests:
            try:requests.post(self.webhook,json=payload,timeout=2)
            except Exception:pass
        if self.command:
            try:subprocess.Popen(self.command,shell=True)
            except Exception:pass

class AlertManager:
    def __init__(self,thresholds,notifier):self.thresholds=thresholds;self.notifier=notifier;self.silence_until=0.0;self._history=[];self._active={};self._lock=RLock()
    def update_thresholds(self,thresholds):self.thresholds=thresholds
    def _v(self,row,key):
        try:
            raw=row.get(key,'');return None if raw in ('',None) else float(raw)
        except Exception:return None
    def evaluate_status(self,row):
        t=self.thresholds;hr,spo2=self._v(row,'hr'),self._v(row,'spo2');bs,bd=self._v(row,'bp_sys'),self._v(row,'bp_dia');rr,temp=self._v(row,'rr'),self._v(row,'temp')
        critical=[hr is not None and (hr<t['hr']['low'] or hr>t['hr']['high']),spo2 is not None and spo2<t['spo2']['low'],bs is not None and (bs<t['bp_sys']['low'] or bs>t['bp_sys']['high']),bd is not None and bd>t['bp_dia']['high'],rr is not None and (rr<t['rr']['low'] or rr>t['rr']['high']),temp is not None and (temp<t['temp']['low'] or temp>t['temp']['high'])]
        if any(critical):return 'crit'
        if spo2 is not None and spo2<t.get('spo2',{}).get('warn_low',92):return 'warn'
        return 'ok'
    def evaluate_and_maybe_alert(self,row):
        status=self.evaluate_status(row);pid=str(row.get('patient_id') or row.get('device_id') or 'unknown')
        with self._lock:
            previous=self._active.get(pid);self._active[pid]=status
            if status=='crit' and previous!='crit':
                item={'time':dt.datetime.now().isoformat(' '),'patient':row.get('patient_id',''),'device_id':row.get('device_id',''),'status':'critical','acknowledged':False,'summary':self.describe(row)};self._history.append(item);self._history=self._history[-2000:]
                if time.time()>=self.silence_until:self.notifier.alert({'type':'critical','patient':row.get('patient_id'),'timestamp':row.get('timestamp'),'metrics':{k:row.get(k) for k in ('hr','spo2','bp_sys','bp_dia','rr','temp')}})
        return status
    def describe(self,row):return f"HR {row.get('hr') or '—'} | SpO2 {row.get('spo2') or '—'} | BP {row.get('bp_sys') or '—'}/{row.get('bp_dia') or '—'} | RR {row.get('rr') or '—'} | Temp {row.get('temp') or '—'}"
    def silence_for(self,seconds):self.silence_until=time.time()+int(seconds)
    def acknowledge_all(self):
        with self._lock:
            for item in self._history:item['acknowledged']=True
    def history(self):
        with self._lock:return list(self._history)
