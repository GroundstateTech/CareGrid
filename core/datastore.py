import sqlite3
from threading import RLock

class DataStore:
    def __init__(self,db_path,schema_fields,max_rows_in_memory=50000):
        self.db_path=db_path;self.schema_fields=list(schema_fields);self.max_rows=int(max_rows_in_memory);self.rows=[];self._latest={};self._history={};self._lock=RLock();self._init_db()
    def _connect(self):return sqlite3.connect(self.db_path,timeout=5)
    def _init_db(self):
        conn=self._connect()
        try:
            cols=', '.join([f'"{c}" TEXT' for c in self.schema_fields]);conn.execute(f'CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, {cols})');conn.execute('CREATE INDEX IF NOT EXISTS idx_logs_patient_ts ON logs(patient_id, timestamp)');conn.commit()
        finally:conn.close()
    def _offload(self,rows):
        if not rows:return
        conn=self._connect()
        try:
            cols=','.join([f'"{c}"' for c in self.schema_fields]);placeholders=','.join(['?']*len(self.schema_fields));conn.executemany(f'INSERT INTO logs ({cols}) VALUES ({placeholders})',[tuple(r.get(k,'') for k in self.schema_fields) for r in rows]);conn.commit()
        finally:conn.close()
    def append_rows(self,rows):
        if not rows:return
        with self._lock:
            overflow=max(0,len(self.rows)+len(rows)-self.max_rows)
            if overflow:self._offload(self.rows[:overflow]);self.rows=self.rows[overflow:]
            self.rows.extend(rows)
            for row in rows:
                pid=str(row.get('patient_id') or '')
                if not pid:continue
                current=self._latest.get(pid)
                if not current or str(row.get('timestamp',''))>=str(current.get('timestamp','')):self._latest[pid]=row
                hist=self._history.setdefault(pid,[]);hist.append(row)
                if len(hist)>2000:del hist[:-2000]
    def latest_by_patient(self):
        with self._lock:return dict(self._latest)
    def patient_history(self,patient_id):
        with self._lock:return list(self._history.get(str(patient_id),[]))
    def tail(self,limit=200):
        with self._lock:return list(self.rows[-max(0,min(int(limit),10000)):])
    def count(self):
        with self._lock:return len(self.rows)
