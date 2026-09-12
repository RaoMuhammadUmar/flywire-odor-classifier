import pyreadr

base = "data/door_raw/DoOR_data-v2_0_0/Dahaniel-DoOR.data-6436660/data/"

print("=" * 60)
print("DoOR.mappings.RData")
print("=" * 60)
maps = pyreadr.read_r(base + "DoOR.mappings.RData")
for k, v in maps.items():
    print(f"\n--- key: {k} | type: {type(v)} ---")
    print(v)
    print()

print("=" * 60)
print("AL.map.RData")
print("=" * 60)
al = pyreadr.read_r(base + "AL.map.RData")
for k, v in al.items():
    print(f"\n--- key: {k} | type: {type(v)} ---")
    print(v)
    print()
