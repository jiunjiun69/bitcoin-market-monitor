"""Checks browser JavaScript syntax before any Pages publication (Node provided by runner)."""
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_frontend_javascript_syntax():
    script=ROOT/"site"/"app.js"
    result=subprocess.run(["node","--check",str(script)],capture_output=True,text=True)
    assert result.returncode==0, result.stderr
