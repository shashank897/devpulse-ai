"""Train a reproducible, project-disjoint TF-IDF defect baseline.
Input JSONL: {"func": str, "target": 0|1, "project": str}.
No dataset is automatically downloaded or redistributed.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score, average_precision_score, confusion_matrix
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline

def train(source, output, seed=42):
    rows=[json.loads(line) for line in Path(source).read_text(encoding='utf-8').splitlines() if line.strip()]
    unique={}
    for row in rows:
        if not row.get('project') or row.get('target') not in (0,1) or not isinstance(row.get('func'),str): raise ValueError('Invalid row: require func, binary target and project.')
        normalized=' '.join(row['func'].split())
        digest=hashlib.sha256(normalized.encode()).hexdigest()
        if digest in unique and unique[digest]['target'] != row['target']: raise ValueError('Conflicting labels for duplicate code.')
        unique.setdefault(digest,row)
    clean=list(unique.values()); groups=np.array([r['project'] for r in clean]); y=np.array([r['target'] for r in clean]); x=np.array([r['func'] for r in clean])
    if len(set(groups))<2: raise ValueError('At least two projects are required for project-disjoint evaluation.')
    train_idx,test_idx=next(GroupShuffleSplit(n_splits=1,test_size=.25,random_state=seed).split(x,y,groups))
    if len(set(y[train_idx]))<2 or len(set(y[test_idx]))<2: raise ValueError('Each split must contain both classes. Supply more projects; do not select a seed by test performance.')
    model=Pipeline([('tfidf',TfidfVectorizer(analyzer='char',ngram_range=(3,5),min_df=2,max_features=50000,sublinear_tf=True)),('classifier',LogisticRegression(max_iter=1000,class_weight='balanced',random_state=seed))])
    model.fit(x[train_idx],y[train_idx]); started=time.perf_counter(); scores=model.predict_proba(x[test_idx])[:,1]; elapsed=time.perf_counter()-started; pred=scores>=.5
    precision,recall,f1,_=precision_recall_fscore_support(y[test_idx],pred,average='binary',zero_division=0)
    report={'model':'devpulse-defect-baseline','version':'1.0.0','languages':['c','cpp'],'seed':seed,'train_projects':sorted(set(groups[train_idx])),'test_projects':sorted(set(groups[test_idx])),'train_samples':len(train_idx),'test_samples':len(test_idx),'exact_duplicates_removed':len(rows)-len(clean),'accuracy':accuracy_score(y[test_idx],pred),'precision':precision,'recall':recall,'f1':f1,'roc_auc':roc_auc_score(y[test_idx],scores),'pr_auc':average_precision_score(y[test_idx],scores),'confusion_matrix':confusion_matrix(y[test_idx],pred).tolist(),'ms_per_function':elapsed/len(test_idx)*1000,'functions_per_second':len(test_idx)/elapsed,'calibrated':False,'threshold':.5,'dataset_sha256':hashlib.sha256(Path(source).read_bytes()).hexdigest()}
    out=Path(output);out.mkdir(parents=True,exist_ok=True);joblib.dump({'model':model,'metadata':report},out/'baseline.joblib');report['artifact_bytes']=(out/'baseline.joblib').stat().st_size;(out/'evaluation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('dataset');parser.add_argument('--output',default='artifacts');parser.add_argument('--seed',type=int,default=42);args=parser.parse_args();train(args.dataset,args.output,args.seed)
