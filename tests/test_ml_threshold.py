import numpy as np
import pytest
from backend import ml


@pytest.mark.parametrize('score,threshold,expected', [
    (.45, .4, 'elevated_defect_signal'),
    (.35, .4, 'low_defect_signal'),
    (.4, .4, 'elevated_defect_signal'),
    (.45, None, 'low_defect_signal'),
])
def test_prediction_respects_artifact_threshold(monkeypatch, score, threshold, expected):
    class Classifier:
        def predict_proba(self, code):
            return np.array([[1 - score, score]])
    metadata = {'model': 'test', 'version': 'test'}
    if threshold is not None:
        metadata['threshold'] = threshold
    monkeypatch.setattr(ml, 'load_model', lambda path: {'model': Classifier(), 'metadata': metadata})
    result = ml.predict_code('int f() { return 1; }', 'unused')
    assert result['prediction'] == expected
    assert result['threshold'] == (.5 if threshold is None else threshold)
    assert result['calibrated_probability'] is None
