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

from scripts.market import mnav_signal

def test_mnav_single_fresh_reading_is_actionable():
    now=datetime(2026,10,25,12,tzinfo=timezone.utc)
    item={"value":1.18,"date":"2026-10-25","freshness":"fresh"}
    result=mnav_signal([["2026-10-25",1.18]],item,now)
    assert result["status"]=="clear"
    assert result["label"]=="溢價未偏高"
    assert "18%" in result["evidence"]
    assert "走勢" in result["detail"]

def test_mnav_missing_is_not_false_clear():
    now=datetime(2026,10,25,12,tzinfo=timezone.utc)
    result=mnav_signal([],{"value":None,"freshness":"missing"},now)
    assert result["status"]=="unknown"

def test_mnav_high_premium_warns_without_trend():
    now=datetime(2026,10,25,12,tzinfo=timezone.utc)
    result=mnav_signal([["2026-10-25",1.65]],{"value":1.65,"date":"2026-10-25","freshness":"fresh"},now)
    assert result["status"]=="watch"
    assert result["label"]=="溢價偏高"
