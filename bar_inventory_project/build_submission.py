"""Create the review notebook, executive PDF and interview walkthrough from outputs."""
from pathlib import Path
import json
import nbformat as nbf
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT

ROOT = Path(__file__).resolve().parent

def notebook():
    md=nbf.v4.new_markdown_cell; code=nbf.v4.new_code_cell
    cells=[md('''# Hotel bar inventory forecasting and par recommendations
## Krystal Ball assessment
This notebook analyses the supplied transaction CSV, compares four forecasting approaches, recommends stock targets, and tests two inventory policies. All volumes are millilitres unless labelled otherwise. The executed results are included; **Run All** regenerates them.

**Business question:** how much stock should each bar hold for each brand to balance unavailable drinks against excess inventory? No prices or holding-cost rates were supplied, so we report volume and service outcomes, not invented financial savings.'''),
    code('''from pathlib import Path
import sys, json, inspect
import pandas as pd
from IPython.display import display, Image
ROOT = Path.cwd()
if ROOT.name == 'notebooks': ROOT = ROOT.parent
if not (ROOT/'src/inventory.py').exists():
    raise RuntimeError('Open this notebook from bar_inventory_project or its notebooks folder')
sys.path.insert(0, str(ROOT/'src'))
import inventory as inv
pd.set_option('display.max_columns', 12)
raw, daily, y, pairs, audit = inv.prepare(ROOT/'data/raw/bar_inventory_data.csv')
display(pd.Series(audit, name='Data audit'))'''),
    md('''## 1. Data preparation and assumptions
Parse US-style timestamps explicitly. Remove exact duplicate records. Reject missing, nonnumeric, negative or nonfinite required values. Flag row balance differences above 0.02 ml but retain supplied consumption: there is no authoritative replacement. Also audit continuity between each series' consecutive logged balances.

Only observed bar-brand combinations are expanded over the common calendar. **Unlogged days are assumed to have zero consumption**, while missing balances remain missing. This is a strong completeness assumption, not an observation; the `observed` flag preserves the distinction. Items are assumed stocked over the full calendar. Product launch dates, closure calendars and extraction gaps could invalidate this assumption. Zero closing balances with prior positive consumption are stockout proxies, not proof of lost customer demand.

Consumption is fulfilled demand. Demand during a stockout is censored and cannot be recovered from this dataset alone.'''),
    code('''display(raw.loc[raw.balance_flag, ['Date Time Served','Bar Name','Brand Name','balance_error_ml']].head(10))
coverage = daily.groupby('Bar Name').agg(series_days=('observed','size'), observed_days=('observed','sum'), consumption_ml=('demand','sum'))
coverage['coverage_pct'] = 100*coverage.observed_days/coverage.series_days
display(coverage)
display(daily.groupby('observed').agg(days=('demand','size'), mean_consumption_ml=('demand','mean')))
display(daily.loc[daily.stockout_proxy, ['date','Bar Name','Brand Name','closing']].head())'''),
    md('''## 2. EDA and temporal evaluation
ABC classes rank pre-test consumption volume (80% / 95% cumulative boundaries), not monetary value. Explore weekdays rather than assuming that Friday and Saturday are busier.

Use the first 60% of calendar days for training, the next 20% for model selection, and the final 20% for test reporting. Within validation/test, forecast from weekly rolling origins for up to seven days. Every lag and rolling feature is calculated from earlier history within its own series. Multi-day Random Forest predictions are recursive, with no future actuals within a forecast block.

Compare a 14-day mean, weekly seasonal naive, additive weekly Holt-Winters with fixed smoothing coefficients (0.2 level, 0.1 seasonal; not tuned), and pooled Random Forest (60 trees, depth 10, minimum leaf 30). The series index is an identity proxy with an arbitrary ordinal ordering; one-hot or hierarchical encodings are a future improvement. Forest training is fixed within each evaluation segment and refreshed at the test boundary. Model choice uses validation WAPE only. WAPE is undefined when total actual demand is zero; MAE remains usable.'''),
    code('''print(inspect.getsource(inv.features))
print(inspect.getsource(inv.evaluate))
results = inv.run()'''),
    code('''display(results['metrics'].round(4))
display(Image(filename=str(ROOT/'outputs/assessment_overview.png')))
display(pd.read_csv(ROOT/'outputs/abc_classification.csv').head(12))
display(pd.read_csv(ROOT/'outputs/test_metrics_by_series.csv').sort_values('WAPE',ascending=False).head(10))'''),
    md('''## 3. Inventory decision and simulation
At the end of day t, forecast consumption for t+1 through t+L using data available through t. Default supplier lead time L=2 days. **Par = sum of lead-time forecasts + 1.645 × validation RMSE × sqrt(L)**. The RMSE is per series and is frozen before the test. The normal approximation and independent daily errors are simplifications; 1.645 is a nominal 95% one-sided factor, not a guaranteed fill rate.

Each morning receive due orders, fulfil demand, and record lost volume. At day end, compute inventory position = on-hand + on-order, then order max(0, par - inventory position). An order placed at the end of t arrives before demand at t+L. Thus L=1 means next morning and the target covers L future daily demands under this convention. Reorder threshold equals the target (daily order-up-to policy).

Compare an assumed fixed seven-day-mean target with the forecast-and-buffer policy, using identical initial stock and no initial pipeline. This is not a reconstruction of the hotel's undocumented current ordering rules. There is no warm-up exclusion. The same recorded demand stream drives both policies. Previous recorded consumption remains observable in the replay even if a simulated policy would have lost it: this is a historical scenario comparison, not a live censored-feedback experiment.

Orders are continuous ml to isolate the policy. 750 ml bottle rounding appears only in the recommendation export and is not included in the backtest. No expiry, minimum order, capacity, supplier variability or purchasing costs are modelled.'''),
    code('''print(inspect.getsource(inv.simulate))
display(results['policies'].round(3))
display(pd.read_csv(ROOT/'outputs/sensitivity.csv').round(3))'''),
    md('''## 4. Operational recommendations
The CSV below lists historical as-of targets for every bar-brand pair. It is based on the final date in the supplied data, not today's date. Managers must verify actual on-hand and outstanding orders before applying the inventory-position rule. Do not subtract a stale recorded balance to generate a purchase order.

`period_turnover` = total fulfilled test-period volume / mean aggregate closing stock; it is not annualised. A stockout count is a bar-brand-day with positive unmet demand, not a calendar-day total. Inventory levels are a service/holding tradeoff: do not claim both improve unless the results show that.'''),
    code("display(results['recommendations'].round(2).head(16))\nprint('All 96 recommendations: outputs/par_recommendations.csv')"),
    md('''## 5. Deployment, limitations and next steps
Validate logging completeness and stockout censoring before deployment. Reconcile balances with POS/stocktake data. Run a daily pipeline with schema and freshness checks, forecast refresh, and manager-reviewed recommendations. Track forecast errors, service, stock levels, override frequency and actual lead times. Use chronological rolling evaluation when retraining.

First improvements: stock availability and unfulfilled-request logs; bottle sizes and case-pack constraints; actual delivery calendars; promotions, occupancy and holidays; intermittent-demand models and empirical lead-time error quantiles. Stress-test supplier delays and correlated demand. Unknown series need a documented cold-start rule before production.

Source: supplied `Consumption Dataset - Dataset.csv`, copied unchanged under `data/raw/`. Assignment: supplied reference document and screenshot. See the two-page report and four-minute video outline for the managerial summary.''')]
    nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},'language_info':{'name':'python','version':'3.12'}})
    nbf.write(nb,ROOT/'notebooks/inventory_forecasting_solution.ipynb')

