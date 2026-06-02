"""
Script to parse the IR pulse data from the raw IR dumps and convert it into a binary format.
"""

from dataclasses import dataclass
from pathlib import Path
import re
import sys

# Configure constants for directories and parsing parameters
DUMPS_DIR = Path(__file__).resolve().parent.parent / "ir_dumps"
PARSED_DIR = Path(__file__).resolve().parent.parent / "ir_parsed"
BIT_THRESHOLD = 800

TRIM_BITS = 0
PARSE_RAW = True

@dataclass(frozen=True)
class FrameResult:
	bit_string: str

# Remove the first row of the dump file, which is likely a header or metadata line
def strip_first_row(lines: list[str]) -> list[str]:
	return lines[1:]

# Extract data only from the first block
def extract_data(lines: list[str]) -> list[list[str]]:
	data: list[str] = []

	for line in lines:
		if not line.strip():
			return data
		
		data.append(line)
	
	return data


# Parse a block of lines to extract the pulse durations and convert them into a binary string based on the defined threshold
def parse_block_to_bits(lines: list[str]) -> str:
	numbers: list[int] = []

	for line in lines:
		for index, value in enumerate(re.findall(r"\d+", line)):
			# Only include the "off" durations, which are at odd indices in the data
			# The "off" durations seem to be the ones that determine the bit values
			if index % 2 != 0:
				numbers.append(int(value))

	return "".join("0" if value < BIT_THRESHOLD else "1" for value in numbers)

# Parse the dump file and return a list of FrameResult objects containing the frame index and the corresponding bit string for each block of data
def parse_dump_file(file_path: Path) -> list[FrameResult]:
	content = file_path.read_text(encoding="utf-8")
	lines = content.splitlines()
	stripped = strip_first_row(lines)
	data = extract_data(stripped)

	# Process the data to extract the bit string
	result = parse_block_to_bits(data)
	return result

# Format the bit string into lines of bytes, optionally trimming a specified number of bits from the start and allowing for raw output without byte grouping
def format_bit_string(bit_string: str, trim_bits: int = TRIM_BITS, raw: bool = False) -> list[str]:
	trimmed = bit_string[trim_bits:] if trim_bits > 0 else bit_string
	bytes_list = bit_string if raw else [trimmed[i : i + 8] for i in range(0, len(trimmed), 8)]
	lines: list[str] = []
	for i in range(0, len(bytes_list), 6):
		lines.append(" ".join(bytes_list[i : i + 6]))
	return lines

# Main
def main() -> int:
	# Check if the directory containing the IR dumps exists
	if not DUMPS_DIR.exists():
		print(f"IR dumps directory not found: {DUMPS_DIR}", file=sys.stderr)
		return 1

	# Ensure the output directory for parsed data exists
	PARSED_DIR.mkdir(parents=True, exist_ok=True)

	# Process each file in the dumps directory, parse it, and write the formatted output to the parsed directory
	for entry in sorted(DUMPS_DIR.iterdir()):
		# Only parse files
		if not entry.is_file():
			continue
		
		# Parse the dump file and extract the bit string
		bit_string = parse_dump_file(entry)
		output_lines: list[str] = []

		# Format the bit string and append it to the output lines
		output_lines.extend(format_bit_string(bit_string, trim_bits=TRIM_BITS, raw=PARSE_RAW))

		# Write the formatted output to a new file in the parsed directory, using the same name as the original dump file
		output_path = PARSED_DIR / entry.name
		output_path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")

	return 0


if __name__ == "__main__":
	raise SystemExit(main())
