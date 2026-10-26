# Automatic Stress Threshold and Type Detection

## Configure
Data preparation:
Before running the workflow, extract the relevant crop data archive
(Maize data.zip, Potato data.zip, or Wheat data.zip) and place the selected
crop-country input file in the data/ folder as:

combined_nonstandardized_data.xlsx

Alternatively, set DATA_FILE in config.py to the full path of the selected input file.


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

