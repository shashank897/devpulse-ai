"""Publish this checkout with the current Git Credential Manager account.
Credentials remain in process memory and are never printed or persisted here.
"""
import json
import subprocess
import urllib.request
import urllib.error

def run(*args): return subprocess.run(args,check=True,capture_output=True,text=True).stdout.strip()
credential=run('git','credential-manager','get') if False else subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',check=True,capture_output=True,text=True).stdout
fields=dict(line.split('=',1) for line in credential.splitlines() if '=' in line)
token=fields.get('password')
if not token: raise SystemExit('No GitHub credential is available. Sign in to GitHub using Git Credential Manager.')
headers={'Authorization':'Bearer '+token,'User-Agent':'DevPulse-Publish','Accept':'application/vnd.github+json'}
def api(path,data=None):
    request=urllib.request.Request('https://api.github.com'+path,data=json.dumps(data).encode() if data else None,headers=headers)
    with urllib.request.urlopen(request,timeout=30) as response: return json.load(response)
account=api('/user')['login']
if account!='shashank897': raise SystemExit('The GitHub credential does not match the connected account.')
try:
    existing=api('/repos/'+account+'/devpulse-ai')
    raise SystemExit('Repository already exists; inspect it before publishing: '+existing['html_url'])
except urllib.error.HTTPError as exc:
    if exc.code!=404: raise
repo=api('/user/repos',{'name':'devpulse-ai','description':'Evidence-first engineering intelligence: code analysis, repository scans, finding triage, and a reproducible defect-classification baseline.','private':False,'auto_init':False})
print('Created repository:',repo['html_url'])
run('git','remote','add','origin',repo['clone_url'])
print(run('git','push','-u','origin','main'))
