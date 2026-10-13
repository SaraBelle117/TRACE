import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src" / "trace" / "io"))
from thrashing_to_csv import thrash_rate

fps, window_s, hz = 15.0, 10.0, 1.5  # 1.5 Hz -> expect 90 thrashes/min
t = np.arange(0, 60, 1 / fps)
got = thrash_rate(pd.Series(np.sin(2 * np.pi * hz * t + 0.3)), fps, window_s).median()
print(f"expected {hz * 60:.1f}, got {got:.1f} thrashes/min")
assert abs(got - hz * 60) < 2, "FAILED"
print("passed")