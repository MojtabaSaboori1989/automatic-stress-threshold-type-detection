# Automatic Stress Threshold and Type Detection

## Configure

Edit only `config.py`:

```python
CASE\_NAME = "ARM\_Potato"
RUN\_MODE = "FULL\_DATA"      # FULL\_DATA, LOYO, or BOTH
DATA\_FILE = r""         # blank = data/combined\_nonstandardized\_data.xlsx
```

## Run

From CMD opened in this package folder:

```cmd
python run\_pipeline.py
```

If Windows does not recognize `python`:

```cmd
py run\_pipeline.py
```

## Main output folders

```text
results/<CASE\_NAME>/00\_full\_data\_preprocessing/
results/<CASE\_NAME>/01\_yield\_classes/
results/<CASE\_NAME>/02\_standardization/
results/<CASE\_NAME>/03\_thresholds\_and\_signature/
results/<CASE\_NAME>/04\_stress\_types\_and\_evaluation/
```

F1 retains the automatic density plot `full\_data\_automatic\_STa.png`. F2 retains
its detailed prediction/vote/diagnostic outputs and the complete
`<CASE>\_alignment\_results\_with\_metrics.xlsx` workbook with alignment summaries,
per-year tables, stress types, dominant stress types, STa summary and classification
metrics.

All generated preprocessing artifacts (correlation matrices, heatmap, standardized/
non-standardized UPDATED files, shortlist/drop audit, and preprocessing audit) are
written under `00\_full\_data\_preprocessing/`. The input workbook itself is read only,
so F1 no longer leaves generated files beside the raw data.

For `FULL\_DATA` and `BOTH`, F2 always creates the old-style complete workbook in
`04\_stress\_types\_and\_evaluation/` with these 11 sheets: Class Counts, Per-Year (Sh),
Per-Year (All), Alignment Summary, Per Class Accuracy, Overall Accuracy, Data with
Alignment, Sh class\_Metrics, Classification Report, Dominant stress types, and STa Summary.

