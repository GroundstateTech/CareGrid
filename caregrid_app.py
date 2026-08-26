#!/usr/bin/env python3
import datetime as dt
import os
import queue
import threading

from adapters.file_reader import FileReader
from adapters.hl7_adapter import HL7Server
from adapters.mqtt_adapter import MQTTAdapter
from adapters.sdc_adapter import SDCAdapter
from adapters.serial_adapter import SerialAdapter
from adapters.simulator import SimulatorAdapter
from adapters.syslog_adapter import SyslogAdapter
from core.alerting import AlertManager, Notifier
from core.api import start_rest_api
from core.datastore import DataStore
from core.extractor import VitalsExtractor
from core.normalizer import DEFAULT_THRESHOLDS, SCHEMA_FIELDS, normalize_row
from core.patient_record import PatientRecordStore
from core.settings import Settings
from core.snapshot import Snapshotter
from ui.main_ui import CareGridApp

APP_TITLE='CareGrid — Unified Patient Signal Intelligence'
ROOT=os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH=os.path.join(ROOT,'caregrid_settings.json')
DB_PATH=os.path.join(ROOT,'caregrid_data.db')
PATIENT_RECORD_DB_PATH=os.path.join(ROOT,'caregrid_patient_records.db')
SNAPSHOT_PATH=os.path.join(ROOT,'snapshots')

def main():
    settings=Settings(SETTINGS_PATH).load();thresholds=settings.get('thresholds',DEFAULT_THRESHOLDS)
    ds=DataStore(DB_PATH,SCHEMA_FIELDS,50000);patient_records=PatientRecordStore(PATIENT_RECORD_DB_PATH);extractor=VitalsExtractor();notifier=Notifier(settings.get('webhook',''),settings.get('alarm_command',''));alerts=AlertManager(thresholds,notifier);reader=FileReader();ingest_q=queue.Queue()
    def enqueue_context(ctx):ingest_q.put(('context',ctx))
    adapters={
        'serial':SerialAdapter(enqueue_context,settings.get('serial_port','COM3'),int(settings.get('serial_baud',9600))),
        'mqtt':MQTTAdapter(enqueue_context,settings.get('mqtt_host','localhost'),int(settings.get('mqtt_port',1883)),settings.get('mqtt_topic','caregrid/+/+/vitals')),
        'hl7':HL7Server(enqueue_context,int(settings.get('hl7_port',2575)),settings.get('hl7_host','127.0.0.1')),
        'sdc':SDCAdapter(enqueue_context),
        'syslog':SyslogAdapter(enqueue_context,int(settings.get('syslog_port',5514)),settings.get('syslog_host','127.0.0.1')),
        'simulator':SimulatorAdapter(enqueue_context,float(settings.get('sim_interval',1.0))),
    }
    def process_context(ctx):
        base=normalize_row(ctx);extra=extractor.from_context(base.get('context',''))
        for k,v in extra.items():
            if v and not base.get(k):base[k]=v
        if not base.get('timestamp'):base['timestamp']=dt.datetime.now().isoformat(' ')
        ds.append_rows([base]);alerts.evaluate_and_maybe_alert(base)
    def ingest_files(paths):
        def worker():
            for path in paths:
                for row in reader.read_file(path):process_context(row)
        threading.Thread(target=worker,daemon=True).start()
    running=True
    def ingest_worker():
        while running:
            try:_kind,payload=ingest_q.get(timeout=.5);process_context(payload)
            except queue.Empty:continue
            except Exception as e:print('[CareGrid ingest]',e)
    threading.Thread(target=ingest_worker,daemon=True).start()
    api=None
    try:api=start_rest_api(int(settings.get('api_port',8765)),lambda:list(ds.latest_by_patient().values()),lambda:alerts.history()[-200:],lambda n:ds.tail(n),host=settings.get('api_host','127.0.0.1'))
    except Exception as e:print('[CareGrid API]',e)
    snapshots=Snapshotter(SNAPSHOT_PATH,ds,int(settings.get('snapshot_every_min',15)));snapshots.start()
    app=CareGridApp(APP_TITLE,settings,ds,alerts,notifier,extractor,reader,adapters);app.patient_records=patient_records;app.on_files_selected=ingest_files;app.snapshotter=snapshots
    def apply_settings(cfg):
        for k,v in cfg.items():settings.set(k,v)
        settings.save();alerts.update_thresholds(cfg.get('thresholds',alerts.thresholds));notifier.webhook=cfg.get('webhook','')
        adapters['serial'].port=cfg.get('serial_port',adapters['serial'].port);adapters['serial'].baud=int(cfg.get('serial_baud',adapters['serial'].baud));adapters['mqtt'].host=cfg.get('mqtt_host',adapters['mqtt'].host);adapters['mqtt'].port=int(cfg.get('mqtt_port',adapters['mqtt'].port));adapters['mqtt'].topic=cfg.get('mqtt_topic',adapters['mqtt'].topic);adapters['hl7'].port=int(cfg.get('hl7_port',adapters['hl7'].port));adapters['syslog'].port=int(cfg.get('syslog_port',adapters['syslog'].port))
    app.on_settings_changed=apply_settings
    try:app.mainloop()
    finally:
        running=False;snapshots.stop()
        if api:
            try:api.shutdown();api.server_close()
            except Exception:pass

if __name__=='__main__':main()
