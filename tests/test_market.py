from datetime import datetime, timezone
from scripts.market import merge, ratio, weekly, metric
def test_merge():
    assert merge([["2026-01-01",10]],[["2026-01-01",12]])==[["2026-01-01",12.0]]
def test_ratio_does_not_use_future_btc():
    assert ratio([["2026-01-03",100]],[["2026-01-02",50],["2026-01-03",100]])==[["2026-01-03",2.0]]
def test_weekly_ignores_unfinished_sunday():
    now=datetime(2026,10,25,12,tzinfo=timezone.utc)
    assert weekly([["2026-10-18",123],["2026-10-25",999]],now,1)==(123.0,"2026-10-18")
def test_missing_is_not_fresh():
    now=datetime(2026,10,25,12,tzinfo=timezone.utc)
    assert metric([],"test",2,now)["freshness"]=="missing"
