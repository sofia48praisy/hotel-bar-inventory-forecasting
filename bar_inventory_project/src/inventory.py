"""Auditable consumption forecasting and periodic-review inventory simulation."""
from pathlib import Path
import json
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from statsmodels.tsa.holtwinters import ExponentialSmoothing

ROOT = Path(__file__).resolve().parents[1]
MODELS = ['mean_14', 'seasonal_naive', 'holt_winters', 'random_forest']

def prepare(path):
    raw = pd.read_csv(path)
    required = ['Date Time Served', 'Bar Name', 'Brand Name', 'Opening Balance (ml)',
                'Purchase (ml)', 'Consumed (ml)', 'Closing Balance (ml)']
    if set(required) - set(raw):
        raise ValueError('Missing required columns')
    if raw[required].isna().any().any():
        raise ValueError('Missing required values; resolve before forecasting')
    d = raw.drop_duplicates().copy()
    d['timestamp'] = pd.to_datetime(d['Date Time Served'], format='%m/%d/%Y %H:%M', errors='raise')
    amounts = required[3:]
    d[amounts] = d[amounts].apply(pd.to_numeric, errors='raise')
    if not np.isfinite(d[amounts]).all().all() or (d[amounts] < 0).any().any():
        raise ValueError('Amounts must be finite and nonnegative')
    d['balance_error_ml'] = d[amounts[0]] + d[amounts[1]] - d[amounts[2]] - d[amounts[3]]
    d['balance_flag'] = d.balance_error_ml.abs() > .02
    d['date'] = d.timestamp.dt.floor('D')
    d = d.sort_values('timestamp', kind='stable')
    keys = ['Bar Name', 'Brand Name']
    d['previous_closing_ml'] = d.groupby(keys)['Closing Balance (ml)'].shift()
    d['continuity_flag'] = (d['Opening Balance (ml)'] - d.previous_closing_ml).abs() > .02
    daily = d.groupby(keys + ['date']).agg(demand=('Consumed (ml)', 'sum'),
        closing=('Closing Balance (ml)', 'last'), rows=('timestamp', 'size')).reset_index()
    pairs = d[keys].drop_duplicates().sort_values(keys).reset_index(drop=True)
    dates = pd.date_range(d.date.min(), d.date.max(), freq='D')
    grid = pairs.merge(pd.DataFrame({'date': dates}), how='cross').merge(daily, on=keys+['date'], how='left')
    grid['observed'] = grid.rows.notna()
    grid['demand'] = grid.demand.fillna(0)
    # Do not fabricate opening/closing balances for days without logs.
    grid['series'] = grid.groupby(keys, sort=True).ngroup()
    grid = grid.sort_values(['series','date'])
    grid['prior_consumption_ml'] = grid.groupby('series').demand.transform(lambda s: s.cumsum().shift(fill_value=0))
    grid['stockout_proxy'] = (grid.closing == 0) & (grid.prior_consumption_ml > 0)
    y = grid.pivot(index='date', columns='series', values='demand').sort_index()
    audit = {'raw_rows': len(raw), 'duplicates_removed': len(raw)-len(d), 'series': len(pairs),
        'days': len(dates), 'start': str(dates[0].date()), 'end': str(dates[-1].date()),
        'balance_flag_rows': int(d.balance_flag.sum()), 'maximum_balance_error_ml': float(d.balance_error_ml.abs().max()),
        'continuity_flag_rows': int(d.continuity_flag.sum()),
        'missing_series_days': int((~grid.observed).sum()), 'total_series_days': len(grid),
        'observed_zero_closing_days': int((grid.closing == 0).sum()),
        'historical_stockout_proxy_days':int(grid.stockout_proxy.sum())}
    return d, grid, y, pairs, audit

def features(history, date):
    # history is time x series; every feature uses strictly earlier observations.
    h = np.asarray(history)
    n = h.shape[1]
    return np.column_stack([np.arange(n), h[-1], h[-7], h[-14], h[-7:].mean(0),
        h[-14:].mean(0), h[-7:].std(0), np.full(n, date.dayofweek)])

def fit_rf(y):
    x = np.vstack([features(y.iloc[:i].values, y.index[i]) for i in range(14, len(y))])
    target = y.iloc[14:].values.ravel()
    return RandomForestRegressor(n_estimators=60, min_samples_leaf=30, max_depth=10,
        random_state=42, n_jobs=-1).fit(x, target)

def forecast(history, dates, model, rf=None):
    h = history.values.copy()
    if model == 'mean_14':
        return np.tile(h[-14:].mean(0), (len(dates), 1))
    if model == 'seasonal_naive':
        return np.array([h[-7 + i % 7] for i in range(len(dates))])
    if model == 'holt_winters':
        results = []
        for j in range(h.shape[1]):
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', RuntimeWarning)
                fit = ExponentialSmoothing(h[:, j], seasonal='add', seasonal_periods=7,
                    initialization_method='estimated').fit(optimized=False,
                    smoothing_level=.2, smoothing_seasonal=.1)
            results.append(np.maximum(0, fit.forecast(len(dates))))
        return np.array(results).T
    predictions = []
    for date in dates:
        p = np.maximum(0, rf.predict(features(h, date)))
        predictions.append(p)
        h = np.vstack([h, p])
    return np.array(predictions)

