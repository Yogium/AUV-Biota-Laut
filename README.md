# AUV Biota Laut
Ini adalah repository untuk semua program kelompok TA AUV Biota Laut ITB 2025-2026

Data structure:
- id        : int
- timestamp : string
- latitude : double
- longitude : double
- depth     : float
- label     : string
- confidence: float
- filename  : string

## ID format
10 digit structure:

| Digit | Function | Allocation | Explanation |
|-------|----------|-----------|-----------|
| 1 | Flag | 1 digit | 0 (Safe) or 1 (Warning).|
| 2 | Label | 1 digit | 0-4 (Fish, Coral, Seagrass, Human, Other). |
| 3-7 | Frame | 5 digit | Frame number |
| 8-10 | Counter | 3 digit | Object number in frame |
