# Datasets for DevPulse AI

Sources checked on 2026-10-31. The current classifier predicts a C/C++ function-level defect signal. Code completion, bug repair and vulnerability classification require different labels; generic source-code collections do not supply these labels automatically.

| Dataset | Where to obtain it | Use in this project |
| --- | --- | --- |
| CodeXGLUE / Devign | [Microsoft task and original download](https://github.com/microsoft/CodeXGLUE/tree/main/Code-Code/Defect-detection), [Hugging Face parquet files](https://huggingface.co/datasets/google/code_x_glue_cc_defect_detection/tree/main/data) | Already downloaded locally. 27,318 C/C++ functions, binary labels, FFmpeg/QEMU project names and commit IDs. Used for the baseline and v2 comparison. The dataset card specifies C-UDA. |
| PrimeVul | [Authors' repository and release download](https://github.com/DLVulDet/PrimeVul#-primevul-dataset) | Candidate for the next, broader training benchmark. Authors describe approximately 7,000 vulnerable and 229,000 benign functions, deduplication, chronological splits and vulnerable/patched pairs. Preserve its splits and inspect source overlap before combining it with Devign. Not downloaded or used in this experiment. |
| IBM D2A | [IBM repository and dataset download instructions](https://github.com/IBM/D2A#downloading-the-d2a-dataset-and-the-splits) | Additional real code labeled using differential static analysis. Useful as a separate benchmark; its automatically produced labels have different assumptions. Not downloaded or used in this experiment. |

Check each dataset's data-use terms and the licenses of the underlying source projects before redistribution. A repository's software license does not establish identical terms for every included code sample. Downloaded source code remains in the ignored `data/` directory.

## Reproduce the current experiment

From the repository directory, using the project Python environment:

```powershell
python -m pip install -r ml/requirements.txt -r ml/requirements-data.txt
python ml/train_improved.py --data data --output artifacts/experiment-v2
```

If the parquet files are missing, obtain `train`, `validation`, and `test` from the Hugging Face files link above and save them as `data/train.parquet`, `data/validation.parquet`, and `data/test.parquet`. The existing `ml/README.md` provides direct download commands.

The experiment retains the historical FFmpeg training / QEMU test boundary. It removes exact whitespace-normalized duplicates and conflicting duplicate labels, then holds out FFmpeg commits for validation. Six character/token TF-IDF logistic-regression configurations are compared using validation average precision (PR-AUC), with validation F1 as a tie breaker. The decision threshold maximizes validation balanced accuracy, which weights detection and specificity equally. An initial validation-only F1 threshold trial was stopped before test evaluation because it flagged almost every validation function. The chosen model is refitted on FFmpeg, then evaluated once on QEMU. `selection.json` records all validation results and input checksums; `evaluation.json` records the final metrics and differences from the deployed baseline.

These are cross-project results and cannot be compared directly with published scores on CodeXGLUE's original random split. Threshold adjustment can exchange precision for recall; it cannot improve ROC-AUC or PR-AUC by itself. More data and training do not guarantee every metric will improve. Near duplicates, imperfect labels, a single validation project and previously observed historical test results remain limitations. Independent future evaluation is needed before security use.
