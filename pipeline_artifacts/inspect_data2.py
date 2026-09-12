import pandas as pd
import pyreadr

print("=" * 60)
print("A. NOWOTNY WINE CSV (latin-1)")
print("=" * 60)
wine = pd.read_csv("data/nowotny/deBruyne_wineset_OlfCode_Drosophila_2014.csv", encoding="latin-1")
print("Shape:", wine.shape)
print("Columns:", wine.columns.tolist())
print(wine.head(3))

print("\n" + "=" * 60)
print("B. UNIQUE NEURONS")
print("=" * 60)
ind = pd.read_csv("data/nowotny/deBruyne_industrialset_OlfCode_Drosophila_2014.csv")
ind_neurons = sorted(ind["neuron"].unique())
wine_neurons = sorted(wine["neuron"].unique())
print(f"Industrial ({len(ind_neurons)}):", ind_neurons)
print(f"Wine ({len(wine_neurons)}):", wine_neurons)
print(f"Shared: {sorted(set(ind_neurons) & set(wine_neurons))}")

print("\n" + "=" * 60)
print("C. OLFACTORY SUBCLASSES")
print("=" * 60)
cl = pd.read_csv("data/flywire_raw/classification.csv")
olf = cl[cl["class"] == "olfactory"]
print("olfactory sub_class counts:")
print(olf["sub_class"].value_counts())
print("\nsample:")
print(olf.head(10).to_string())

print("\n" + "=" * 60)
print("D. ALPN SUBCLASSES")
print("=" * 60)
alpn = cl[cl["class"] == "ALPN"]
print(alpn["sub_class"].value_counts())

print("\n" + "=" * 60)
print("E. KENYON CELL SUBCLASSES")
print("=" * 60)
kc = cl[cl["class"] == "Kenyon_Cell"]
print(kc["sub_class"].value_counts())

print("\n" + "=" * 60)
print("F. CELL TYPES — ORN entries")
print("=" * 60)
ct = pd.read_csv("data/flywire_raw/consolidated_cell_types.csv")
orn = ct[ct["primary_type"].str.contains("ORN", case=False, na=False)]
print(f"Unique ORN primary_types: {orn['primary_type'].nunique()}")
print(sorted(orn["primary_type"].unique()))
