# Hotel Bar Inventory Forecasting

Krystal Ball assessment: forecast consumption for each bar and brand, recommend inventory targets, and simulate replenishment performance.

## Start here

- [Standalone executed notebook](submission/inventory_forecasting_standalone.ipynb): includes the dataset and implementation for single-file review.
- [Two-page business report](submission/business_report.pdf).
- [Project setup and methodology](bar_inventory_project/README.md).
- [Python implementation](bar_inventory_project/src/inventory.py) and [tests](bar_inventory_project/tests/test_inventory.py).
- [Presentation narration and interview guide](bar_inventory_project/video_script/video_narration_and_interview_guide.md).

## Findings

The supplied dataset contains 6,575 records across six bars and sixteen brands. Among four candidates, the fourteen-day mean achieved the lowest validation WAPE. Daily forecasting accuracy remains weak; missing transaction days are assumed to represent zero consumption and require validation.

Compared with an assumed fixed seven-day stock policy, the proposed policy reduced simulated stockout bar-brand-days from 527 to 373 and increased volume fulfilment from 76.5% to 83.2%. Average stock increased by 26.5%. These results demonstrate a service-versus-inventory tradeoff, not simultaneous improvement in both outcomes or proven financial savings.

## Run

See the [project README](bar_inventory_project/README.md) for environment setup and commands. The standalone notebook can run separately after installing its listed Python dependencies. It creates a `krystal_ball_run` directory beside the notebook.

Six unit tests passed, and both delivered notebooks were executed without cell errors. Recommendations are historical as of January 1, 2024. This is an assessment prototype, not a live ordering system.
