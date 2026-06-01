# IR Bit/Byte Map (KM16P)

Byte mapping uses:

- Offset: 6 bits (discard bits 0-5 before byte grouping)
- Bit order in each byte: reversed (LSB-first)
- Total bits: 143 (bits 0-141 plus fixed bit 142 = 1)

## Byte Index Reference

After offset, there are 17 bytes (byte index 0-16). Byte 16 is checksum.

## Known Field Positions

Bit indices are 0-based within the 143-bit stream.

| Field | Bit Positions | Encoding |
|---|---|---|
| Power | 43 | 1 = on, 0 = off |
| Temperature | 54-57 | 4 bits, LSB-first, value is tempC - 16 |
| Fan | 70-72 | 3 bits, LSB-first |
| Swing | 73-76 | 4 bits, LSB-first |
| Zero fill | 105-133 | Observed constant 0s in base payload |
| Checksum | 134-141 | 8 bits, LSB-first byte after offset |
| Tail bit | 142 | fixed 1 |

## Known Fixed/Reserved Ranges

These ranges are constant in the base payload used by the encoder and appear fixed across the captured frames used so far. They may still contain mode-specific behavior not yet decoded.

| Range | Notes |
|---|---|
| 0-42 | Base header (fixed in base payload) |
| 44-53 | Secondary header (fixed in base payload) |

## Known Encoded Values

Fan and swing settings are encoded as LSB-first bitfields.

| Field | Setting | LSB-first value | Bits |
|---|---|---:|---|
| Fan | 0 | 1 | 100 |
| Fan | 1 | 2 | 010 |
| Fan | 2 | 3 | 110 |
| Fan | 3 | 4 | 001 |
| Swing | 0 | 9 | 1001 |
| Swing | 1 | 10 | 0101 |
| Swing | 2 | 11 | 1101 |
| Swing | 3 | 12 | 0011 |
| Swing | 4 | 13 | 1011 |

## Full Bit Map

