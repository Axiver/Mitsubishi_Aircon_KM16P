# Mitsubishi_Aircon_KM16P

Reverse engineering the KM16P remote for Mitsubishi air conditioners. This project collects raw IR dumps, parses them into bitstreams, and documents the protocol structure (including checksum behavior). It also provides a small encoder/decoder utility for working with the parsed frames.

## Repository layout

- Raw IR captures: [ir_dumps/](ir_dumps/)
- Parsed bitstreams (one bit per token): [ir_parsed/](ir_parsed/)
- Parsing and encoding tools: [scripts/parse.py](scripts/parse.py), [scripts/control.py](scripts/control.py)
- Bit and byte map reference: [docs/ir_bit_map.md](docs/ir_bit_map.md)

## Data flow

1. Raw captures in [ir_dumps/](ir_dumps/) are processed by [scripts/parse.py](scripts/parse.py).
2. The parser extracts off-durations, thresholding them into 0/1 bits, and writes output into [ir_parsed/](ir_parsed/).
3. The encoding helper in [scripts/control.py](scripts/control.py) encodes new frames with a valid checksum.

## Parsed bitstream format

Each file in [ir_parsed/](ir_parsed/) is a single frame represented as whitespace-separated bits. The total length is 143 bits. Bit 142 is always fixed to 1.

For byte-oriented work, the mapping is:

- Drop the first 6 bits (offset).
- Group into bytes.
- Reverse bit order inside each byte (LSB-first).
- The last byte (byte index 16) is the checksum.

The full bit and byte index map is in [docs/ir_bit_map.md](docs/ir_bit_map.md).

## Known field locations

Field positions below are 0-based bit indices within the 143-bit stream.

- Power: bit 43
- Temperature: bits 54-57 (LSB-first, value is tempC - 16)
- Fan: bits 70-72 (LSB-first, settings 0-3)
- Swing: bits 73-76 (LSB-first, settings 0-4)
- Checksum: bits 134-141
- Fixed tail bit: 142 (always 1)

Some mode-specific flags appear in clusters around bits 49-51, 63-64, 72-78, 88-104, and 115, based on the captured frames. These are not fully decoded yet.

## Checksum

Checksum is computed over the payload bytes (after offset and bit reversal) as:

$$
	ext{checksum} = (\sum\text{payload bytes} + 0x23) \bmod 256
$$

## Usage

All commands below assume the venv is active, or you are calling the venv Python directly.

### Parse raw dumps

Run the parser to regenerate [ir_parsed/](ir_parsed/) from [ir_dumps/](ir_dumps/):

```
py scripts/parse.py
```

Converts raw timing dumps into bits, applying a fixed threshold to distinguish 0/1 bits.

### Encode a new frame

By default, encoding uses the 24C_swing0_fan0 payload as the base. To create a new frame with specific settings, run:

```
py scripts/control.py encode \
	--temp 25 \
	--fan 2 \
	--swing 3 \
	--power on \
	--output ./bitstream_file \
	--bytes
```

This creates a new frame with the specified temperature, fan, swing, and power settings, while preserving other bits from the base frame. The checksum and fixed tail bit are automatically updated.
Note that the output is not transmissible as-is; it is a bitstream file that can be converted to ir-ctl timings with the next step.

If you are working with a specific mode (auto, eco, dehumidifying, fan, smartset, timer), start from a base frame that already matches that mode to preserve mode-specific bits.
(This may be added in the future, but for now you can manually copy a base frame from [ir_parsed/](ir_parsed/) that matches your desired mode and modify it with the encoder.)

### Transmit with ir-ctl

#### Bitstream to ir-ctl timings
To convert a bitstream file into ir-ctl timings for transmission, run:

```py scripts/encode_irctl.py \
	--input ./bitstream_file \
	--output ./ir_ctl_timings
```

The IR frame can then be transmitted using ir-ctl with the generated timings file.

`ir-ctl -d /dev/lirc0 --send=./ir_ctl_timings --carrier=38000` (at 38kHz carrier frequency)

## Notes and limitations

- The parser currently uses a fixed threshold for distinguishing 0/1 bits. If your capture hardware or environment differs, adjust `BIT_THRESHOLD` in [scripts/parse.py](scripts/parse.py).
- Only a subset of fields is fully decoded. Mode-related flags still need additional reverse engineering.
- The encoder updates the checksum and fixed tail bit for you, but does not change unknown mode bits.

## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to this project. Contributions to expand the protocol decoding, add more captures, or improve the tools are welcome.
