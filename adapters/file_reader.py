import csv, datetime as dt, json, os, sqlite3
try:
    import pandas as pd
except Exception:
    pd=None
try:
    import pyedflib
except Exception:
    pyedflib=None
try:
    import pypandoc
except Exception:
    pypandoc=None
try:
    from odf.opendocument import load as odf_load
    from odf import text as odf_text
except Exception:
    odf_load=None;odf_text=None
class FileReader:
    def _row(self,path,severity,event,context):return {'timestamp':dt.datetime.now().isoformat(' '),'patient_id':'','device_type':'','device_id':'','hr':'','spo2':'','bp_sys':'','bp_dia':'','rr':'','temp':'','flow':'','source_type':(os.path.splitext(path)[1] or 'text').lstrip('.'),'source_name':os.path.basename(path),'severity':severity,'event':event,'context':context}
    def read_file(self,path):
        low=path.lower();ext=os.path.splitext(path)[1].lower()
        try:
            if low.endswith('.edf.qrs') or ext=='.qrs':return self._read_text(path)
            if ext=='.csv':return self._read_csv(path)
            if ext=='.json':return self._read_json(path)
            if ext in ('.hl7','.msg'):return self._read_hl7(path)
            if ext=='.edf':return self._read_edf(path)
            if ext=='.ods':return self._read_ods(path)
            if ext=='.odt':return self._read_odt(path)
            if ext in ('.rtf','.xml'):return self._read_document(path)
            if ext in ('.dat','.db','.sqlite','.sqlite3'):return self._read_dat_or_db(path)
            return self._read_text(path)
        except Exception as e:return [self._row(path,'ERROR','read failure',str(e))]
    def _read_text(self,path):
        rows=[]
        with open(path,'r',encoding='utf-8',errors='ignore') as f:
            for line in f:
                if line.strip():rows.append(self._row(path,'INFO',line.strip()[:80],line.strip()))
        return rows
    def _read_csv(self,path):
        if pd:
            try:
                df=pd.read_csv(path);return [self._row(path,'INFO','CSV row',json.dumps({c:(None if pd.isna(r[c]) else r[c]) for c in df.columns},default=str)) for _,r in df.iterrows()]
            except Exception:pass
        with open(path,newline='',encoding='utf-8',errors='ignore') as f:return [self._row(path,'INFO','CSV row',json.dumps(r)) for r in csv.DictReader(f)]
    def _read_json(self,path):
        with open(path,'r',encoding='utf-8') as f:data=json.load(f)
        if isinstance(data,dict) and data.get('resourceType')=='Bundle':
            rows=[]
            for entry in data.get('entry',[]):
                resource=entry.get('resource',{});rows.append(self._row(path,'INFO',f"FHIR {resource.get('resourceType','Resource')}",json.dumps(resource,default=str)))
            return rows
        if isinstance(data,list):return [self._row(path,'INFO','JSON item',json.dumps(x,default=str)) for x in data]
        return [self._row(path,'INFO',f"FHIR {data.get('resourceType','JSON')}" if isinstance(data,dict) else 'JSON',json.dumps(data,default=str))]
    def _read_hl7(self,path):
        text=open(path,'r',encoding='utf-8',errors='ignore').read().replace('\r','\n');return [self._row(path,'INFO','HL7 segment',seg) for seg in text.splitlines() if seg.strip()]
    def _read_edf(self,path):
        if not pyedflib:return [self._row(path,'WARN','EDF dependency missing','Install pyedflib for EDF metadata and signals.')]
        f=pyedflib.EdfReader(path)
        try:
            rows=[self._row(path,'INFO','EDF header',json.dumps(f.getHeader(),default=str))]
            for h in f.getSignalHeaders():rows.append(self._row(path,'INFO','EDF signal',json.dumps(h,default=str)))
            return rows
        finally:f.close()
    def _read_ods(self,path):
        if not pd:return [self._row(path,'WARN','ODS dependency missing','Install pandas and odfpy for ODS support.')]
        df=pd.read_excel(path,engine='odf');return [self._row(path,'INFO','ODS row',json.dumps({c:(None if pd.isna(r[c]) else r[c]) for c in df.columns},default=str)) for _,r in df.iterrows()]
    def _read_odt(self,path):
        if odf_load and odf_text:
            doc=odf_load(path);rows=[]
            for p in doc.getElementsByType(odf_text.P):
                text=''.join(str(n) for n in p.childNodes).strip()
                if text:rows.append(self._row(path,'INFO','ODT text',text))
            return rows
        return self._read_document(path)
    def _read_document(self,path):
        if pypandoc:
            try:
                txt=pypandoc.convert_file(path,'plain');return [self._row(path,'INFO','document text',l.strip()) for l in txt.splitlines() if l.strip()]
            except Exception:pass
        return self._read_text(path)
    def _read_dat_or_db(self,path):
        rows=[]
        try:
            conn=sqlite3.connect(f'file:{os.path.abspath(path)}?mode=ro',uri=True);cur=conn.cursor();cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            for (table,) in cur.fetchall():
                safe=table.replace('"','""')
                try:
                    cur.execute(f'SELECT * FROM "{safe}" LIMIT 2000');names=[d[0] for d in cur.description]
                    for record in cur.fetchall():rows.append(self._row(path,'INFO',f'{table} row',json.dumps(dict(zip(names,record)),default=str)))
                except Exception:pass
            conn.close()
            if rows:return rows
        except Exception:pass
        with open(path,'rb') as f:blob=f.read(65536)
        text=blob.decode('utf-8',errors='ignore')
        if text.strip():return [self._row(path,'INFO','DAT text',line[:4000]) for line in text.splitlines() if line.strip()][:500]
        return [self._row(path,'WARN','binary DAT','Binary file detected; no known parser matched this format.')]