| Bit Index | Byte Index | Byte Bit (LSB=0) | Notes |
|---:|---:|---:|---|
| 0 | - | - | offset bits (fixed 0) |
| 1 | - | - | offset bits (fixed 0) |
| 2 | - | - | offset bits (fixed 0) |
| 3 | - | - | offset bits (fixed 0) |
| 4 | - | - | offset bits (fixed 0) |
| 5 | - | - | offset bits (fixed 0) |
| 6 | 0 | 0 |  |
| 7 | 0 | 1 |  |
| 8 | 0 | 2 |  |
| 9 | 0 | 3 |  |
| 10 | 0 | 4 |  |
| 11 | 0 | 5 |  |
| 12 | 0 | 6 |  |
| 13 | 0 | 7 |  |
| 14 | 1 | 0 |  |
| 15 | 1 | 1 |  |
| 16 | 1 | 2 |  |
| 17 | 1 | 3 |  |
| 18 | 1 | 4 |  |
| 19 | 1 | 5 |  |
| 20 | 1 | 6 |  |
| 21 | 1 | 7 |  |
| 22 | 2 | 0 |  |
| 23 | 2 | 1 |  |
| 24 | 2 | 2 |  |
| 25 | 2 | 3 |  |
| 26 | 2 | 4 |  |
| 27 | 2 | 5 |  |
| 28 | 2 | 6 |  |
| 29 | 2 | 7 |  |
| 30 | 3 | 0 |  |
| 31 | 3 | 1 |  |
| 32 | 3 | 2 |  |
| 33 | 3 | 3 |  |
| 34 | 3 | 4 |  |
| 35 | 3 | 5 |  |
| 36 | 3 | 6 |  |
| 37 | 3 | 7 |  |
| 38 | 4 | 0 |  |
| 39 | 4 | 1 |  |
| 40 | 4 | 2 |  |
| 41 | 4 | 3 |  |
| 42 | 4 | 4 |  |
| 43 | 4 | 5 |  |
| 44 | 4 | 6 |  |
| 45 | 4 | 7 |  |
| 46 | 5 | 0 |  |
| 47 | 5 | 1 |  |
| 48 | 5 | 2 |  |
| 49 | 5 | 3 |  |
| 50 | 5 | 4 |  |
| 51 | 5 | 5 |  |
| 52 | 5 | 6 |  |
| 53 | 5 | 7 |  |
| 54 | 6 | 0 |  |
| 55 | 6 | 1 |  |
| 56 | 6 | 2 |  |
| 57 | 6 | 3 |  |
| 58 | 6 | 4 |  |
| 59 | 6 | 5 |  |
| 60 | 6 | 6 |  |
| 61 | 6 | 7 |  |
| 62 | 7 | 0 |  |
| 63 | 7 | 1 |  |
| 64 | 7 | 2 |  |
| 65 | 7 | 3 |  |
| 66 | 7 | 4 |  |
| 67 | 7 | 5 |  |
| 68 | 7 | 6 |  |
| 69 | 7 | 7 |  |
| 70 | 8 | 0 |  |
| 71 | 8 | 1 |  |
| 72 | 8 | 2 |  |
| 73 | 8 | 3 |  |
| 74 | 8 | 4 |  |
| 75 | 8 | 5 |  |
| 76 | 8 | 6 |  |
| 77 | 8 | 7 |  |
| 78 | 9 | 0 |  |
| 79 | 9 | 1 |  |
| 80 | 9 | 2 |  |
| 81 | 9 | 3 |  |
| 82 | 9 | 4 |  |
| 83 | 9 | 5 |  |
| 84 | 9 | 6 |  |
| 85 | 9 | 7 |  |
| 86 | 10 | 0 |  |
| 87 | 10 | 1 |  |
| 88 | 10 | 2 |  |
| 89 | 10 | 3 |  |
| 90 | 10 | 4 |  |
| 91 | 10 | 5 |  |
| 92 | 10 | 6 |  |
| 93 | 10 | 7 |  |
| 94 | 11 | 0 |  |
| 95 | 11 | 1 |  |
| 96 | 11 | 2 |  |
| 97 | 11 | 3 |  |
| 98 | 11 | 4 |  |
| 99 | 11 | 5 |  |
| 100 | 11 | 6 |  |
| 101 | 11 | 7 |  |
| 102 | 12 | 0 |  |
| 103 | 12 | 1 |  |
| 104 | 12 | 2 |  |
| 105 | 12 | 3 |  |
| 106 | 12 | 4 |  |
| 107 | 12 | 5 |  |
| 108 | 12 | 6 |  |
| 109 | 12 | 7 |  |
| 110 | 13 | 0 |  |
| 111 | 13 | 1 |  |
| 112 | 13 | 2 |  |
| 113 | 13 | 3 |  |
| 114 | 13 | 4 |  |
| 115 | 13 | 5 |  |
| 116 | 13 | 6 |  |
| 117 | 13 | 7 |  |
| 118 | 14 | 0 |  |
| 119 | 14 | 1 |  |
| 120 | 14 | 2 |  |
| 121 | 14 | 3 |  |
| 122 | 14 | 4 |  |
| 123 | 14 | 5 |  |
| 124 | 14 | 6 |  |
| 125 | 14 | 7 |  |
| 126 | 15 | 0 |  |
| 127 | 15 | 1 |  |
| 128 | 15 | 2 |  |
| 129 | 15 | 3 |  |
| 130 | 15 | 4 |  |
| 131 | 15 | 5 |  |
| 132 | 15 | 6 |  |
| 133 | 15 | 7 |  |
| 134 | 16 | 0 | checksum byte |
| 135 | 16 | 1 | checksum byte |
| 136 | 16 | 2 | checksum byte |
| 137 | 16 | 3 | checksum byte |
| 138 | 16 | 4 | checksum byte |
| 139 | 16 | 5 | checksum byte |
| 140 | 16 | 6 | checksum byte |
| 141 | 16 | 7 | checksum byte |
| 142 | - | - | fixed 1 |
