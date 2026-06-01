# Contributing

Thanks for helping reverse engineer the Mitsubishi KM16P IR protocol. This repo focuses on collecting IR dumps, parsing them into bitstreams, and documenting or encoding the protocol.

## Ways to contribute

- Add new IR captures in ir_dumps/ and their parsed bitstreams in ir_parsed/.
- Improve the parser or protocol tools in scripts/.
- Document new field mappings or behaviors in docs/.
- Report findings in issues or pull requests with clear reproduction steps.

## Data contributions (IR captures)

### Capture guidelines

- Capture a single, clean frame per file.
- Keep the remote pointed at the receiver and minimize reflections.
- Record the exact remote settings for each capture (mode, temp, fan, swing, power, timers).

### File naming

Use a descriptive, consistent name that matches the existing pattern:

- 24C_swing0_fan2
- eco_24C_swing0_fan0
- timer_start_24C_swing0_fan0

If a capture does not fit the current pattern, still keep it short and descriptive.

### Parsed data

After adding a file to ir_dumps/, run the parser to regenerate the parsed output:

```
py scripts/parse.py
```

Check in both the new dump and the new parsed file. Keep the output in ir_parsed/ with the same base name as the input.

## Protocol and code changes

### Environment setup

- Use Python 3.10+.
- Create and activate a venv (example for Windows):

```
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Encoding and decoding

If you add or modify protocol logic, validate changes by encoding a known frame and checking:

- The checksum matches the documented calculation.
- The fixed tail bit is set.
- The encoded output length stays 143 bits.

### Documentation updates

When you decode new fields, update docs/ir_bit_map.md and include:

- Bit and byte positions (0-based bit index in the 143-bit stream).
- Value encoding details (LSB/MSB, offsets, valid ranges).
- Example captures showing the change.

## PR checklist

- New captures include both ir_dumps/ and matching ir_parsed/ files.
- Tool changes include a short explanation in the PR description.
- Documentation updated when new field locations are discovered.
- No unrelated changes in the same PR.

## Questions

If you are unsure about a capture format or a field mapping, open an issue with your raw dump and the exact remote settings used.
