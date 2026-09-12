"""
Optional — if you want to expand beyond the 71 Nowotny odorants using DoOR 2.0,
run this first to avoid double-counting odorants present in both datasets.

Inputs:
    data/nowotny/orn_responses.csv
    data/door/door_response_matrix.csv

Output:
    outputs/door_extra_odorants.csv   -- DoOR odorants NOT already in Nowotny,
                                          safe to add for expanded coverage
"""
import pandas as pd
from pathlib import Path

DATA_N = Path("data/nowotny")
DATA_D = Path("data/door")
OUT = Path("outputs")
OUT.mkdir(exist_ok=True)


def normalize_name(s: str) -> str:
    return s.strip().lower().replace("-", "").replace(" ", "")


if __name__ == "__main__":
    nowotny = pd.read_csv(DATA_N / "orn_responses.csv", index_col=0)
    door = pd.read_csv(DATA_D / "door_response_matrix.csv", index_col=0)

    nowotny_norm = {normalize_name(n) for n in nowotny.index}
    door_norm_map = {normalize_name(n): n for n in door.index}

    overlap = [orig for norm, orig in door_norm_map.items() if norm in nowotny_norm]
    extra = door.loc[[orig for norm, orig in door_norm_map.items() if norm not in nowotny_norm]]

    print(f"DoOR odorants overlapping with Nowotny (excluded to avoid double count): {len(overlap)}")
    print(f"DoOR odorants usable for expansion: {len(extra)}")

    extra.to_csv(OUT / "door_extra_odorants.csv")
