# Four-minute video walkthrough

## 0:00-0:35 | Business problem
Show the notebook introduction. Explain stockouts versus money and space tied up in surplus stock. Scope: six bars and 16 brands, 96 series. No cost data means no financial savings estimate.

## 0:35-1:15 | Data and assumptions
Show the audit and coverage tables. Mention 6,575 records, 149 balance exceptions and 81.3% unlogged series-days. Explain that zeros are an explicit assumption and recorded sales are censored during stockouts. Keep the raw data unchanged.

## 1:15-2:00 | Forecasting
Show the metrics and weekly-origin code. Explain the 60/20/20 chronological split and why random splitting leaks future information. Compare the four models. Validation chose mean_14; its test WAPE is 167.3%. Explain the weakness of sparse daily demand and why complexity does not guarantee a better forecast.

## 2:00-3:05 | Stock recommendation and simulation
Show the par formula and simulation table. Explain the two-day lead time, safety buffer, on-order inventory and arrival timing. Compare 527 versus 373 stockout series-days, 76.5% versus 83.2% fill rate, and +26.5% holding change. Describe the tradeoff honestly. The fixed comparator is assumed; bottle rounding is not simulated.

## 3:05-4:00 | How managers use it
Show the recommendations CSV. Explain that par is a target, not an order quantity: subtract actual inventory position. Recommendations are historical, as of 2024-01-01. Close with a manager-reviewed pilot, better stock availability logs, real supplier lead times and daily performance monitoring.

## Preparation
- Run the notebook before recording and keep the PDF and tables open.
- Rehearse explaining WAPE, validation versus test, inventory position and lost demand in your own words.
- Record your own screen and voice. This file is an outline, not a recorded presentation.
