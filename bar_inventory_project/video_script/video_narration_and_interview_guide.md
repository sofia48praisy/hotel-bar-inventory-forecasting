# Four-minute video narration

Use this as a rehearsal script. Explain the choices in your own words. Keep the notebook open and show the section named at each timestamp.

## 0:00-0:35 - Introduction and business problem

Show: notebook title and data audit.

“This project helps hotel bar managers decide how much of each brand to keep in stock. Too little stock means unavailable drinks and lost sales. Too much ties up money and storage space. My solution takes the supplied inventory records, estimates consumption, recommends a stock target for each bar and brand, and tests the ordering policy against historical consumption.”

## 0:35-1:15 - Data and assumptions

Show: data audit and coverage table.

“The dataset contains 6,575 records for six bars and sixteen brands. I converted timestamps into daily consumption for 96 bar-brand combinations. I checked the equation: opening stock plus purchases minus consumption should equal closing stock. There are 149 inconsistent rows. I flag them and retain the supplied consumption because there is no authoritative corrected value.

“About 81% of bar-brand-days have no record. I assume those days mean zero consumption, but keep an observed flag because missing logs could also explain them. This is the most important assumption to verify before using the system in a real hotel.”

## 1:15-2:00 - Forecasting

Show: model comparison table.

“I compared a fourteen-day average, a seasonal naive model, weekly exponential smoothing and a Random Forest. I split time chronologically: sixty percent training, twenty percent validation and twenty percent test. The model is selected using validation only. Forecasts use earlier observations, so future demand cannot leak into the input features.

“The fourteen-day average had the lowest validation WAPE among these four models. It is also simple to explain and maintain. However, test WAPE is about 167%, so I would not call the forecasts accurate. Even predicting zero has a lower WAPE on this sparse dataset, although that is not a useful stocking policy. I would investigate log completeness and weekly aggregation before live use.”

## 2:00-2:45 - Inventory logic

Show: inventory section and one row of recommendations.

“The par level is a target stock level. I calculate it as the next two days of predicted consumption plus a safety buffer based on validation forecast errors. Two days is an assumed supplier lead time. The factor 1.645 is a nominal normal-distribution service factor, not a guarantee of 95% fulfilment.

“The simulation receives deliveries, serves demand, records shortages and places an order at day end. It subtracts both stock on hand and stock already ordered from the target, which prevents duplicate ordering. Unfulfilled demand is treated as lost sales.”

## 2:45-3:25 - Results and tradeoff

Show: policy metrics table and stock chart.

“Against an assumed fixed seven-day stock rule, stockout instances fell from 527 to 373: about a 29% reduction. These are bar-brand-days, not calendar days. Volume fulfilment improved from 76.5% to 83.2%, and lost volume fell from 92.9 to 66.3 litres.

“The tradeoff is that average stock increased by 26.5%. Therefore, I am showing better service at the cost of more inventory, not claiming that both stockouts and overstock improved. The comparator is an assumed policy, and these are historical simulation outcomes rather than proven business savings.”

## 3:25-4:10 - Real hotel use and improvements

Show: recommendation CSV and conclusion.

“In practice, a daily job would validate the latest transactions, refresh forecasts and suggest stock targets. A manager would review them against live stock, pending orders and supplier schedules before ordering. These recommendations are historical as of January 1st, 2024, not current purchase orders.

“I would next add hotel occupancy, promotions, delivery variability, actual bottle sizes and unfulfilled customer requests. I would monitor missing data, forecast error, fill rate, stock levels and manager overrides. The first priority is trustworthy data, followed by a controlled pilot to choose an acceptable service-versus-stock balance.”

# Quick explanations for follow-up questions

| Question | Plain-language answer |
|---|---|
| What is a time series? | Consumption values ordered by date for one bar and brand. |
| What is the baseline? | A simple reference forecast, here the average of the previous fourteen days. |
| Why chronological splits? | The real system only knows the past. Random splits can let future information influence evaluation. |
| Why not Random Forest? | It had slightly lower test RMSE but worse validation WAPE. I followed the preselected validation criterion instead of choosing retrospectively on the test. |
| What does WAPE measure? | Total absolute forecast error divided by total actual consumption. It can exceed 100% and is undefined if total actual demand is zero. |
| Why is WAPE so high? | Most series-days are zero under the completeness assumption. Positive forecasts create errors on many zero days, and consumption is difficult to predict from the available features. |
| Is a zero forecast better? | On WAPE alone, yes here. That exposes the weakness of daily forecasts and the limits of an absolute-error objective for stock decisions. A stocking policy also needs service and inventory evaluation. |
| What is safety stock? | Extra stock held because actual demand and deliveries may differ from expectations. Here it uses validation RMSE and an assumed lead time. |
| Par versus order quantity? | Par is the target. Order quantity is max(0, par minus on-hand minus outstanding orders). |
| Give a simple example. | A target of 1,200 ml, 300 ml on hand and 450 ml on order implies a 450 ml order before real pack-size constraints. These numbers are illustrative. |
| Is consumption true demand? | Not always. A sold-out item cannot be consumed, so recorded sales may hide unmet demand. |
| Why not calculate financial savings? | The data has no prices, margins or holding costs. Volume and service comparisons are supported; financial savings are not. |
| Is this production-ready? | It is a reproducible assessment prototype. Missing-day assumptions, stock accuracy, supplier timing and order constraints need validation first. |

# Recording checklist

1. Open the executed standalone notebook and report before recording.
2. Practise once and aim for approximately four minutes.
3. Show the audit, model table, policy table and one recommendation. Do not scroll through every line of code.
4. Record your own screen and voice. The form requires a real 3-5 minute video; this text does not replace it.
5. Check that your voice and displayed numbers are understandable and that the final file is below 10 MB. For a four-minute clip, an average total bitrate below about 300 kbps leaves some margin; verify the actual exported size. Use an accepted video format shown by the upload picker.
6. Do not claim 95% achieved fulfilment, high forecast accuracy, financial savings, or lower holding stock. Those claims are not supported by the results.
