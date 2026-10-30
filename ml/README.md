# Defect baseline

This is a real trainable scikit-learn TF-IDF + logistic-regression pipeline, not an LLM classifier or a heuristic disguised as ML. No trained model is bundled and no accuracy is claimed.

Install `pip install -r ml/requirements.txt`, then run `python ml/train.py data/devign.jsonl --output artifacts`. Supply legally usable CodeXGLUE/Devign C/C++ function records with `func`, `target`, and `project`. Inspect the upstream data license and provenance before downloading or redistributing. Data is deliberately not committed. Do not train on the landing-page fixtures and claim research performance.

The pipeline normalizes whitespace, removes exact duplicates, rejects conflicting duplicate labels, and holds out entire projects with a fixed seed. It reports accuracy, precision, recall, F1, ROC-AUC, PR-AUC, confusion matrix, latency, throughput and model size. Near-duplicate leakage and dataset label noise remain limitations. A future validation split is required for threshold tuning or calibration. The default threshold is fixed at 0.5; probabilities are explicitly uncalibrated.

Set MODEL_PATH to a trusted artifact and install ML dependencies to enable inference. Joblib deserialization is unsafe for untrusted artifacts; users cannot upload models. This lightweight deployment intentionally excludes PyTorch/CodeBERT fine-tuning. Transformer training and model comparison have not been performed. No model result is shown in the UI until a validated model integration is available.
