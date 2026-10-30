"""Select a CPU-friendly classifier on FFmpeg validation; evaluate QEMU once.

The historical QEMU holdout is never used for model or threshold selection.
Run from the repository root: python ml/train_improved.py
"""
import argparse
import hashlib
import json
import platform
import time
from importlib.metadata import version
from pathlib import Path

import joblib
import numpy as np
import pyarrow.parquet as pq
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score,
                             confusion_matrix, roc_curve,
                             precision_recall_fscore_support, roc_auc_score)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import FeatureUnion, Pipeline


METRICS = ('accuracy', 'precision', 'recall', 'f1', 'roc_auc', 'pr_auc')


def metrics(y, scores, threshold):
    scores = np.asarray(scores)
    predicted = scores >= threshold
    p, r, f, _ = precision_recall_fscore_support(
        y, predicted, average='binary', zero_division=0)
    return dict(accuracy=float(accuracy_score(y, predicted)), precision=float(p),
                recall=float(r), f1=float(f), roc_auc=float(roc_auc_score(y, scores)),
                pr_auc=float(average_precision_score(y, scores)),
                confusion_matrix=confusion_matrix(y, predicted).tolist())


def vectorizer(kind):
    char = TfidfVectorizer(analyzer='char', ngram_range=(3, 5), min_df=2,
                          max_features=50000, sublinear_tf=True)
    if kind == 'char':
        return char
    tokens = TfidfVectorizer(token_pattern=r'[A-Za-z_]\w*|==|!=|<=|>=|->|&&|\|\|',
                            ngram_range=(1, 2), min_df=2, max_features=50000,
                            sublinear_tf=True, lowercase=False)
    return FeatureUnion([('characters', char), ('tokens', tokens)])


def train(directory, output):
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    records = []
    checksums = {}
    for split in ('train', 'validation', 'test'):
        source = Path(directory) / f'{split}.parquet'
        checksums[split] = hashlib.sha256(source.read_bytes()).hexdigest()
        records.extend(pq.read_table(source, columns=['func', 'target', 'project', 'commit_id']).to_pylist())
    duplicates = {}
    for row in records:
        digest = hashlib.sha256(' '.join(row['func'].split()).encode()).hexdigest()
        duplicates.setdefault(digest, []).append(row)
    clean = [rows[0] for rows in duplicates.values()
             if len({r['target'] for r in rows}) == 1
             and len({r['project'] for r in rows}) == 1]
    # Explicit projects reproduce the historical holdout without seed searching.
    training = [r for r in clean if r['project'] == 'FFmpeg']
    test = [r for r in clean if r['project'] == 'qemu']
    assert len(training) == 9666 and len(test) == 17497, 'Unexpected benchmark version'
    x = np.array([r['func'] for r in training])
    y = np.array([int(r['target']) for r in training])
    commits = np.array([r['commit_id'] for r in training])
    inner, validation = next(GroupShuffleSplit(n_splits=1, test_size=.25,
                            random_state=42).split(x, y, commits))
    assert not set(commits[inner]) & set(commits[validation])
    candidates = []
    for kind in ('char', 'char_tokens'):
        features = vectorizer(kind)
        matrix = features.fit_transform(x[inner])
        validation_matrix = features.transform(x[validation])
        for c in (.1, 1., 10.):
            classifier = LogisticRegression(C=c, solver='liblinear', max_iter=1000,
                                             class_weight='balanced', random_state=42)
            classifier.fit(matrix, y[inner])
            scores = classifier.predict_proba(validation_matrix)[:, 1]
            false_positive_rate, true_positive_rate, thresholds = roc_curve(y[validation], scores)
            # Maximize balanced accuracy to penalize an all-positive classifier.
            objective = np.where(np.isfinite(thresholds), true_positive_rate - false_positive_rate, -np.inf)
            threshold = float(thresholds[np.argmax(objective)])
            entry = dict(features=kind, c=c, threshold=threshold,
                         validation=metrics(y[validation], scores, threshold))
            candidates.append(entry)
            print(json.dumps(entry), flush=True)
    # Predeclared selection rule: validation average precision, then F1.
    winner = max(candidates, key=lambda c: (c['validation']['pr_auc'], c['validation']['f1']))
    selection = dict(seed=42, train_project='FFmpeg', test_project='qemu',
                     inner_samples=len(inner), validation_samples=len(validation),
                     inner_commits=len(set(commits[inner])),
                     validation_commits=len(set(commits[validation])),
                     selection_rule='validation PR-AUC, then validation F1; threshold maximizes validation balanced accuracy',
                     parquet_sha256=checksums, candidates=candidates, selected=winner,
                     environment=dict(python=platform.python_version(),
                                      packages={p: version(p) for p in ('scikit-learn', 'numpy', 'joblib', 'pyarrow')}))
    (out / 'selection.json').write_text(json.dumps(selection, indent=2), encoding='utf-8')
    print('Selection locked; fitting full FFmpeg training set.', flush=True)
    model = Pipeline([('features', vectorizer(winner['features'])),
                      ('classifier', LogisticRegression(C=winner['c'], solver='liblinear',
                       max_iter=1000, class_weight='balanced', random_state=42))])
    model.fit(x, y)
    started = time.perf_counter()
    scores = model.predict_proba([r['func'] for r in test])[:, 1]
    elapsed = time.perf_counter() - started
    report = dict(model='devpulse-defect-candidate', version='2.0.0', languages=['c', 'cpp'],
                  seed=42, train_projects=['FFmpeg'], test_projects=['qemu'],
                  train_samples=len(training), test_samples=len(test), calibrated=False,
                  threshold=winner['threshold'], selected_features=winner['features'],
                  selected_c=winner['c'], **metrics([r['target'] for r in test], scores, winner['threshold']),
                  ms_per_function=elapsed / len(test) * 1000,
                  functions_per_second=len(test) / elapsed)
    baseline = json.loads(Path('artifacts/evaluation.json').read_text())
    report['baseline_delta'] = {k: report[k] - baseline[k] for k in METRICS}
    report['all_quality_metrics_improved'] = all(report[k] > baseline[k] for k in METRICS)
    joblib.dump({'model': model, 'metadata': report}, out / 'candidate.joblib')
    report['artifact_bytes'] = (out / 'candidate.joblib').stat().st_size
    (out / 'evaluation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', default='data')
    parser.add_argument('--output', default='artifacts/experiment-v2')
    args = parser.parse_args()
    train(args.data, args.output)
