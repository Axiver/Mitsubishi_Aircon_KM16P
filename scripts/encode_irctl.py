import argparse
import re
from pathlib import Path

"""
    Define Header Data
"""
# Observed timings in microseconds from the captured dumps.
HEADER_PULSE = 3500 # Initial long pulse to indicate the start of a frame
HEADER_SPACE = 1650 # Long space after the initial pulse
BIT_PULSE = 440 # Standard pulse duration for every bit
BIT_SPACE_0 = 430 # Space duration for a "0" bit
BIT_SPACE_1 = 1280 # Space duration for a "1" bit
FRAME_GAP = 17000 # Gap at the end of the frame before the next one starts


"""
    Functions
"""
# Reads the input file and extracts a continuous string of bits (0s and 1s) from it, ignoring any other characters or formatting
def read_bits(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    bits = re.findall(r"[01]", text)
    if not bits:
        raise ValueError("No bits found in input file.")
    return "".join(bits)


def build_timings(bitstring: str) -> list[tuple[str, int]]:
    # Initialise a list of timings
    timings: list[tuple[str, int]] = []
    
    # Construct the header timings (first 3 bits)
    timings.append(("pulse", HEADER_PULSE))
    timings.append(("space", HEADER_SPACE))
    timings.append(("pulse", BIT_PULSE))
    timings.append(("space", BIT_SPACE_0))
    timings.append(("pulse", BIT_PULSE))
    timings.append(("space", BIT_SPACE_1))

    # Convert each bit in the bitstring into the corresponding pulse and space timings based on whether the bit is a "0" or a "1", using the defined durations for each type of bit
    for bit in bitstring:
        timings.append(("pulse", BIT_PULSE))
        if bit == "0":
            timings.append(("space", BIT_SPACE_0))
        else:
            timings.append(("space", BIT_SPACE_1))

    # Append the final gap timing at the end of the frame
    timings.append(("space", FRAME_GAP))
    return timings

# Writes the generated timings to a file in the format expected by ir-ctl
def write_irctl(path: Path, timings: list[tuple[str, int]]) -> None:
    # ir-ctl expects lines of the format "pulse/space <duration>"
    lines = [f"{kind} {duration}" for kind, duration in timings]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert KM16P bitstream into ir-ctl raw timings."
    )
    parser.add_argument("--input", required=True, type=Path, help="Input bit file.")
    parser.add_argument("--output", required=True, type=Path, help="Output raw file.")
    args = parser.parse_args()

    bitstring = read_bits(args.input)
    timings = build_timings(bitstring)
    write_irctl(args.output, timings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
