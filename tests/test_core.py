import os,tempfile
from unittest.mock import patch
from core.normalizer import normalize_row,SCHEMA_FIELDS,DEFAULT_THRESHOLDS
from core.extractor import VitalsExtractor
from core.datastore import DataStore
from core.alerting import AlertManager,Notifier

def test_normalizer_schema():
    row=normalize_row({'patient_id':'A','hr':88,'bp':'120/70'});assert list(row.keys())==SCHEMA_FIELDS;assert row['bp_sys']=='120' and row['bp_dia']=='70'
def test_extractor_text():
    x=VitalsExtractor().from_context('patient=P1 device=MON2 HR=91 SpO2=97 BP=121/75 RR=17 Temp=37.1');assert x['patient_id']=='P1' and x['hr']=='91' and x['spo2']=='97' and x['bp_sys']=='121'
def test_datastore_latest():
    with tempfile.TemporaryDirectory() as td:
        ds=DataStore(os.path.join(td,'x.db'),SCHEMA_FIELDS,10);ds.append_rows([normalize_row({'patient_id':'P1','hr':80})]);assert ds.latest_by_patient()['P1']['hr']=='80'
def test_alert_transition():
    a=AlertManager(DEFAULT_THRESHOLDS,Notifier());row=normalize_row({'patient_id':'P1','spo2':85});assert a.evaluate_and_maybe_alert(row)=='crit';assert len(a.history())==1;a.evaluate_and_maybe_alert(row);assert len(a.history())==1

def test_notifier_uses_argument_safe_command_and_reports_failure():
    notifier=Notifier(command='tool --label "patient one"')
    with patch('core.alerting.subprocess.Popen') as launch:
        assert notifier.alert({'type':'test'}) is True
        launch.assert_called_once_with(['tool','--label','patient one'],shell=False)
    with patch('core.alerting.subprocess.Popen',side_effect=OSError('missing')):
        assert notifier.alert({'type':'test'}) is False
        assert notifier.last_errors == ['command: missing']
