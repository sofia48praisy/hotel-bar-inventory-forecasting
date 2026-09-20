from pathlib import Path
import json, gzip, base64

root=Path('bar_inventory_project')
nb=json.loads((root/'notebooks/inventory_forecasting_solution.ipynb').read_text(encoding='utf-8'))
source=(root/'src/inventory.py').read_text(encoding='utf-8')
data=base64.b64encode(gzip.compress((root/'data/raw/bar_inventory_data.csv').read_bytes())).decode()
setup='''# Standalone submission: includes the unchanged input CSV and implementation.
# Install requirements in your chosen Python environment before Run All:
# pip install pandas numpy matplotlib scikit-learn statsmodels
from pathlib import Path
import sys, json, inspect, gzip, base64
import pandas as pd
from IPython.display import display, Image
ROOT = Path.cwd() / 'krystal_ball_run'
for folder in ['src', 'data/raw', 'data/processed', 'outputs']:
    (ROOT/folder).mkdir(parents=True, exist_ok=True)
'''
setup += 'IMPLEMENTATION = '+repr(source)+'\n'
setup += 'EMBEDDED_CSV_GZIP_BASE64 = '+repr(data)+'\n'
setup += '''(ROOT/'src/inventory.py').write_text(IMPLEMENTATION, encoding='utf-8')
(ROOT/'data/raw/bar_inventory_data.csv').write_bytes(gzip.decompress(base64.b64decode(EMBEDDED_CSV_GZIP_BASE64)))
import importlib.util
spec = importlib.util.spec_from_file_location('inventory', ROOT/'src/inventory.py')
inv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inv)
pd.set_option('display.max_columns', 12)
raw, daily, y, pairs, audit = inv.prepare(ROOT/'data/raw/bar_inventory_data.csv')
display(pd.Series(audit, name='Data audit'))
'''
nb['cells'][1]['source']=setup.splitlines(keepends=True)
nb['cells'][0]['source'].append('\n\n**Single-file submission:** the exact CSV and Python implementation are embedded in the setup cell. Running creates a `krystal_ball_run` folder beside the notebook. No separate source file or dataset download is required. Python dependencies must be installed. Expand the implementation string or review the method listings below.\n')
nb['cells'][-1]['source'].append('\n\n**Observed result:** the 14-day mean was best among four candidates by validation WAPE. On the test set, the policy reduced stockout series-days by 29.2%, improved volume fill rate from 76.5% to 83.2%, and raised average stock by 26.5%. The service improvement comes with more stock; it is not a simultaneous reduction in overstock.\n')
Path('submission').mkdir(exist_ok=True)
Path('submission/inventory_forecasting_standalone.ipynb').write_text(json.dumps(nb,indent=1,ensure_ascii=False),encoding='utf-8')
