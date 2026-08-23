import datetime as dt
import tkinter as tk
from tkinter import ttk
try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MOK=True
except Exception:MOK=False
class PatientDetail:
    def __init__(self,app):self.app=app
    def open(self,pid):
        win=tk.Toplevel(self.app);win.title(f'CareGrid — {pid}');win.geometry('1100x760');hist=self.app.ds.patient_history(pid);latest=hist[-1] if hist else {};summary=ttk.Frame(win);summary.pack(fill=tk.X,padx=8,pady=8);ttk.Label(summary,text=f'Patient / Bed: {pid}',font=('Segoe UI',15,'bold')).pack(side=tk.LEFT);ttk.Label(summary,text=self.app.alert_mgr.describe(latest)).pack(side=tk.RIGHT)
        if MOK and hist:
            fig=Figure(figsize=(10,5),dpi=100);metrics=[('hr','Heart Rate'),('spo2','SpO₂'),('rr','Resp. Rate'),('temp','Temperature')];recent=hist[-300:];xs=[]
            for r in recent:
                try:xs.append(dt.datetime.fromisoformat(str(r.get('timestamp')).split('.')[0]))
                except Exception:xs.append(dt.datetime.now())
            for i,(key,title) in enumerate(metrics,1):
                ax=fig.add_subplot(4,1,i);vals=[]
                for r in recent:
                    try:vals.append(float(r.get(key)))
                    except Exception:vals.append(float('nan'))
                ax.plot(xs,vals);ax.set_ylabel(title)
            fig.tight_layout();canvas=FigureCanvasTkAgg(fig,master=win);canvas.draw();canvas.get_tk_widget().pack(fill=tk.BOTH,expand=True,padx=8,pady=8)
