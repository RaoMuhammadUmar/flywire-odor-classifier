"""
Published sensillum -> odorant receptor gene mapping for the 20 ORN types
used in the de Bruyne dataset. Sourced from Couto et al. 2005, Fishilevich &
Vosshall 2005, Hallem & Carlson 2006, and the de Bruyne lab's own papers.

This is what 01_extract_connectome.py needs to filter the FlyWire connectome
down to these 20 receptor types -- but that requires the FlyWire "Cell Types"
file (per-neuron receptor/glomerulus identity), which has not been supplied
yet. classification.csv alone only has coarse categories (e.g. class=olfactory)
and cannot resolve individual receptor identity.
"""

ORN_TO_RECEPTOR = {
    "ab1A": "Or42b",
    "ab1B": "Or92a",
    "ab1C": "Gr21a/Gr63a",   # CO2 receptor, not an Or gene
    "ab1D": "Or10a",
    "ab2A": "Or59b",
    "ab2B": "Or85a",          # co-expresses Or33b
    "ab3A": "Or22a",
    "ab3B": "Or85b",
    "ab4A": "Or7a",
    "ab4B": "Or56a",          # co-expresses Or33a
    "ab5A": "Or82a",
    "ab5B": "Or47a",          # co-expresses Or33b
    "ab7A": "Or98a",
    "ab7B": "Or67c",
    "ab8A": "Or43b",
    "ab8B": "Or9a",
    "pb1A": "Or42a",
    "pb1B": "Or71a",
    "pb3A": "Or59c",
    "pb3B": "Or85d",
}
