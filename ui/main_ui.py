import csv,os,re,tkinter as tk
from tkinter import ttk,filedialog,messagebox
from core.normalizer import SCHEMA_FIELDS,DEFAULT_THRESHOLDS
from ui import theme
from ui.alerts_panel import AlertsPanel
from ui.devices_panel import DevicesPanel
from ui.logs_panel import LogsPanel
from ui.patient_detail import PatientDetail
from ui.settings_panel import SettingsWindow
from ui.vitals_panel import VitalsPanel
class CareGridApp(tk.Tk):
    def __init__(self,title,settings,datastore,alert_mgr,notifier,extractor,file_reader,adapters):
        super().__init__();self.title(title);self.geometry(settings.get('window_geometry','1660x960'));self.minsize(1200,720);self.configure(bg=theme.BG);self.settings=settings;self.ds=datastore;self.alert_mgr=alert_mgr;self.notifier=notifier;self.extractor=extractor;self.file_reader=file_reader;self.adapters=adapters;self.schema_fields=SCHEMA_FIELDS;self.default_thresholds=DEFAULT_THRESHOLDS;self.on_files_selected=lambda paths:None;self.on_settings_changed=lambda cfg:None;self._watch_folder=settings.get('watch_folder','');self._live=False;self._seen={};self._last_alert_count=0;self._style();self.patient_detail=PatientDetail(self);self.settings_window=SettingsWindow(self);self._build();self.protocol('WM_DELETE_WINDOW',self.close);self.after(500,self._tick)
    def _style(self):
        s=ttk.Style(self)
        try:s.theme_use('clam')
        except Exception:pass
        s.configure('Treeview',background=theme.PANEL,fieldbackground=theme.PANEL,foreground=theme.TEXT,rowheight=28);s.configure('Treeview.Heading',font=('Segoe UI',9,'bold'));s.configure('TButton',padding=6);s.configure('TLabel',background=theme.BG,foreground=theme.TEXT)
    def _build(self):
        self._menu();header=tk.Frame(self,bg=theme.ACCENT_DARK,height=62);header.pack(fill=tk.X);tk.Label(header,text='CAREGRID',bg=theme.ACCENT_DARK,fg='white',font=('Segoe UI',19,'bold')).pack(side=tk.LEFT,padx=(16,8),pady=12);tk.Label(header,text='Unified Patient Signal Intelligence',bg=theme.ACCENT_DARK,fg='#DDEBF5',font=('Segoe UI',10)).pack(side=tk.LEFT,pady=17);self.connection_var=tk.StringVar(value='LOCAL / READY');tk.Label(header,textvariable=self.connection_var,bg=theme.ACCENT_DARK,fg='white',font=('Segoe UI',9,'bold')).pack(side=tk.RIGHT,padx=16)
        self.kpi=tk.Frame(self,bg=theme.BG);self.kpi.pack(fill=tk.X,padx=8,pady=7);self.kpi_vars={}
        for key,label in [('patients','Active Patients'),('critical','Critical'),('warnings','Warnings'),('devices','Connections'),('records','Records')]:
            card=tk.Frame(self.kpi,bg=theme.PANEL,highlightthickness=1,highlightbackground=theme.BORDER);card.pack(side=tk.LEFT,fill=tk.X,expand=True,padx=4);v=tk.StringVar(value='0');self.kpi_vars[key]=v;tk.Label(card,text=label,bg=theme.PANEL,fg=theme.MUTED,font=('Segoe UI',9)).pack(anchor='w',padx=10,pady=(7,0));tk.Label(card,textvariable=v,bg=theme.PANEL,fg=theme.TEXT,font=('Segoe UI',18,'bold')).pack(anchor='w',padx=10,pady=(0,7))
        outer=ttk.PanedWindow(self,orient=tk.VERTICAL);outer.pack(fill=tk.BOTH,expand=True,padx=8,pady=(0,4));top=ttk.PanedWindow(outer,orient=tk.HORIZONTAL);bottom=tk.Frame(outer,bg=theme.PANEL);outer.add(top,weight=4);outer.add(bottom,weight=1);left=ttk.PanedWindow(top,orient=tk.VERTICAL);center=tk.Frame(top,bg=theme.PANEL);right=ttk.PanedWindow(top,orient=tk.VERTICAL);top.add(left,weight=1);top.add(center,weight=3);top.add(right,weight=1);a=tk.Frame(left,bg=theme.PANEL);d=tk.Frame(left,bg=theme.PANEL);left.add(a,weight=2);left.add(d,weight=1);self.alerts_panel=AlertsPanel(self);self.alerts_panel.build(a);self.devices_panel=DevicesPanel(self);self.devices_panel.build(d);self.vitals_panel=VitalsPanel(self);self.vitals_panel.build(center);quick=tk.Frame(right,bg=theme.PANEL);helpbox=tk.Frame(right,bg=theme.PANEL);right.add(quick,weight=1);right.add(helpbox,weight=1);self._build_quick(quick);self._build_help(helpbox);self.logs_panel=LogsPanel(self);self.logs_panel.build(bottom);self._bottom_bar();self.refresh_all()
    def _menu(self):
        bar=tk.Menu(self);fm=tk.Menu(bar,tearoff=False);fm.add_command(label='Add Files…',command=self.add_files);fm.add_command(label='Export Current View…',command=self.export_csv);fm.add_separator();fm.add_command(label='Exit',command=self.close);bar.add_cascade(label='File',menu=fm);vm=tk.Menu(bar,tearoff=False);vm.add_command(label='Settings',command=self.show_settings);bar.add_cascade(label='View',menu=vm);tm=tk.Menu(bar,tearoff=False);tm.add_command(label='Start Demo Simulator',command=lambda:self._start_adapter('simulator'));tm.add_command(label='Stop Demo Simulator',command=lambda:self._stop_adapter('simulator'));tm.add_command(label='Write Snapshot Now',command=self.write_snapshot);bar.add_cascade(label='Tools',menu=tm);self.config(menu=bar)
    def _build_quick(self,parent):
        tk.Label(parent,text='Quick Actions',bg=theme.HEADER,fg=theme.TEXT,font=('Segoe UI',10,'bold')).pack(fill=tk.X);body=tk.Frame(parent,bg=theme.PANEL);body.pack(fill=tk.BOTH,expand=True,padx=8,pady=8);ttk.Button(body,text='Add Files',command=self.add_files).pack(fill=tk.X,pady=3);self.live_btn=ttk.Button(body,text='Start Watch Folder',command=self.toggle_live);self.live_btn.pack(fill=tk.X,pady=3);ttk.Button(body,text='Settings',command=self.show_settings).pack(fill=tk.X,pady=3);ttk.Button(body,text='Open Selected Patient Chart',command=self.open_selected_patient).pack(fill=tk.X,pady=3);ttk.Button(body,text='Silence 2 min',command=lambda:self.silence(120)).pack(fill=tk.X,pady=3);ttk.Button(body,text='Acknowledge All',command=self.ack_all).pack(fill=tk.X,pady=3)
    def _build_help(self,parent):
        tk.Label(parent,text='At a Glance',bg=theme.HEADER,fg=theme.TEXT,font=('Segoe UI',10,'bold')).pack(fill=tk.X);self.glance=tk.StringVar(value='No patient data yet.\nUse Demo Simulator or Add Files.');tk.Label(parent,textvariable=self.glance,bg=theme.PANEL,fg=theme.TEXT,justify='left',anchor='nw',wraplength=320,font=('Segoe UI',10)).pack(fill=tk.BOTH,expand=True,padx=10,pady=10)
    def _bottom_bar(self):
        b=tk.Frame(self,bg=theme.HEADER);b.pack(fill=tk.X);ttk.Label(b,text='Search:').pack(side=tk.LEFT,padx=(8,4),pady=5);self.search=tk.StringVar();e=ttk.Entry(b,textvariable=self.search,width=42);e.pack(side=tk.LEFT);e.bind('<Return>',lambda e:self.refresh_all());ttk.Button(b,text='Apply',command=self.refresh_all).pack(side=tk.LEFT,padx=3);ttk.Button(b,text='Clear',command=self.clear_search).pack(side=tk.LEFT);self.status=tk.StringVar(value='Ready');ttk.Label(b,textvariable=self.status).pack(side=tk.RIGHT,padx=10)
    def _filtered(self):
        rows=self.ds.tail(5000);pat=self.search.get().strip()
        if not pat:return rows
        try:rx=re.compile(pat,re.I)
        except Exception:return rows
        return [r for r in rows if any(rx.search(str(r.get(k,''))) for k in ('patient_id','device_id','device_type','event','context','source_name'))]
    def refresh_all(self):
        self.vitals_panel.refresh();self.alerts_panel.refresh();self.devices_panel.refresh();self.logs_panel.refresh(self._filtered());latest=self.ds.latest_by_patient();statuses=[self.alert_mgr.evaluate_status(r) for r in latest.values()];self.kpi_vars['patients'].set(str(len(latest)));self.kpi_vars['critical'].set(str(statuses.count('crit')));self.kpi_vars['warnings'].set(str(statuses.count('warn')));self.kpi_vars['devices'].set(str(sum(1 for a in self.adapters.values() if getattr(a,'running',False))));self.kpi_vars['records'].set(str(self.ds.count()));crit=[pid for pid,r in latest.items() if self.alert_mgr.evaluate_status(r)=='crit'];warn=[pid for pid,r in latest.items() if self.alert_mgr.evaluate_status(r)=='warn'];self.glance.set(('CRITICAL: '+', '.join(crit[:6])+'\n' if crit else 'No critical patients.\n')+('Warnings: '+', '.join(warn[:6]) if warn else 'No active warnings.'))
    def _tick(self):
        try:self.refresh_all();self._popup_new_alerts();self._poll_watch()
        except Exception as e:self.status.set(f'UI warning: {e}')
        self.after(750,self._tick)
    def _popup_new_alerts(self):
        hist=self.alert_mgr.history()
        if len(hist)>self._last_alert_count:
            newest=hist[-1];self._last_alert_count=len(hist);win=tk.Toplevel(self);win.title('CareGrid — Critical Alert');win.configure(bg=theme.CRIT2);win.attributes('-topmost',True);tk.Label(win,text='CRITICAL PATIENT ALERT',bg=theme.CRIT2,fg='white',font=('Segoe UI',16,'bold')).pack(fill=tk.X,padx=18,pady=(14,4));tk.Label(win,text=f"Patient / Bed: {newest.get('patient') or 'Unknown'}\n{newest.get('summary','')}",bg=theme.CRIT2,fg='white',font=('Segoe UI',11),justify='left').pack(fill=tk.X,padx=18,pady=10);ttk.Button(win,text='Acknowledge',command=win.destroy).pack(pady=(0,14))
        else:self._last_alert_count=len(hist)
    def add_files(self):
        paths=filedialog.askopenfilenames(title='Add clinical logs / data',filetypes=[('Supported data','*.csv *.json *.hl7 *.msg *.edf *.qrs *.ods *.odt *.rtf *.xml *.dat *.db *.sqlite *.txt *.log'),('All files','*.*')]);
        if paths:self.on_files_selected(list(paths));self.status.set(f'Importing {len(paths)} file(s)…')
    def export_csv(self):
        rows=self._filtered()
        if not rows:messagebox.showinfo('Export','No data to export.');return
        path=filedialog.asksaveasfilename(defaultextension='.csv',filetypes=[('CSV','*.csv')]);
        if not path:return
        with open(path,'w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=self.schema_fields);w.writeheader();w.writerows(rows)
        self.status.set(f'Exported {len(rows)} records.')
    def clear_search(self):self.search.set('');self.refresh_all()
    def show_settings(self):self.settings_window.show()
    def apply_settings(self,cfg):self.on_settings_changed(cfg);self._watch_folder=cfg.get('watch_folder',self._watch_folder);self.notifier.webhook=cfg.get('webhook','');self.status.set('Settings applied.')
    def silence(self,seconds):self.alert_mgr.silence_for(seconds);self.status.set(f'Alarm sound silenced for {seconds//60} min.')
    def ack_all(self):self.alert_mgr.acknowledge_all();self.alerts_panel.refresh();self.status.set('Alerts acknowledged.')
    def _start_adapter(self,name):
        a=self.adapters.get(name)
        if a:
            try:a.start();self.status.set(f'{name} started.')
            except Exception as e:messagebox.showerror('Connection',str(e))
    def _stop_adapter(self,name):
        a=self.adapters.get(name)
        if a:a.stop();self.status.set(f'{name} stopped.')
    def toggle_live(self):self._live=not self._live;self.live_btn.config(text='Stop Watch Folder' if self._live else 'Start Watch Folder');self.status.set('Watch folder active.' if self._live else 'Watch folder stopped.')
    def _poll_watch(self):
        if not self._live or not self._watch_folder or not os.path.isdir(self._watch_folder):return
        for name in os.listdir(self._watch_folder):
            path=os.path.join(self._watch_folder,name)
            if not os.path.isfile(path):continue
            try:key=(path,os.path.getsize(path),os.path.getmtime(path))
            except Exception:continue
            old=self._seen.get(path)
            if old!=key:self._seen[path]=key;self.on_files_selected([path])
    def open_selected_patient(self):
        iid=self.vitals_panel.tree.focus()
        if iid:
            values=self.vitals_panel.tree.item(iid,'values')
            if values:self.patient_detail.open(values[0])
    def write_snapshot(self):
        if hasattr(self,'snapshotter'):self.snapshotter.write_snapshot();self.status.set('Snapshot written.')
    def close(self):
        try:self.settings.set('window_geometry',self.geometry());self.settings.save()
        except Exception:pass
        for a in self.adapters.values():
            try:a.stop()
            except Exception:pass
        self.destroy()
