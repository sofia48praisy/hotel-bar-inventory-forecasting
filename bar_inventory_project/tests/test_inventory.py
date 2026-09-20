import sys
from pathlib import Path
import unittest
import tempfile
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from inventory import simulate, features, prepare, forecast

class InventoryTests(unittest.TestCase):
    def test_delivery_timing_and_pipeline(self):
        log, m = simulate(np.array([[5.],[5.],[5.],[5.]]), np.full((4,1),10.), 2, [5.])
        np.testing.assert_allclose(log.received, [0,0,10,0])
        np.testing.assert_allclose(log.order, [10,0,5,5])
        self.assertEqual(m['lost_volume_ml'],5)

    def test_conservation(self):
        rng = np.random.default_rng(5)
        log, _ = simulate(rng.uniform(0,10,(30,3)), np.full((30,3),15), 3)
        np.testing.assert_allclose(log.opening-log.served, log.closing)
        np.testing.assert_allclose(log.served+log.lost, log.demand)
        self.assertTrue((log.closing>=0).all())

    def test_no_demand(self):
        log, metrics = simulate(np.zeros((5,2)),np.zeros((5,2)))
        self.assertEqual(metrics['fill_rate'],1)
        self.assertEqual(log.order.sum(),0)

    def test_series_features_do_not_mix(self):
        h = np.tile([1.,100.],(20,1))
        f = features(h,pd.Timestamp('2023-01-01'))
        np.testing.assert_allclose(f[:,4],[1,100])
        np.testing.assert_allclose(f[:,6],0)

    def test_forecast_uses_history_only(self):
        h = pd.DataFrame(np.arange(42).reshape(21,2))
        p = forecast(h,pd.date_range('2023-01-01',periods=8),'seasonal_naive')
        np.testing.assert_array_equal(p[0],p[7])
        np.testing.assert_array_equal(p[0],h.iloc[-7])

    def test_grid_does_not_invent_pairs(self):
        d = pd.DataFrame({'Date Time Served':['1/1/2023 10:00','1/3/2023 10:00'],
            'Bar Name':['A','B'],'Brand Name':['X','Y'],'Opening Balance (ml)':[10,10],
            'Purchase (ml)':[0,0],'Consumed (ml)':[2,3],'Closing Balance (ml)':[8,7]})
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'data.csv';d.to_csv(path,index=False)
            _, grid, y, _, audit=prepare(path)
        self.assertEqual(y.shape,(3,2))
        self.assertEqual(audit['missing_series_days'],4)
        self.assertEqual(grid.closing.isna().sum(),4)

if __name__=='__main__':
    unittest.main()