def evaluate(y, start, end, rf):
    """Weekly origins, seven-day recursive forecasts; no future actuals in a block."""
    predictions = {m: [] for m in MODELS}
    for origin in range(start, end, 7):
        dates = y.index[origin:min(origin+7, end)]
        for model in MODELS:
            predictions[model].append(forecast(y.iloc[:origin], dates, model, rf))
    return {m: np.vstack(p) for m, p in predictions.items()}

def score(actual, predictions, split):
    out = []
    for model, p in predictions.items():
        error = np.asarray(actual)-p
        out.append({'split': split, 'model': model, 'MAE_ml': np.abs(error).mean(),
            'RMSE_ml': np.sqrt((error**2).mean()),
            'WAPE': np.abs(error).sum()/np.asarray(actual).sum() if np.asarray(actual).sum() else np.nan})
    return pd.DataFrame(out)

def simulate(actual, targets, lead_time=2, initial=None):
    """Daily end-of-day review; receive before demand; orders arrive t+L.

    targets[t] covers future days t+1..t+L (L=1 arrives next morning).
    Inventory position includes all outstanding orders. Unmet demand is lost.
    """
    a, targets = np.asarray(actual), np.asarray(targets)
    if lead_time < 1 or a.shape != targets.shape or (a < 0).any() or (targets < 0).any():
        raise ValueError('Invalid simulation input')
    stock = np.array(initial if initial is not None else targets[0], dtype=float).copy()
    if (stock < 0).any():
        raise ValueError('Negative initial stock')
    pending = {}
    records = []
    for t, demand in enumerate(a):
        received = pending.pop(t, np.zeros_like(stock))
        stock += received
        opening = stock.copy()
        served = np.minimum(stock, demand)
        lost = demand-served
        stock -= served
        pipeline = sum(pending.values(), np.zeros_like(stock))
        order = np.maximum(0, targets[t]-stock-pipeline)
        pending[t+lead_time] = pending.get(t+lead_time, np.zeros_like(stock)) + order
        for j in range(len(stock)):
            records.append((t, j, demand[j], received[j], opening[j], served[j], lost[j], stock[j], order[j], targets[t,j]))
    log = pd.DataFrame(records, columns=['day','series','demand','received','opening','served','lost','closing','order','target'])
    holding = log.closing.mean()
    metrics = {'stockout_series_days': int((log.lost>1e-8).sum()), 'lost_volume_ml': log.lost.sum(),
        'fill_rate': log.served.sum()/log.demand.sum() if log.demand.sum() else 1.,
        'mean_closing_ml_per_series': holding,
        'period_turnover': log.served.sum()/(holding*a.shape[1]) if holding else np.nan}
    return log, metrics

def daily_targets(y, start, end, model, rf, rmse, lead_time=2, z=1.645):
    targets = []
    for t in range(start, end):
        # End-of-day actual is available when placing this order.
        dates = pd.date_range(y.index[t]+pd.Timedelta(days=1), periods=lead_time)
        p = forecast(y.iloc[:t+1], dates, model, rf)
        targets.append(p.sum(0) + z*rmse*np.sqrt(lead_time))
    return np.array(targets)

