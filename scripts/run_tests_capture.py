import subprocess
import sys
from pathlib import Path

cwd = Path(__file__).resolve().parent.parent
outfile = cwd / "test_output.txt"

result = subprocess.run([sys.executable, "-m", "pytest", "-vv"], cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
with outfile.open("w", encoding="utf-8") as f:
    f.write(result.stdout)
print(f"Wrote test output to {outfile}")
sys.exit(result.returncode)
