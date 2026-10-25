from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
dist = root / "dist"
if dist.exists():
    shutil.rmtree(dist)
shutil.copytree(root / "site", dist)
(dist / "data").mkdir(exist_ok=True)
shutil.copy2(root / "data" / "latest.json", dist / "data" / "latest.json")
(dist / ".nojekyll").touch()
print("Website built:", dist)
