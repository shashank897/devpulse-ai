import os
import tempfile
import time
import pytest
from concurrent.futures import ThreadPoolExecutor
os.environ['DATABASE_URL']='sqlite:///'+os.path.join(tempfile.mkdtemp(),'test.db').replace('\\','/')
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture(autouse=True)
def fresh_worker(monkeypatch):
    # Each TestClient lifespan shuts down its worker, so each test gets its own.
    from backend import main
    worker=ThreadPoolExecutor(max_workers=1)
    monkeypatch.setattr(main,'executor',worker)
    yield
    worker.shutdown(wait=True)

def wait_scan(client, scan_id):
    for _ in range(100):
        data=client.get('/api/v1/scans/'+scan_id).json()
        if data['status'] in ('completed','failed'): return data
        time.sleep(.02)
    raise AssertionError('Scan did not complete')

def test_scan_session_triage_exports_and_deletion():
    with TestClient(app) as client:
        assert client.get('/api/v1/health').status_code==200
        result=client.post('/api/v1/scans',json={'code':'eval(user)','language':'python'})
        assert result.status_code==202
        scan_id=result.json()['id']; scan=wait_scan(client,scan_id)
        assert scan['status']=='completed' and scan['findings']
        outsider=TestClient(app)
        assert outsider.get('/api/v1/scans/'+scan_id).status_code==404
        assert outsider.get('/api/v1/scans/'+scan_id+'/export').status_code==404
        finding_id=scan['findings'][0]['id']
        assert outsider.patch(f'/api/v1/scans/{scan_id}/findings/{finding_id}',json={'status':'resolved'}).status_code==404
        assert client.patch(f'/api/v1/scans/{scan_id}/findings/{finding_id}',json={'status':'confirmed'}).status_code==200
        assert client.get('/api/v1/scans/'+scan_id+'/export?format=sarif').json()['version']=='2.1.0'
        assert client.post('/api/v1/explain',json={'scan_id':scan_id,'finding_id':finding_id}).status_code==422
        assert client.post('/api/v1/explain',json={'scan_id':scan_id,'finding_id':finding_id,'consent':True}).json()['source']=='rule-guidance'
        assert client.post('/api/v1/scans',json={'code':'eval(x)'},headers={'Origin':'https://evil.example'}).status_code==403
        assert client.post('/api/v1/scans',json={'code':''}).status_code==422
        assert client.delete('/api/v1/scans').status_code==200
        assert client.get('/api/v1/scans').json()==[]

def test_code_preview_is_explicit_and_does_not_create_scan_history():
    source='import sqlite3\nconnection=sqlite3.connect(":memory:")\nquery=f"SELECT * FROM users WHERE name = \'{username}\'"\nconnection.execute(query)'
    with TestClient(app) as client:
        result=client.post('/api/v1/optimize-preview',json={'language':'python','category':'security','code':source})
        assert result.status_code==200
        assert 'connection.execute(query, query_params)' in result.json()['suggestions'][0]['code']
        assert client.get('/api/v1/scans').json()==[]
        assert client.post('/api/v1/optimize-preview',json={'language':'python','category':'security','code':'x'*100001}).status_code==422

def test_trained_ml_endpoint(monkeypatch):
    from pathlib import Path
    from backend.ml import load_model
    load_model.cache_clear()
    monkeypatch.setenv('MODEL_PATH',str(Path('artifacts/baseline.joblib').resolve()))
    with TestClient(app) as client:
        result=client.post('/api/v1/ml/predict',json={'language':'c','code':'int f(char *p) { return p[0]; }'})
        assert result.status_code==200
        body=result.json()
        assert body['model_name']=='devpulse-extra_trees'
        assert body['model_version']=='3.0.0'
        assert abs(body['threshold']-0.5042610664824371)<1e-10
        assert body['calibrated_probability'] is None
        assert body['prediction'] in ('low_defect_signal','elevated_defect_signal')
        assert client.post('/api/v1/ml/predict',json={'language':'python','code':'print(1)'}).status_code==422
    load_model.cache_clear()


def test_delete_one_scan_is_owned_and_preserves_other_history():
    with TestClient(app) as client:
        first=client.post('/api/v1/scans',json={'code':'eval(user)','language':'python'}).json()['id']
        second=client.post('/api/v1/scans',json={'code':'print(1)','language':'python'}).json()['id']
        assert wait_scan(client,first)['status']=='completed'
        assert wait_scan(client,second)['status']=='completed'
        outsider=TestClient(app)
        assert outsider.delete('/api/v1/scans/'+first).status_code==404
        assert client.delete('/api/v1/scans/'+first).status_code==200
        assert client.get('/api/v1/scans/'+first).status_code==404
        assert client.get('/api/v1/scans/'+second).status_code==200
        assert client.delete('/api/v1/scans/'+first).status_code==404


def test_active_scan_cannot_be_deleted_and_failure_keeps_repository(monkeypatch):
    from backend import main
    jobs=[]
    monkeypatch.setattr(main.executor,'submit',lambda *args: jobs.append(args))
    with TestClient(app) as client:
        response=client.post('/api/v1/scans',json={'repository':'owner/repo'})
        scan_id=response.json()['id']
        assert client.delete('/api/v1/scans/'+scan_id).status_code==409
        assert client.get('/api/v1/scans/'+scan_id).json()['repository']=='owner/repo'
        def failure(_):
            raise ValueError('Repository download failed')
        monkeypatch.setattr(main,'repository_files',failure)
        fn,*args=jobs.pop()
        fn(*args)
        failed=client.get('/api/v1/scans/'+scan_id).json()
        assert failed['status']=='failed' and failed['repository']=='owner/repo'
        assert client.delete('/api/v1/scans/'+scan_id).status_code==200
