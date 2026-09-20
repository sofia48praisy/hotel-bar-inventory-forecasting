# Hotel Bar Inventory Forecasting

An end-to-end Krystal Ball assessment using the supplied consumption dataset. Start with `notebooks/inventory_forecasting_solution.ipynb` and `report/business_report.pdf`.

## Run locally

Python 3.10+ is recommended (tested with 3.12). From this project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python src/inventory.py
python build_submission.py
jupyter lab notebooks/inventory_forecasting_solution.ipynb
```

On macOS/Linux replace activation with `source .venv/bin/activate`. In Jupyter choose the environment's Python kernel and **Run All**. The notebook reruns modelling and produces the result CSVs and chart. `build_submission.py` refreshes the report and video outline from those outputs and creates a fresh, unexecuted notebook, so run it before your final notebook execution. The delivered notebook already includes executed outputs.

## Included files

- `data/raw/bar_inventory_data.csv`: unchanged copy of the supplied CSV.
- `data/processed/daily_bar_consumption.csv`: daily grid, observed flag and stockout proxy.
- `notebooks/inventory_forecasting_solution.ipynb`: narrative, runnable analysis, methods and results.
- `src/inventory.py`: reusable preprocessing, forecasting and simulation implementation.
- `outputs/`: data-quality exceptions, model scores, policy metrics, per-series scores, ABC classes, full simulation logs, lead-time sensitivity, seven-day forecasts and 96 par recommendations.
- `report/business_report.pdf`: two-page managerial report.
- `video_script/video_walkthrough_outline.md`: four-minute presentation plan.
- `tests/test_inventory.py`: delivery timing, pipeline accounting, conservation, zero demand, series separation and grid tests.

## Decisions that matter

1. Explicit US-format timestamps; values remain in ml. Balance discrepancies are flagged rather than silently rewriting consumption.
2. Only bar-brand pairs seen in the source are modelled. Unlogged days are assumed zero consumption. Missing stock balances remain unknown. Coverage is surfaced for review; zero-filling is not proof that the logs are complete.
3. Chronological 60/20/20 split, weekly rolling-origin seven-day forecasts, selection on validation WAPE only. A shared Random Forest is retrained before the test; smoothing uses prior observations only. Final recommendations are trained/refreshed after evaluation.
4. Safety buffer is 1.645 x per-series validation RMSE x sqrt(lead days). This assumes approximately independent errors and does not guarantee 95% fulfilment. The validation errors mix horizons 1-7 and are a pragmatic proxy rather than a calibrated lead-time error distribution.
5. End-of-day daily ordering, arrivals before demand on day t+L, default L=2. Order = max(0, target - on-hand - outstanding orders). Unmet demand is lost. Same initial stock and demand for both policies, no warm-up exclusion.
6. Fixed seven-day stock is an assumed comparator, not a measured incumbent policy. Historical consumed volume is used as demand and understates demand under stockouts. Simulated lost demand does not change the exogenous historical model inputs.
7. Continuous-ml orders are simulated. The 750 ml bottle conversion is illustrative and not backtested. There are no price, case-pack, expiry, capacity or actual supplier constraints in the source.
8. Targets are historical as of the last date of the supplied dataset. They are not current purchase orders. Use live verified inventory position before ordering.

MAE/RMSE units are ml per bar-brand-day; WAPE is a ratio. Stockout counts are bar-brand-days. Holding is mean end-of-day ml per series. Turnover is test-period fulfilled volume divided by mean aggregate closing stock, not annualised. ABC ranks consumption volume, not sales or profit.

## Submission

The full form has separate project, notebook, video and write-up upload fields, each limited to 10 MB. `krystal_ball_submission.zip` in the parent folder bundles the complete project. The parent `submission` folder contains a standalone notebook with embedded data/source and a copy of the report. Confirm supported extensions in the upload picker. The video is required and must be recorded separately; the narration and interview guide under `video_script` help you prepare.

Before your interview, review the missing-day assumption, explain why WAPE can exceed 100%, and distinguish a par target from an order quantity. The test results are reported even if the selected model or policy does not improve every metric.
