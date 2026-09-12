import pyreadr
import pandas as pd

base = "data/door_raw/DoOR_data-v2_0_0/Dahaniel-DoOR.data-6436660/data/"
maps = pyreadr.read_r(base + "DoOR.mappings.RData")
df = list(maps.values())[0]

print("Columns:", df.columns.tolist())
print("\nAll rows where OSN is one of our 20 sensilla codes:")
our_osns = ['ab1A','ab1B','ab1C','ab1D','ab2A','ab2B','ab3A','ab3B',
            'ab4A','ab4B','ab5A','ab5B','ab7A','ab7B','ab8A','ab8B',
            'pb1A','pb1B','pb3A','pb3B']

subset = df[df["OSN"].isin(our_osns)]
print(subset[["receptor", "sensillum", "OSN", "code", "code.OSN"]].to_string())

print("\n" + "=" * 60)
print("Full columns preview (first 5 rows, all columns)")
print("=" * 60)
print(df.head().to_string())
