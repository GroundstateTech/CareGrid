import datetime as dt
import tkinter as tk
from tkinter import ttk
try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MOK=True
except Exception:
    MOK=False

from ui.record_widgets import ToolTip,field,today,now,as_float,SYMPTOMS,BODY,SEVERITY,MEALS,SLEEP,FREQ

class PatientDetail:
    def __init__(self,app):self.app=app

    def _tree(self,parent,cols,height=7):
        t=ttk.Treeview(parent,columns=cols,show='headings',height=height)
        t._reverse={}
        for c in cols:
            t.heading(c,text=c.replace('_',' ').title(),command=lambda cc=c,tt=t:self._sort(tt,cc));t.column(c,width=110,anchor='center');t._reverse[c]=False
        t.pack(fill=tk.BOTH,expand=True,padx=8,pady=6);return t

    def _sort(self,t,col):
        rev=t._reverse.get(col,False)
        def key(iid):
            s=str(t.set(iid,col)).strip()
            try:return (0,float(s))
            except Exception:pass
            for fmt in ('%Y-%m-%d %H:%M','%Y-%m-%d'):
                try:return (1,dt.datetime.strptime(s,fmt))
                except Exception:pass
            return (2,s.lower())
        ids=list(t.get_children(''));ids.sort(key=key,reverse=rev)
        for i,iid in enumerate(ids):t.move(iid,'',i)
        t._reverse[col]=not rev
        for c in t['columns']:
            label=c.replace('_',' ').title()+((' ▼' if rev else ' ▲') if c==col else '')
            t.heading(c,text=label,command=lambda cc=c,tt=t:self._sort(tt,cc))

    def _fill(self,t,rows,cols):
        t.delete(*t.get_children())
        for r in rows:t.insert('','end',values=[r.get(c,'') for c in cols])

    def open(self,pid):
        win=tk.Toplevel(self.app);win.title(f'CareGrid — Patient {pid}');win.geometry('1320x850')
        prof=self.app.patient_records.profile(pid)
        hist=self.app.ds.patient_history(pid);latest=hist[-1] if hist else {}
        top=tk.Frame(win,bg='#123d5a');top.pack(fill=tk.X)
        name=(' '.join(x for x in [prof.get('first_name',''),prof.get('last_name','')] if x).strip() or f'Patient / Bed {pid}')
        tk.Label(top,text=name,bg='#123d5a',fg='white',font=('Segoe UI',16,'bold')).pack(side=tk.LEFT,padx=12,pady=10)
        tk.Label(top,text=f"ID: {pid}    MRN: {prof.get('mrn','')}    DOB: {prof.get('dob','')}",bg='#123d5a',fg='#DDEBF5').pack(side=tk.LEFT,padx=8)
        tk.Label(top,text=self.app.alert_mgr.describe(latest),bg='#123d5a',fg='white',font=('Segoe UI',9,'bold')).pack(side=tk.RIGHT,padx=12)
        banner=tk.Frame(win,bg='#e8f1f6');banner.pack(fill=tk.X)
        alls=self.app.patient_records.rows('allergies',pid);probs=self.app.patient_records.rows('problems',pid)
        active=[r.get('problem','') for r in probs if r.get('status')=='Active'][:4]
        tk.Label(banner,text='Allergies: '+(', '.join(r.get('substance','') for r in alls[:4]) if alls else 'None recorded'),bg='#e8f1f6',fg='#7a1f1f').pack(side=tk.LEFT,padx=12,pady=5)
        tk.Label(banner,text='Active Problems: '+(', '.join(active) if active else 'None recorded'),bg='#e8f1f6',fg='#263845').pack(side=tk.LEFT,padx=12)

        nb=ttk.Notebook(win);nb.pack(fill=tk.BOTH,expand=True,padx=8,pady=8)
        tabs={}
        for n in ['Overview','Live Trends','Record','Problems / Allergies','Medications','Encounters','Timeline','Coverage & Billing','Chart Search']:
            tabs[n]=ttk.Frame(nb);nb.add(tabs[n],text=n)
        self._overview(tabs['Overview'],pid,prof,hist,latest)
        self._trends(tabs['Live Trends'],hist)
        self._record(tabs['Record'],pid)
        self._problems(tabs['Problems / Allergies'],pid)
        self._medications(tabs['Medications'],pid)
        self._encounters(tabs['Encounters'],pid)
        self._timeline(tabs['Timeline'],pid,hist)
        self._coverage(tabs['Coverage & Billing'],pid,prof)
        self._search(tabs['Chart Search'],pid)

    def _overview(self,p,pid,prof,hist,latest):
        outer=tk.Frame(p,bg='white');outer.pack(fill=tk.BOTH,expand=True,padx=10,pady=10)
        left=tk.Frame(outer,bg='white');left.pack(side=tk.LEFT,fill=tk.BOTH,expand=True)
        right=tk.Frame(outer,bg='white');right.pack(side=tk.RIGHT,fill=tk.BOTH,expand=True)
        fields=[('MRN','mrn','Medical Record Number: facility identifier for the patient.'),('First Name','first_name','Patient first name.'),('Last Name','last_name','Patient surname.'),('DOB','dob','Date of birth, preferably YYYY-MM-DD.'),('Sex','sex','Administrative/clinical sex field.'),('Phone','phone','Primary contact number.'),('Email','email','Primary email.'),('Address','address','Street/mailing address.'),('Emergency Contact','emergency_contact','Emergency contact or next of kin.'),('Primary Provider','primary_provider','Primary care provider or responsible clinician.')]
        vars={}
        form=ttk.LabelFrame(left,text='Demographics / Patient Info');form.pack(fill=tk.X,padx=6,pady=6)
        for i,(label,key,tip) in enumerate(fields):
            v=tk.StringVar(value=str(prof.get(key,'') or ''));vars[key]=v;field(form,i,0,label,v,None,tip,32)
        def save():
            data={k:v.get() for k,v in vars.items()};data.update({k:prof.get(k,'') for k in ['insurer','member_id','group_number','policyholder','deductible','oop_max','notes']});self.app.patient_records.upsert_profile(pid,data)
        ttk.Button(form,text='Save Patient Info',command=save).grid(row=len(fields),column=1,sticky='e',padx=6,pady=7)
        summary=ttk.LabelFrame(right,text='Current Snapshot');summary.pack(fill=tk.BOTH,expand=True,padx=6,pady=6)
        lines=[f"Signal records: {len(hist)}",f"Medical events: {len(self.app.patient_records.rows('medical_events',pid))}",f"Medications: {len(self.app.patient_records.rows('medications',pid))}",f"Problems: {len(self.app.patient_records.rows('problems',pid))}",f"Allergies: {len(self.app.patient_records.rows('allergies',pid))}"]
        if latest: lines += ['',self.app.alert_mgr.describe(latest)]
        tk.Label(summary,text='\n'.join(lines),bg='white',fg='#233642',justify='left',anchor='nw',font=('Segoe UI',11)).pack(fill=tk.BOTH,expand=True,padx=12,pady=12)

    def _trends(self,p,hist):
        if not hist:
            ttk.Label(p,text='No live/history data for this patient yet.').pack(padx=20,pady=20);return
        if not MOK:
            ttk.Label(p,text='matplotlib not installed; trend charts unavailable.').pack(padx=20,pady=20);return
        fig=Figure(figsize=(10,6),dpi=100);metrics=[('hr','Heart Rate'),('spo2','SpO₂'),('rr','Resp. Rate'),('temp','Temperature')];recent=hist[-300:];xs=[]
        for r in recent:
            try:xs.append(dt.datetime.fromisoformat(str(r.get('timestamp')).split('.')[0]))
            except Exception:xs.append(dt.datetime.now())
        for i,(key,title) in enumerate(metrics,1):
            ax=fig.add_subplot(4,1,i);vals=[]
            for r in recent:
                try:vals.append(float(r.get(key)))
                except Exception:vals.append(float('nan'))
            ax.plot(xs,vals);ax.set_ylabel(title)
        fig.tight_layout();canvas=FigureCanvasTkAgg(fig,master=p);canvas.draw();canvas.get_tk_widget().pack(fill=tk.BOTH,expand=True,padx=8,pady=8)

    def _record(self,p,pid):
        nb=ttk.Notebook(p);nb.pack(fill=tk.BOTH,expand=True,padx=6,pady=6)
        tabs={n:ttk.Frame(nb) for n in ['Medical Event','Nutrition','Sleep','General Log']}
        for n,f in tabs.items():nb.add(f,text=n)
        self._medical(tabs['Medical Event'],pid);self._nutrition(tabs['Nutrition'],pid);self._sleep(tabs['Sleep'],pid);self._general(tabs['General Log'],pid)

    def _medical(self,p,pid):
        names=[('Date',today(),None,'Date of event.'),('Event Type','Symptom',['Symptom','Pain','Injury','Illness','Other'],'Broad event category.'),('Symptom','Headache',SYMPTOMS,'Primary symptom.'),('Where','Head',BODY,'Body region.'),('Side','N/A',['N/A','Left','Right','Both','Center','Generalized'],'Laterality.'),('Severity','0',SEVERITY,'0=no symptoms, 10=worst imaginable.'),('Feels Like','None',['None','Sharp','Dull','Aching','Burning','Throbbing','Pressure','Tingling','Numbness','Other'],'Quality.'),('Trigger','Unknown',['Unknown','Sleep Loss','Stress','Food','Caffeine','Weather','Medication','Other'],'Possible trigger.'),('Relief','None',['None','Rest','Hydration','Food','Medication','Sleep','Other'],'What helped.')]
        frm=ttk.Frame(p);frm.pack(fill=tk.X,padx=8,pady=6);v={}
        for i,(label,default,choices,tip) in enumerate(names):
            var=tk.StringVar(value=default);v[label]=var;r,c=divmod(i,3);field(frm,r,c,label,var,choices,tip)
        text=tk.Text(p,height=7,wrap='word');text.pack(fill=tk.X,padx=8,pady=4)
        tree=self._tree(p,['date','event_type','symptom','body_region','severity','trigger'],6)
        def save():
            self.app.patient_records.insert('medical_events',pid,{'ts':now(),'date':v['Date'].get(),'event_type':v['Event Type'].get(),'symptom':v['Symptom'].get(),'body_region':v['Where'].get(),'side':v['Side'].get(),'severity':v['Severity'].get(),'pain_quality':v['Feels Like'].get(),'onset':'','duration':'','trigger':v['Trigger'].get(),'relief':v['Relief'].get(),'narrative':text.get('1.0','end').strip(),'tags':''});text.delete('1.0','end');self._fill(tree,self.app.patient_records.rows('medical_events',pid),['date','event_type','symptom','body_region','severity','trigger'])
        ttk.Button(p,text='Save Medical Event',command=save).pack(anchor='e',padx=8,pady=4);self._fill(tree,self.app.patient_records.rows('medical_events',pid),['date','event_type','symptom','body_region','severity','trigger'])

    def _nutrition(self,p,pid):
        items=[('Date',today(),None,'Date consumed.'),('Meal Type','Meal',MEALS,'Meal category.'),('Meal','',None,'Food or meal description.'),('Calories','',None,'Calories.'),('Protein','',None,'Protein grams.'),('Carbs','',None,'Carbohydrate grams.'),('Fat','',None,'Fat grams.'),('Water oz','',None,'Water ounces.'),('Caffeine mg','',None,'Caffeine milligrams.'),('Notes','',None,'Additional context.')]
        frm=ttk.Frame(p);frm.pack(fill=tk.X,padx=8,pady=6);v={}
        for i,(label,default,choices,tip) in enumerate(items):
            var=tk.StringVar(value=default);v[label]=var;r,c=divmod(i,2);field(frm,r,c,label,var,choices,tip)
        tree=self._tree(p,['date','meal_type','meal','calories','protein'],7)
        def save():
            self.app.patient_records.insert('nutrition',pid,{'ts':now(),'date':v['Date'].get(),'meal_type':v['Meal Type'].get(),'meal':v['Meal'].get(),'calories':as_float(v['Calories'].get()),'protein':as_float(v['Protein'].get()),'carbs':as_float(v['Carbs'].get()),'fat':as_float(v['Fat'].get()),'fiber':None,'sugar':None,'water_oz':as_float(v['Water oz'].get()),'caffeine_mg':as_float(v['Caffeine mg'].get()),'notes':v['Notes'].get()});self._fill(tree,self.app.patient_records.rows('nutrition',pid),['date','meal_type','meal','calories','protein'])
        ttk.Button(p,text='Save Nutrition',command=save).pack(anchor='e',padx=8,pady=4);self._fill(tree,self.app.patient_records.rows('nutrition',pid),['date','meal_type','meal','calories','protein'])

    def _sleep(self,p,pid):
        items=[('Date',today(),None,'Sleep date.'),('Type','Sleep',SLEEP,'Sleep/rest type.'),('Bedtime','',None,'Start time.'),('Wake Time','',None,'End time.'),('Duration hrs','',None,'Decimal hours.'),('Quality','0',SEVERITY,'Subjective 0-10 quality.'),('Notes','',None,'Sleep notes.')]
        frm=ttk.Frame(p);frm.pack(fill=tk.X,padx=8,pady=6);v={}
        for i,(label,default,choices,tip) in enumerate(items):var=tk.StringVar(value=default);v[label]=var;r,c=divmod(i,2);field(frm,r,c,label,var,choices,tip)
        tree=self._tree(p,['date','session_type','duration_hrs','quality'],7)
        def save():self.app.patient_records.insert('sleep',pid,{'ts':now(),'date':v['Date'].get(),'session_type':v['Type'].get(),'bedtime':v['Bedtime'].get(),'waketime':v['Wake Time'].get(),'duration_hrs':as_float(v['Duration hrs'].get()),'quality':as_float(v['Quality'].get()),'notes':v['Notes'].get()});self._fill(tree,self.app.patient_records.rows('sleep',pid),['date','session_type','duration_hrs','quality'])
        ttk.Button(p,text='Save Sleep',command=save).pack(anchor='e',padx=8,pady=4);self._fill(tree,self.app.patient_records.rows('sleep',pid),['date','session_type','duration_hrs','quality'])

    def _general(self,p,pid):
        frm=ttk.Frame(p);frm.pack(fill=tk.X,padx=8,pady=6);date=tk.StringVar(value=today());kind=tk.StringVar(value='Personal');title=tk.StringVar();tags=tk.StringVar();field(frm,0,0,'Date',date,None,'Log date.');field(frm,0,1,'Type',kind,['Personal','Mood','Cognition','Observation','Work/Project','Other'],'Log category.');field(frm,1,0,'Title',title,None,'Short title.');field(frm,1,1,'Tags',tags,None,'Search keywords.')
        text=tk.Text(p,height=10,wrap='word');text.pack(fill=tk.BOTH,expand=True,padx=8,pady=4);tree=self._tree(p,['date','log_type','title','tags'],5)
        def save():self.app.patient_records.insert('general_logs',pid,{'ts':now(),'date':date.get(),'log_type':kind.get(),'title':title.get(),'narrative':text.get('1.0','end').strip(),'tags':tags.get()});text.delete('1.0','end');self._fill(tree,self.app.patient_records.rows('general_logs',pid),['date','log_type','title','tags'])
        ttk.Button(p,text='Save General Log',command=save).pack(anchor='e',padx=8,pady=4);self._fill(tree,self.app.patient_records.rows('general_logs',pid),['date','log_type','title','tags'])

    def _problems(self,p,pid):
        nb=ttk.Notebook(p);nb.pack(fill=tk.BOTH,expand=True,padx=6,pady=6);pf=ttk.Frame(nb);af=ttk.Frame(nb);nb.add(pf,text='Problems');nb.add(af,text='Allergies')
        frm=ttk.Frame(pf);frm.pack(fill=tk.X,padx=8,pady=6);prob=tk.StringVar();status=tk.StringVar(value='Active');onset=tk.StringVar();code=tk.StringVar();notes=tk.StringVar();field(frm,0,0,'Problem',prob,None,'Diagnosis/problem name.');field(frm,0,1,'Status',status,['Active','Resolved','Inactive','Historical'],'Problem status.');field(frm,1,0,'Onset Date',onset,None,'Onset/diagnosis date.');field(frm,1,1,'Code',code,None,'Optional ICD/SNOMED/local code.');field(frm,2,0,'Notes',notes,None,'Clinical notes.')
        pt=self._tree(pf,['problem','status','onset_date','code'],7)
        def savep():self.app.patient_records.insert('problems',pid,{'problem':prob.get(),'status':status.get(),'onset_date':onset.get(),'code':code.get(),'notes':notes.get()});self._fill(pt,self.app.patient_records.rows('problems',pid),['problem','status','onset_date','code'])
        ttk.Button(pf,text='Add Problem',command=savep).pack(anchor='e',padx=8);self._fill(pt,self.app.patient_records.rows('problems',pid),['problem','status','onset_date','code'])
        frm=ttk.Frame(af);frm.pack(fill=tk.X,padx=8,pady=6);sub=tk.StringVar();reaction=tk.StringVar();sev=tk.StringVar(value='Unknown');ast=tk.StringVar(value='Active');an=tk.StringVar();field(frm,0,0,'Substance',sub,None,'Medication, food or other allergen.');field(frm,0,1,'Reaction',reaction,None,'Observed reaction.');field(frm,1,0,'Severity',sev,['Mild','Moderate','Severe','Unknown'],'Reaction severity.');field(frm,1,1,'Status',ast,['Active','Inactive','Resolved','Unknown'],'Allergy status.');field(frm,2,0,'Notes',an,None,'Additional allergy context.')
        at=self._tree(af,['substance','reaction','severity','status'],7)
        def savea():self.app.patient_records.insert('allergies',pid,{'substance':sub.get(),'reaction':reaction.get(),'severity':sev.get(),'status':ast.get(),'notes':an.get()});self._fill(at,self.app.patient_records.rows('allergies',pid),['substance','reaction','severity','status'])
        ttk.Button(af,text='Add Allergy',command=savea).pack(anchor='e',padx=8);self._fill(at,self.app.patient_records.rows('allergies',pid),['substance','reaction','severity','status'])

    def _medications(self,p,pid):
        frm=ttk.Frame(p);frm.pack(fill=tk.X,padx=8,pady=6);vals={}
        items=[('Date',today(),None,'Record date.'),('Name','',None,'Medication name.'),('Dose','',None,'Dose/strength.'),('Route','Oral',['Oral','IV','IM','Subcutaneous','Topical','Inhaled','Other'],'Administration route.'),('Frequency','Daily',FREQ,'Frequency.'),('Reason','',None,'Indication.'),('Prescriber','',None,'Prescribing clinician.'),('Status','Active',['Active','Completed','Held','Discontinued','PRN','Historical'],'Medication status.'),('Notes','',None,'Medication notes.')]
        for i,(label,default,choices,tip) in enumerate(items):var=tk.StringVar(value=default);vals[label]=var;r,c=divmod(i,2);field(frm,r,c,label,var,choices,tip)
        t=self._tree(p,['date','name','dose','route','frequency','prescriber','status'],8)
        def save():self.app.patient_records.insert('medications',pid,{'ts':now(),'date':vals['Date'].get(),'name':vals['Name'].get(),'dose':vals['Dose'].get(),'route':vals['Route'].get(),'frequency':vals['Frequency'].get(),'reason':vals['Reason'].get(),'prescriber':vals['Prescriber'].get(),'status':vals['Status'].get(),'notes':vals['Notes'].get()});self._fill(t,self.app.patient_records.rows('medications',pid),['date','name','dose','route','frequency','prescriber','status'])
        ttk.Button(p,text='Add Medication',command=save).pack(anchor='e',padx=8);self._fill(t,self.app.patient_records.rows('medications',pid),['date','name','dose','route','frequency','prescriber','status'])

    def _encounters(self,p,pid):
        frm=ttk.Frame(p);frm.pack(fill=tk.X,padx=8,pady=6);vals={};items=[('Encounter Date',today(),None,'Encounter date.'),('Type','Office Visit',['Office Visit','Emergency','Urgent Care','Inpatient','Observation','Telehealth','Procedure','Other'],'Encounter type.'),('Provider','',None,'Responsible provider.'),('Reason','',None,'Reason/chief complaint.'),('Assessment','',None,'Assessment summary.'),('Plan','',None,'Plan.'),('Status','Complete',['Scheduled','Checked In','In Progress','Complete','Cancelled'],'Encounter status.')]
        for i,(label,default,choices,tip) in enumerate(items):var=tk.StringVar(value=default);vals[label]=var;r,c=divmod(i,2);field(frm,r,c,label,var,choices,tip)
        t=self._tree(p,['encounter_date','encounter_type','provider','reason','status'],8)
        def save():self.app.patient_records.insert('encounters',pid,{'encounter_date':vals['Encounter Date'].get(),'encounter_type':vals['Type'].get(),'provider':vals['Provider'].get(),'reason':vals['Reason'].get(),'assessment':vals['Assessment'].get(),'plan':vals['Plan'].get(),'status':vals['Status'].get()});self._fill(t,self.app.patient_records.rows('encounters',pid),['encounter_date','encounter_type','provider','reason','status'])
        ttk.Button(p,text='Save Encounter',command=save).pack(anchor='e',padx=8);self._fill(t,self.app.patient_records.rows('encounters',pid),['encounter_date','encounter_type','provider','reason','status'])

    def _timeline(self,p,pid,hist):
        text=tk.Text(p,wrap='word');text.pack(fill=tk.BOTH,expand=True,padx=8,pady=8);events=[]
        for r in hist[-500:]:events.append((str(r.get('timestamp','')),'Signal',f"HR {r.get('hr','')} | SpO₂ {r.get('spo2','')} | RR {r.get('rr','')} | Temp {r.get('temp','')}"))
        specs=[('medical_events','date','Medical','symptom'),('nutrition','date','Nutrition','meal'),('sleep','date','Sleep','session_type'),('medications','date','Medication','name'),('encounters','encounter_date','Encounter','reason'),('general_logs','date','Log','title')]
        for table,datecol,label,desc in specs:
            for r in self.app.patient_records.rows(table,pid):events.append((str(r.get(datecol,'')),label,str(r.get(desc,''))))
        events.sort(reverse=True)
        text.insert('1.0','\n\n'.join(f'{d} — {kind}\n  {desc}' for d,kind,desc in events) if events else 'No timeline data.');text.config(state='disabled')

    def _coverage(self,p,pid,prof):
        nb=ttk.Notebook(p);nb.pack(fill=tk.BOTH,expand=True,padx=6,pady=6);ins=ttk.Frame(nb);bill=ttk.Frame(nb);nb.add(ins,text='Insurance');nb.add(bill,text='Billing')
        vars={};frm=ttk.Frame(ins);frm.pack(fill=tk.X,padx=8,pady=8);items=[('Insurer','insurer','Insurance company/payer.'),('Member ID','member_id','Insurance member/subscriber ID.'),('Group Number','group_number','Plan/group identifier.'),('Policyholder','policyholder','Primary policyholder.'),('Deductible','deductible','Plan deductible.'),('OOP Max','oop_max','Out-of-pocket maximum.'),('Notes','notes','Coverage notes.')]
        for i,(label,key,tip) in enumerate(items):var=tk.StringVar(value=str(prof.get(key,'') or ''));vars[key]=var;r,c=divmod(i,2);field(frm,r,c,label,var,None,tip,28)
        def savei():
            data=self.app.patient_records.profile(pid);data.update({k:v.get() for k,v in vars.items()});self.app.patient_records.upsert_profile(pid,data)
        ttk.Button(ins,text='Save Coverage',command=savei).pack(anchor='e',padx=8,pady=4)
        vals={};frm=ttk.Frame(bill);frm.pack(fill=tk.X,padx=8,pady=6);items=[('Service Date',today(),None,'Date of service.'),('Provider','',None,'Billing provider/facility.'),('Description','',None,'Charge/claim description.'),('Billed','',None,'Gross billed amount.'),('Insurance Paid','',None,'Amount paid by insurer.'),('Patient Responsibility','',None,'Amount assigned to patient.'),('Paid','',None,'Patient amount paid.'),('Status','Outstanding',['Outstanding','Partial','Paid','Appeal','Denied','Other'],'Billing status.'),('Notes','',None,'Billing notes.')]
        for i,(label,default,choices,tip) in enumerate(items):var=tk.StringVar(value=default);vals[label]=var;r,c=divmod(i,2);field(frm,r,c,label,var,choices,tip)
        t=self._tree(bill,['service_date','provider','description','billed','insurance_paid','patient_responsibility','status'],7)
        def saveb():self.app.patient_records.insert('billing',pid,{'service_date':vals['Service Date'].get(),'provider':vals['Provider'].get(),'description':vals['Description'].get(),'billed':as_float(vals['Billed'].get()),'insurance_paid':as_float(vals['Insurance Paid'].get()),'patient_responsibility':as_float(vals['Patient Responsibility'].get()),'paid':as_float(vals['Paid'].get()),'status':vals['Status'].get(),'notes':vals['Notes'].get()});self._fill(t,self.app.patient_records.rows('billing',pid),['service_date','provider','description','billed','insurance_paid','patient_responsibility','status'])
        ttk.Button(bill,text='Save Billing Entry',command=saveb).pack(anchor='e',padx=8);self._fill(t,self.app.patient_records.rows('billing',pid),['service_date','provider','description','billed','insurance_paid','patient_responsibility','status'])

    def _search(self,p,pid):
        bar=ttk.Frame(p);bar.pack(fill=tk.X,padx=8,pady=8);q=tk.StringVar();entry=ttk.Entry(bar,textvariable=q,width=50);entry.pack(side=tk.LEFT);ToolTip(entry,'Search the entire longitudinal patient chart.');text=tk.Text(p,wrap='word');text.pack(fill=tk.BOTH,expand=True,padx=8,pady=8)
        def run():
            res=self.app.patient_records.search(pid,q.get());lines=[]
            for table,r in res:
                lines.append(f"{table.replace('_',' ').title()} #{r.get('id','')}\n  "+' | '.join(str(v) for k,v in r.items() if k not in ('id','patient_id') and str(v).strip())[:500])
            text.config(state='normal');text.delete('1.0','end');text.insert('1.0','\n\n'.join(lines) if lines else 'No matches.');text.config(state='disabled')
        ttk.Button(bar,text='Search Chart',command=run).pack(side=tk.LEFT,padx=5);entry.bind('<Return>',lambda e:run())
