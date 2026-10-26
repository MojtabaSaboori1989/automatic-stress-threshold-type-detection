# Automatic Stress Threshold and Type Detection

## Configure

Edit only `config.py`:

```python
CASE_NAME = "ARM_Potato"
RUN_MODE = "FULL_DATA"      # FULL_DATA, LOYO, or BOTH
DATA_FILE = r""         # blank = data/combined_nonstandardized_data.xlsx
```

## Run

From CMD opened in this package folder:

```cmd
python run_pipeline.py
```

If Windows does not recognize `python`:

```cmd
py run_pipeline.py
```