def report():
    audit=json.loads((ROOT/'outputs/audit.json').read_text())
    metrics=pd.read_csv(ROOT/'outputs/forecast_metrics.csv')
    policies=pd.read_csv(ROOT/'outputs/policy_metrics.csv')
    winner=audit['selected_model']; test=metrics[metrics.split=='test'].set_index('model')
    fixed,dynamic=policies.iloc[0],policies.iloc[1]
    holding_change=(dynamic.mean_closing_ml_per_series/fixed.mean_closing_ml_per_series-1)*100
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TitleCustom',fontName='Helvetica-Bold',fontSize=24,leading=28,textColor=colors.HexColor('#17364a'),spaceAfter=12))
    styles.add(ParagraphStyle(name='BodyCustom',fontName='Helvetica',fontSize=10,leading=14,spaceAfter=9))
    styles['Heading2'].textColor=colors.HexColor('#167d8d')
    story=[]
    def p(text): story.append(Paragraph(text,styles['BodyCustom']))
    def h(text): story.append(Paragraph(text,styles['Heading2']))
    def table(rows,widths):
        t=Table(rows,colWidths=widths,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#17364a')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#edf4f6'),colors.white])]))
        story.extend([t,Spacer(1,10)])
    story.append(Paragraph('Better stock decisions<br/>for hotel bars',styles['TitleCustom']))
    p(f"Krystal Ball assessment | {audit['start']} to {audit['end']} | 6 bars, 16 brands")
    h('1. Business problem and decision')
    p('Unavailable drinks damage service and sales; excess stock consumes cash and storage. This project estimates daily consumption by bar and brand, translates it into stock targets and compares replenishment outcomes. Prices and cost rates are unavailable, so no financial savings are claimed.')
    h('2. Data quality and assumptions')
    missing=100*audit['missing_series_days']/audit['total_series_days']
    p(f"The source contains {audit['raw_rows']:,} rows and {audit['series']} bar-brand series over {audit['days']} days. {audit['balance_flag_rows']} rows fail the balance equation at a 0.02 ml tolerance (maximum discrepancy {audit['maximum_balance_error_ml']:.2f} ml); consumption is retained and exceptions exported. There are {audit['continuity_flag_rows']:,} consecutive-record balance discontinuities.")
    p(f"{missing:.1f}% of series-days have no log and are assumed zero consumption. Missing closing balances remain unknown. {audit['historical_stockout_proxy_days']} observed zero-closing days with prior demand are stockout proxies, not confirmed lost sales. Recorded consumption understates latent demand during stockouts. Logging completeness is the principal deployment prerequisite.")
    h('3. Model selection and evidence')
    p(f"Chronological 60/20/20 train/validation/test split; weekly rolling origins predict up to seven days without future observations. Validation WAPE selects <b>{winner}</b>. Test starts {audit['test_start']}; it is not used to choose the winner. Forest inputs are past lags, rolling statistics, weekday and series identity. Holt-Winters uses fixed smoothing parameters.")
    table([['Model','Test MAE (ml)','Test WAPE']]+[[m,f'{r.MAE_ml:.1f}',f'{r.WAPE:.1%}'] for m,r in test.iterrows()],[220,130,130])
    p('WAPE is total absolute error divided by total consumption. Even predicting zero everywhere scores 100% WAPE here, beating all four candidates but providing no useful stock coverage. The chosen model is best only among the four candidates. Daily predictive skill is weak; validate logging and test weekly aggregation before a live pilot.')
    story.append(PageBreak())
    story.append(Paragraph('Inventory policy and rollout',styles['TitleCustom']))
    h('4. Simulation performance and tradeoffs')
    p('Default par = next two days of forecast consumption + 1.645 x per-series validation RMSE x sqrt(2). Receive orders before demand; at day end replenish inventory position (on-hand plus on-order) to target. An end-of-day order arrives before demand two days later. Unmet demand is lost. Both policies start with identical seven-day-mean stock and no pipeline.')
    table([['Test-period measure','Fixed 7-day target','Forecast + buffer'],
        ['Stockout bar-brand-days',f'{int(fixed.stockout_series_days):,}',f'{int(dynamic.stockout_series_days):,}'],
        ['Lost volume (litres)',f'{fixed.lost_volume_ml/1000:.1f}',f'{dynamic.lost_volume_ml/1000:.1f}'],
        ['Volume fill rate',f'{fixed.fill_rate:.1%}',f'{dynamic.fill_rate:.1%}'],
        ['Mean closing ml / series',f'{fixed.mean_closing_ml_per_series:.1f}',f'{dynamic.mean_closing_ml_per_series:.1f}'],
        ['Period turnover',f'{fixed.period_turnover:.2f}',f'{dynamic.period_turnover:.2f}']],[220,130,130])
    p(f"The forecast-and-buffer policy changes mean holding stock by {holding_change:+.1f}% and stockout series-days from {int(fixed.stockout_series_days):,} to {int(dynamic.stockout_series_days):,}. The seven-day comparator is an assumed rule, not the hotel's measured current policy. Both replays use the same recorded consumption, so these outcomes do not prove causal savings or recover missing demand.")
    p('The nominal 95% normal factor is not a guaranteed fill rate. Sensitivity results cover 1-3 day lead times and factors 1.282, 1.645 and 2.326. Continuous-ml ordering is simulated; 750 ml bottle rounding is indicative only. No holding-cost optimisation, expiry, case packs, capacity limits or variable delivery times are included.')
    h('5. Production plan and failure modes')
    p('First reconcile inventory records and establish whether missing logs mean no demand. Pilot with manager review: daily ingestion, completeness checks, refreshed forecasts and targets, then actual stock and pipeline checks before ordering. Monitor forecast error, fill rate, stock, delivery delays and manual overrides. Freeze model changes until a chronological backtest passes agreed service and holding thresholds.')
    p('Next add occupancy, promotions and holidays; supplier calendars and lead-time variability; bottle sizes and order constraints; censored-demand estimation; and intermittent-demand alternatives. Correlated errors and supplier delays can make the square-root safety buffer too small. Product launches and closed bars need explicit availability calendars.')
    p(f"All 96 recommendations are historical as of {audit['end']}. They are not current purchase orders. Source: user-supplied Consumption Dataset - Dataset.csv; full methods, audit flags, sensitivity results and reproducible code accompany the notebook.")
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#617582'))
        canvas.drawString(42,25,'KRYSTAL BALL  /  INVENTORY ASSESSMENT')
        canvas.drawRightString(553,25,str(doc.page))
    SimpleDocTemplate(str(ROOT/'report/business_report.pdf'),pagesize=(595,842),rightMargin=42,leftMargin=42,topMargin=35,bottomMargin=40).build(story,onFirstPage=footer,onLaterPages=footer)
    script=f'''# Four-minute video walkthrough

## 0:00-0:35 | Business problem
Show the notebook introduction. Explain stockouts versus money and space tied up in surplus stock. Scope: six bars and 16 brands, 96 series. No cost data means no financial savings estimate.

## 0:35-1:15 | Data and assumptions
Show the audit and coverage tables. Mention {audit['raw_rows']:,} records, {audit['balance_flag_rows']} balance exceptions and {missing:.1f}% unlogged series-days. Explain that zeros are an explicit assumption and recorded sales are censored during stockouts. Keep the raw data unchanged.

## 1:15-2:00 | Forecasting
Show the metrics and weekly-origin code. Explain the 60/20/20 chronological split and why random splitting leaks future information. Compare the four models. Validation chose {winner}; its test WAPE is {test.loc[winner,'WAPE']:.1%}. Explain the weakness of sparse daily demand and why complexity does not guarantee a better forecast.

## 2:00-3:05 | Stock recommendation and simulation
Show the par formula and simulation table. Explain the two-day lead time, safety buffer, on-order inventory and arrival timing. Compare {int(fixed.stockout_series_days):,} versus {int(dynamic.stockout_series_days):,} stockout series-days, {fixed.fill_rate:.1%} versus {dynamic.fill_rate:.1%} fill rate, and {holding_change:+.1f}% holding change. Describe the tradeoff honestly. The fixed comparator is assumed; bottle rounding is not simulated.

## 3:05-4:00 | How managers use it
Show the recommendations CSV. Explain that par is a target, not an order quantity: subtract actual inventory position. Recommendations are historical, as of {audit['end']}. Close with a manager-reviewed pilot, better stock availability logs, real supplier lead times and daily performance monitoring.

## Preparation
- Run the notebook before recording and keep the PDF and tables open.
- Rehearse explaining WAPE, validation versus test, inventory position and lost demand in your own words.
- Record your own screen and voice. This file is an outline, not a recorded presentation.
'''
    (ROOT/'video_script/video_walkthrough_outline.md').write_text(script,encoding='utf-8')

if __name__=='__main__':
    notebook();report()
