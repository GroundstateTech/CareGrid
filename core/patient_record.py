import sqlite3
import datetime as dt
from threading import RLock

class PatientRecordStore:
    """Longitudinal patient information store keyed by existing CareGrid patient_id/bed id.

    Kept separate from DataStore so live signal ingestion remains fast and simple.
    """
    def __init__(self, db_path):
        self.db_path=db_path
        self._lock=RLock()
        self._init_db()

    def _connect(self):
        conn=sqlite3.connect(self.db_path,timeout=5)
        conn.row_factory=sqlite3.Row
        return conn

    def _init_db(self):
        conn=self._connect()
        try:
            conn.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS patient_profile(
                patient_id TEXT PRIMARY KEY,
                mrn TEXT, first_name TEXT, last_name TEXT, dob TEXT, sex TEXT,
                phone TEXT, email TEXT, address TEXT, emergency_contact TEXT,
                primary_provider TEXT, insurer TEXT, member_id TEXT, group_number TEXT,
                policyholder TEXT, deductible REAL, oop_max REAL, notes TEXT,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS medical_events(
                id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id TEXT, ts TEXT, date TEXT,
                event_type TEXT, symptom TEXT, body_region TEXT, side TEXT, severity INTEGER,
                pain_quality TEXT, onset TEXT, duration TEXT, trigger TEXT, relief TEXT,
                narrative TEXT, tags TEXT
            );
            CREATE TABLE IF NOT EXISTS nutrition(
                id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id TEXT, ts TEXT, date TEXT,
                meal_type TEXT, meal TEXT, calories REAL, protein REAL, carbs REAL, fat REAL,
                fiber REAL, sugar REAL, water_oz REAL, caffeine_mg REAL, notes TEXT
            );
            CREATE TABLE IF NOT EXISTS sleep(
                id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id TEXT, ts TEXT, date TEXT,
                session_type TEXT, bedtime TEXT, waketime TEXT, duration_hrs REAL, quality REAL, notes TEXT
            );
            CREATE TABLE IF NOT EXISTS medications(
                id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id TEXT, ts TEXT, date TEXT,
                name TEXT, dose TEXT, route TEXT, frequency TEXT, reason TEXT, prescriber TEXT,
                status TEXT, notes TEXT
            );
            CREATE TABLE IF NOT EXISTS allergies(
                id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id TEXT, substance TEXT,
                reaction TEXT, severity TEXT, status TEXT, notes TEXT
            );
            CREATE TABLE IF NOT EXISTS problems(
                id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id TEXT, problem TEXT,
                status TEXT, onset_date TEXT, code TEXT, notes TEXT
            );
            CREATE TABLE IF NOT EXISTS encounters(
                id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id TEXT, encounter_date TEXT,
                encounter_type TEXT, provider TEXT, reason TEXT, assessment TEXT, plan TEXT, status TEXT
            );
            CREATE TABLE IF NOT EXISTS general_logs(
                id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id TEXT, ts TEXT, date TEXT,
                log_type TEXT, title TEXT, narrative TEXT, tags TEXT
            );
            CREATE TABLE IF NOT EXISTS billing(
                id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id TEXT, service_date TEXT,
                provider TEXT, description TEXT, billed REAL, insurance_paid REAL,
                patient_responsibility REAL, paid REAL, status TEXT, notes TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_medical_events_patient_date ON medical_events(patient_id,date);
            CREATE INDEX IF NOT EXISTS idx_nutrition_patient_date ON nutrition(patient_id,date);
            CREATE INDEX IF NOT EXISTS idx_sleep_patient_date ON sleep(patient_id,date);
            CREATE INDEX IF NOT EXISTS idx_medications_patient_date ON medications(patient_id,date);
            CREATE INDEX IF NOT EXISTS idx_general_logs_patient_date ON general_logs(patient_id,date);
            ''')
            conn.commit()
        finally:
            conn.close()

    def now(self): return dt.datetime.now().strftime('%Y-%m-%d %H:%M')
    def today(self): return dt.date.today().strftime('%Y-%m-%d')

    def profile(self, patient_id):
        conn=self._connect()
        try:
            r=conn.execute('SELECT * FROM patient_profile WHERE patient_id=?',(str(patient_id),)).fetchone()
            return dict(r) if r else {'patient_id':str(patient_id)}
        finally: conn.close()

    def upsert_profile(self, patient_id, fields):
        pid=str(patient_id); now=self.now()
        allowed=['mrn','first_name','last_name','dob','sex','phone','email','address','emergency_contact','primary_provider','insurer','member_id','group_number','policyholder','deductible','oop_max','notes']
        vals=[fields.get(k,'') for k in allowed]
        conn=self._connect()
        try:
            conn.execute(f'''INSERT INTO patient_profile(patient_id,{','.join(allowed)},updated_at)
                VALUES ({','.join(['?']*(len(allowed)+2))})
                ON CONFLICT(patient_id) DO UPDATE SET {','.join([k+'=excluded.'+k for k in allowed])},updated_at=excluded.updated_at''',[pid]+vals+[now])
            conn.commit()
        finally: conn.close()

    def insert(self, table, patient_id, fields):
        allowed={
            'medical_events':['ts','date','event_type','symptom','body_region','side','severity','pain_quality','onset','duration','trigger','relief','narrative','tags'],
            'nutrition':['ts','date','meal_type','meal','calories','protein','carbs','fat','fiber','sugar','water_oz','caffeine_mg','notes'],
            'sleep':['ts','date','session_type','bedtime','waketime','duration_hrs','quality','notes'],
            'medications':['ts','date','name','dose','route','frequency','reason','prescriber','status','notes'],
            'allergies':['substance','reaction','severity','status','notes'],
            'problems':['problem','status','onset_date','code','notes'],
            'encounters':['encounter_date','encounter_type','provider','reason','assessment','plan','status'],
            'general_logs':['ts','date','log_type','title','narrative','tags'],
            'billing':['service_date','provider','description','billed','insurance_paid','patient_responsibility','paid','status','notes'],
        }
        cols=allowed[table]; vals=[fields.get(c,'') for c in cols]
        conn=self._connect()
        try:
            cur=conn.execute(f"INSERT INTO {table}(patient_id,{','.join(cols)}) VALUES ({','.join(['?']*(len(cols)+1))})",[str(patient_id)]+vals)
            conn.commit(); return cur.lastrowid
        finally: conn.close()

    def rows(self, table, patient_id, order='id DESC'):
        conn=self._connect()
        try:
            return [dict(r) for r in conn.execute(f'SELECT * FROM {table} WHERE patient_id=? ORDER BY {order}',(str(patient_id),)).fetchall()]
        finally: conn.close()

    def search(self, patient_id, query):
        q=str(query or '').strip().lower()
        if not q:return []
        specs={
            'medical_events':['event_type','symptom','body_region','trigger','narrative','tags'],
            'nutrition':['meal_type','meal','notes'],
            'sleep':['session_type','notes'],
            'medications':['name','dose','route','frequency','reason','prescriber','status','notes'],
            'allergies':['substance','reaction','severity','status','notes'],
            'problems':['problem','status','code','notes'],
            'encounters':['encounter_type','provider','reason','assessment','plan','status'],
            'general_logs':['log_type','title','narrative','tags'],
            'billing':['provider','description','status','notes'],
        }
        out=[]
        for table,cols in specs.items():
            for r in self.rows(table,patient_id):
                blob=' '.join(str(r.get(c,'')) for c in cols).lower()
                if q in blob: out.append((table,r))
        return out
