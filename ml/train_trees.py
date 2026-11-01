"""Train two additional model families without selecting against QEMU results.

Run from the repository root: python ml/train_trees.py
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
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits

from train_improved import METRICS, metrics, vectorizer


def write(path, value):
    path.write_text(json.dumps(value, indent=2), encoding='utf-8')


def classifier(family, depth):
    cls = RandomForestClassifier if family == 'random_forest' else ExtraTreesClassifier
    return cls(n_estimators=160, max_depth=depth, min_samples_leaf=2,
               max_features='sqrt', class_weight='balanced', n_jobs=2, random_state=42)


def train(directory, output):
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    if (out / 'evaluation.json').exists():
        raise ValueError('Use a new output directory; completed experiments are not overwritten.')
    records, checksums = [], {}
    for split in ('train', 'validation', 'test'):
        source = Path(directory) / f'{split}.parquet'
        checksums[split] = hashlib.sha256(source.read_bytes()).hexdigest()
        records.extend(pq.read_table(source, columns=['func', 'target', 'project', 'commit_id']).to_pylist())
    duplicates = {}
    for row in records:
        digest = hashlib.sha256(' '.join(row['func'].split()).encode()).hexdigest()
        duplicates.setdefault(digest, []).append(row)
    clean = [rows[0] for rows in duplicates.values()
             if len({r['target'] for r in rows}) == 1 and len({r['project'] for r in rows}) == 1]
    training = [r for r in clean if r['project'] == 'FFmpeg']
    test = [r for r in clean if r['project'] == 'qemu']
    assert len(training) == 9666 and len(test) == 17497, 'Unexpected dataset'
    x = np.array([r['func'] for r in training])
    y = np.array([r['target'] for r in training])
    groups = np.array([r['commit_id'] for r in training])
    inner, validation = next(GroupShuffleSplit(n_splits=1, test_size=.25, random_state=42).split(x, y, groups))
    assert not set(groups[inner]) & set(groups[validation])
    print('Preparing character TF-IDF features on inner training data only.', flush=True)
    features = vectorizer('char')
    matrix = features.fit_transform(x[inner])
    valid_matrix = features.transform(x[validation])
    reference = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42)
    reference.fit(matrix, y[inner])
    reference_metrics = metrics(y[validation], reference.predict_proba(valid_matrix)[:, 1], .5)
    print(json.dumps({'validation_baseline': reference_metrics}), flush=True)
    candidates, winners = [], {}
    # Predeclared objective: maximize the worst metric difference from the validation
    # baseline, then average difference. Test metrics never enter this function.
    def objective(result):
        differences = [result[k] - reference_metrics[k] for k in METRICS]
        return min(differences), float(np.mean(differences))
    for family in ('random_forest', 'extra_trees'):
        family_results = []
        for depth in (16, 32, 48):
            print(f'Fitting {family}, depth {depth}.', flush=True)
            started = time.perf_counter()
            model = classifier(family, depth)
            model.fit(matrix, y[inner])
            scores = model.predict_proba(valid_matrix)[:, 1]
            thresholds = np.unique(np.r_[.5, np.quantile(scores, np.linspace(0, 1, 101))])
            evaluations = [(float(t), metrics(y[validation], scores, t)) for t in thresholds]
            threshold, result = max(evaluations, key=lambda item: objective(item[1]))
            entry = dict(family=family, max_depth=depth, threshold=threshold,
                         validation=result, fit_and_selection_seconds=time.perf_counter()-started)
            candidates.append(entry)
            family_results.append(entry)
            print(json.dumps(entry), flush=True)
        winners[family] = max(family_results, key=lambda entry: objective(entry['validation']))
    selection = dict(seed=42, train_project='FFmpeg', test_project='qemu',
                     inner_samples=len(inner), validation_samples=len(validation),
                     inner_commits=len(set(groups[inner])), validation_commits=len(set(groups[validation])),
                     parquet_sha256=checksums, validation_baseline=reference_metrics,
                     selection_rule='Maximize minimum of six metric deltas versus inner-fit baseline; mean delta breaks ties. Thresholds: 101 validation score quantiles plus 0.5.',
                     features='character TF-IDF 3-5 grams, 50000 features; same as baseline',
                     fixed_parameters=dict(n_estimators=160, min_samples_leaf=2, max_features='sqrt', class_weight='balanced', n_jobs=2),
                     candidates=candidates, selected=winners,
                     environment=dict(python=platform.python_version(), packages={p: version(p) for p in ('scikit-learn', 'numpy', 'joblib', 'pyarrow')}))
    write(out/'selection.json', selection)
    print('Both model settings and thresholds locked before QEMU evaluation.', flush=True)
    full_features = vectorizer('char')
    full_matrix = full_features.fit_transform(x)
    models = {}
    for family, winner in winners.items():
        print(f'Fitting final {family} on all FFmpeg samples.', flush=True)
        started = time.perf_counter()
        fitted = classifier(family, winner['max_depth']).fit(full_matrix, y)
        models[family] = (Pipeline([('features', full_features), ('classifier', fitted)]), time.perf_counter()-started)
    baseline = json.loads(Path('artifacts/evaluation.json').read_text())
    reports = {}
    for family, (model, fit_seconds) in models.items():
        print(f'Evaluating locked {family} on QEMU once.', flush=True)
        started = time.perf_counter()
        scores = model.predict_proba([r['func'] for r in test])[:, 1]
        elapsed = time.perf_counter()-started
        result = dict(model=f'devpulse-{family}', version='3.0.0', languages=['c', 'cpp'],
                      train_samples=len(training), test_samples=len(test), train_projects=['FFmpeg'], test_projects=['qemu'],
                      calibrated=False, threshold=winners[family]['threshold'], final_classifier_fit_seconds=fit_seconds,
                      **metrics([r['target'] for r in test], scores, winners[family]['threshold']),
                      ms_per_function=elapsed/len(test)*1000, functions_per_second=len(test)/elapsed)
        result['baseline_delta'] = {k: result[k]-baseline[k] for k in METRICS}
        result['all_quality_metrics_improved'] = all(result[k] > baseline[k] for k in METRICS)
        artifact = out/f'{family}.joblib'
        joblib.dump(dict(model=model, metadata=result), artifact, compress=3)
        result['artifact_bytes'] = artifact.stat().st_size
        # Round-trip the trusted artifact and confirm its prediction interface.
        restored = joblib.load(artifact)
        assert np.allclose(restored['model'].predict_proba([test[0]['func']])[:, 1], scores[:1])
        reports[family] = result
        write(out/f'{family}-evaluation.json', result)
        print(json.dumps(result), flush=True)
    report = dict(selection=selection, baseline=baseline, models=reports,
                  limitation='Historical QEMU results are already known. This is a development comparison, not a fresh independent benchmark. Timing is local and uncontrolled; scores are uncalibrated.')
    write(out/'evaluation.json', report)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', default='data')
    parser.add_argument('--output', default='artifacts/experiment-v3')
    args = parser.parse_args()
    with threadpool_limits(limits=2):
        train(args.data, args.output)
