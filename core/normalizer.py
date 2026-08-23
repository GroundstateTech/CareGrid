import datetime as dt
import json

SCHEMA_FIELDS=['timestamp','patient_id','device_type','device_id','hr','spo2','bp_sys','bp_dia','rr','temp','flow','source_type','source_name','severity','event','context']
DEFAULT_THRESHOLDS={'hr':{'low':40,'high':150},'spo2':{'low':88,'warn_low':92},'bp_sys':{'low':80,'high':200},'bp_dia':{'high':120},'rr':{'low':8,'high':30},'temp':{'low':35.0,'high':39.5}}

def _num(value,floating=False):
    if value in (None,''):return ''
    try:return str(float(value) if floating else int(float(value)))
    except Exception:return str(value)

def normalize_row(data):
    row={k:'' for k in SCHEMA_FIELDS};row['timestamp']=str(data.get('timestamp') or dt.datetime.now().isoformat(' '));row['patient_id']=str(data.get('patient_id') or data.get('patient') or data.get('pid') or '');row['device_type']=str(data.get('device_type') or data.get('type') or '');row['device_id']=str(data.get('device_id') or data.get('device') or data.get('bed') or '');row['hr']=_num(data.get('hr') or data.get('heart_rate'));row['spo2']=_num(data.get('spo2') or data.get('SpO2') or data.get('o2'));bp=str(data.get('bp') or '')
    if '/' in bp:
        try:s,d=bp.split('/',1);row['bp_sys'],row['bp_dia']=_num(s),_num(d)
        except Exception:pass
    row['bp_sys']=row['bp_sys'] or _num(data.get('bp_sys'));row['bp_dia']=row['bp_dia'] or _num(data.get('bp_dia'));row['rr']=_num(data.get('rr') or data.get('resp_rate'));row['temp']=_num(data.get('temp') or data.get('temperature'),True);row['flow']=_num(data.get('flow'),True);row['source_type']=str(data.get('source_type') or '');row['source_name']=str(data.get('source_name') or '');row['severity']=str(data.get('severity') or 'INFO');row['event']=str(data.get('event') or '');context=data.get('context','')
    if isinstance(context,(dict,list)):context=json.dumps(context,default=str)
    row['context']=str(context);return row