def run():
    out = ROOT/'outputs'; out.mkdir(exist_ok=True)
    raw, daily, y, pairs, audit = prepare(ROOT/'data/raw/bar_inventory_data.csv')
    daily.to_csv(ROOT/'data/processed/daily_bar_consumption.csv', index=False)
    raw.loc[raw.balance_flag | raw.continuity_flag].to_csv(out/'data_quality_flags.csv', index=False)
    n = len(y); train_end = int(n*.6); val_end = int(n*.8)
    print('Training and validation...', flush=True)
    rf = fit_rf(y.iloc[:train_end])
    val = evaluate(y, train_end, val_end, rf)
    val_metrics = score(y.iloc[train_end:val_end], val, 'validation')
    winner = val_metrics.sort_values('WAPE').iloc[0]['model']
    print('Selected:', winner, '; evaluating untouched test period...', flush=True)
    rf_test = fit_rf(y.iloc[:val_end])
    test = evaluate(y, val_end, n, rf_test)
    metrics = pd.concat([val_metrics, score(y.iloc[val_end:], test, 'test')], ignore_index=True)
    metrics.to_csv(out/'forecast_metrics.csv', index=False)
    series_scores = pairs.copy(); series_scores['series'] = range(len(pairs))
    series_error = y.iloc[val_end:].values-test[winner]
    series_scores['MAE_ml'] = np.abs(series_error).mean(0)
    series_scores['WAPE'] = np.divide(np.abs(series_error).sum(0), y.iloc[val_end:].sum().values,
        out=np.full(len(pairs),np.nan), where=y.iloc[val_end:].sum().values>0)
    series_scores.to_csv(out/'test_metrics_by_series.csv',index=False)
    residuals = y.iloc[train_end:val_end].values-val[winner]
    rmse = np.sqrt((residuals**2).mean(0))
    # Both policies receive the same pre-test initial stock; comparator is assumed, not observed.
    initial = y.iloc[:val_end].mean().values*7
    fixed = np.tile(initial, (n-val_end, 1))
    targets = daily_targets(y, val_end, n, winner, rf_test, rmse)
    policy_rows = []; logs = {}
    for label, target in [('Fixed 7-day stock', fixed), ('Forecast + safety stock', targets)]:
        log, metric = simulate(y.iloc[val_end:].values, target, initial=initial)
        logs[label] = log
        log.to_csv(out/('simulation_fixed.csv' if label.startswith('Fixed') else 'simulation_dynamic.csv'), index=False)
        policy_rows.append({'policy': label, **metric})
    policies = pd.DataFrame(policy_rows); policies.to_csv(out/'policy_metrics.csv', index=False)
    sensitivity = []
    for lead in [1,2,3]:
        for z in [1.282,1.645,2.326]:
            st = daily_targets(y, val_end, n, winner, rf_test, rmse, lead, z)
            _, metric = simulate(y.iloc[val_end:].values, st, lead, initial)
            sensitivity.append({'lead_days':lead, 'z':z, **metric})
    pd.DataFrame(sensitivity).to_csv(out/'sensitivity.csv', index=False)
    # Final retraining uses all supplied data only after evaluation is finished.
    rf_final = fit_rf(y) if winner == 'random_forest' else None
    future_dates = pd.date_range(y.index[-1]+pd.Timedelta(days=1), periods=7)
    future = forecast(y, future_dates, winner, rf_final)
    recommendations = pairs.copy(); recommendations['series'] = range(len(pairs))
    recommendations['as_of'] = str(y.index[-1].date())
    recommendations['lead_time_demand_ml'] = future[:2].sum(0)
    recommendations['safety_stock_ml'] = 1.645*rmse*np.sqrt(2)
    recommendations['par_ml'] = recommendations.lead_time_demand_ml+recommendations.safety_stock_ml
    recommendations['par_750ml_bottles'] = np.ceil(recommendations.par_ml/750).astype(int)
    recommendations.to_csv(out/'par_recommendations.csv', index=False)
    pd.DataFrame(future, index=future_dates).rename_axis('date').to_csv(out/'next_7_days_forecast.csv')
    abc = pairs.copy(); abc['consumption_ml'] = y.iloc[:val_end].sum().values
    abc = abc.sort_values('consumption_ml', ascending=False)
    prior_share = (abc.consumption_ml.cumsum()-abc.consumption_ml)/abc.consumption_ml.sum()
    abc['class'] = np.where(prior_share < .8, 'A', np.where(prior_share < .95, 'B', 'C'))
    abc.to_csv(out/'abc_classification.csv', index=False)
    audit.update({'train_end': str(y.index[train_end-1].date()), 'validation_end':str(y.index[val_end-1].date()),
        'test_start':str(y.index[val_end].date()), 'selected_model':winner})
    (out/'audit.json').write_text(json.dumps(audit, indent=2))
    plt.rcParams.update({'font.size':10, 'axes.spines.top':False, 'axes.spines.right':False})
    fig, axes = plt.subplots(2,2,figsize=(12,7), layout='constrained')
    y.sum(axis=1).rolling(7).mean().plot(ax=axes[0,0], color='#167d8d', title='Daily consumption: 7-day mean (ml)')
    axes[0,0].axvline(y.index[val_end], color='#c67732', linestyle='--')
    y.sum(axis=1).groupby(y.index.dayofweek).mean().plot.bar(ax=axes[0,1], color='#167d8d', title='Average total consumption by weekday (ml)')
    axes[0,1].set_xticklabels(['Mon','Tue','Wed','Thu','Fri','Sat','Sun'], rotation=0)
    metrics.pivot(index='model',columns='split',values='WAPE').plot.bar(ax=axes[1,0], title='Forecast WAPE (lower is better)', color=['#167d8d','#bdcbd3'])
    axes[1,0].tick_params(axis='x', rotation=15)
    for label, log in logs.items():
        axes[1,1].plot(y.index[val_end:],log.groupby('day').closing.sum(),label=label)
    axes[1,1].set_title('Simulated total end-of-day stock (ml)'); axes[1,1].legend(fontsize=8)
    axes[1,1].tick_params(axis='x',rotation=20)
    fig.savefig(out/'assessment_overview.png',dpi=140); plt.close(fig)
    print(metrics.to_string(index=False)); print(policies.to_string(index=False))
    return {'audit':audit, 'metrics':metrics, 'policies':policies, 'recommendations':recommendations}

if __name__ == '__main__':
    run()
