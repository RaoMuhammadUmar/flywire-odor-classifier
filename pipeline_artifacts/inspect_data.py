import pandas as pd
import pyreadr

print("=" * 60)
print("1. CELL TYPES - primary_type distribution")
print("=" * 60)
ct = pd.read_csv("data/flywire_raw/consolidated_cell_types.csv")
print("Shape:", ct.shape)
print("\nTop 30 primary_type values:")
print(ct["primary_type"].value_counts().head(30))

print("\n" + "=" * 60)
print("2. CLASSIFICATION - super_class distribution")
print("=" * 60)
cl = pd.read_csv("data/flywire_raw/classification.csv")
print("Shape:", cl.shape)
print("\nsuper_class counts:")
print(cl["super_class"].value_counts())
print("\nclass counts:")
print(cl["class"].value_counts())
print("\nsub_class counts (top 20):")
print(cl["sub_class"].value_counts().head(20))

print("\n" + "=" * 60)
print("3. NOWOTNY INDUSTRIAL CSV")
print("=" * 60)
ind = pd.read_csv("data/nowotny/deBruyne_industrialset_OlfCode_Drosophila_2014.csv")
print("Shape:", ind.shape)
print("Columns:", ind.columns.tolist())
print("\nFirst row:")
print(ind.iloc[0].to_dict())

print("\n" + "=" * 60)
print("4. NOWOTNY WINE CSV")
print("=" * 60)
wine = pd.read_csv("data/nowotny/deBruyne_wineset_OlfCode_Drosophila_2014.csv")
print("Shape:", wine.shape)
print("Columns:", wine.columns.tolist())
print("\nFirst row:")
print(wine.iloc[0].to_dict())

print("\n" + "=" * 60)
print("5. DOOR RESPONSE MATRIX")
print("=" * 60)
base = "data/door_raw/DoOR_data-v2_0_0/Dahaniel-DoOR.data-6436660/data/"
door = list(pyreadr.read_r(base + "response.matrix_non.normalized.RData").values())[0]
print("Shape:", door.shape)
print("\nFirst 10 odorant index values:")
print(door.index[:10].tolist())
print("\nFirst 10 receptor columns:")
print(door.columns[:10].tolist())

print("\n" + "=" * 60)
print("6. DOOR AL MAP (receptor to glomerulus)")
print("=" * 60)
al = pyreadr.read_r(base + "AL.map.RData")
for k, v in al.items():
    print(f"--- key: {k} | type: {type(v)} ---")
    print(v)
    break
