"""
  Generates IR frames to be transmitted to the AC unit
"""
import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import List

from libs.utils import FIXED_TAIL_BIT, OFFSET_BITS, TOTAL_BITS, encode_frame

# Classes
@dataclass(frozen=True)
class ConfigData:
	start_pos: int
	end_pos: int

"""
  Script Arguments
"""
script_args = {
  # "decode": {
  #   "description": "Decode a parsed bitstream",
  #   "arguments": [
  #     {"name": "input", "type": Path, "help": "Path to ir_parsed file"},
  #     {"name": "--bytes", "action": "store_true", "help": "Print byte dump"},
  #   ],
  # },
  "encode": {
    "description": "Encode a new bitstream",
    "arguments": [
      # {"name": "--base", "type": Path, "help": "Base ir_parsed file override"},
      {"name": "--output", "type": Path, "help": "Output path (ir_parsed format)"},
      {"name": "--power", "choices": ["on", "off"], "help": "Power setting"},
      {"name": "--temp", "type": int, "help": "Temperature in Celsius"},
      {"name": "--fan", "type": int, "help": "Fan setting (0-3)"},
      {"name": "--swing", "type": int, "help": "Swing setting (0-4)"},
      {"name": "--bytes", "action": "store_true", "help": "Print byte dump"},
    ],
  },
}

"""
  IR Data Configurations (The bit ranges where the data resides in the IR signal)
"""
# The sizes of the data segments vary, and may not necessarily have a even number of bits
# They're not grouped into bytes either, so the bit positions are purely arbitrary and based on the observed structure of the IR signal
ON_OFF_DATA: ConfigData = ConfigData(start_pos=44, end_pos=44) # Typically 1 bit (0 for off, 1 for on)
TEMP_DATA: ConfigData = ConfigData(start_pos=55, end_pos=58) # Typically 4 bits
FAN_DATA: ConfigData = ConfigData(start_pos=71, end_pos=73) # Typically 3 bits
SWING_DATA: ConfigData = ConfigData(start_pos=74, end_pos=77) # Typically 4 bits
ZERO_FILL_DATA: ConfigData = ConfigData(start_pos=106, end_pos=134) # Seems to have a fixed sequence of 29 bits that are always "0"
CHECKSUM_DATA: ConfigData = ConfigData(start_pos=135, end_pos=143) # Typically 8 bits

"""
  Settings (The actual values to be transmitted for each setting)
  The binary values are small-endian because the AC unit seems to read the bits in reverse order (seems to be a common convention in IR signals)
"""
FILL_DATA = {
  "header": 0b000100110100110110010010000000000000000000, # Pos 0-43
  "header2": 0b0000011000 # Pos 45-54
}

FAN_SETTINGS = {
  "auto": 0b000,
  "low": 0b100,
  "medium": 0b010,
  "high": 0b0110,
  "turbo": 0b001
}

SWING_SETTINGS = {
  "highest": 0b1001,
  "high": 0b0101,
  "medium": 0b1101,
  "low": 0b0011,
  "lowest": 0b1011,
}


"""
  Base Payload Structure (Configured for 24C, Swing 0, Fan 0, On)
"""
BASE_PAYLOAD = 0b00010011010011011001001000000000000000000001000001100000010000011011001001001001100110000000000000000000000000000000000000000000000000010111001

# Obtain the binary representation of the temperature setting, which is a 4-bit value representing the temperature in Celsius from 16 degrees (since the AC unit's temperature range starts at 16 degrees)
# Returns the result in little-endian format
def encode_temp_setting(temp_celsius: int) -> int:
  # Restrict the temperature to a valid range
  if temp_celsius < 16 or temp_celsius > 30:
    raise ValueError("Temperature must be between 16 and 30 degrees Celsius")
  result = bin(temp_celsius - 16)[2:].zfill(4)  # Remove '0b' prefix and zero-pad to 4 bits

  # Flip the bits to convert to little-endian format
  flipped = result[::-1]
  return flipped

"""
  Args parser
"""
def parse_args() -> argparse.Namespace:
  # Create the main argument parser and a subparser for the different commands (encode and decode)
  parser = argparse.ArgumentParser(description="KM16P IR protocol helper")
  sub = parser.add_subparsers(dest="command", required=True)

  # Iterate through the defined script arguments and add them to the parser
  for command, config in script_args.items():
    cmd_parser = sub.add_parser(command, help=config["description"])

    # Bind the arguments for the current command to the parser
    for arg in config["arguments"]:
      arg_name = arg.pop("name")
      cmd_parser.add_argument(arg_name, **arg)

  return parser.parse_args()

"""
  Writes the encoded bitstring to a file in the ir_parsed format, which consists of lines of 6 bytes (48 bits) each, with spaces between the bytes
"""
def write_bitstring(path: Path, bitstring: str) -> None:
    lines: List[str] = []
    for i in range(0, len(bitstring), 6):
        lines.append(" ".join(bitstring[i : i + 6]))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


"""
  Converts a bitstring into a list of bytes, taking into account the offset for the data and ensuring that the bits are grouped correctly into bytes (8 bits each), with the least significant bit first within each byte
"""
def bits_to_bytes(bitstring: str, offset: int = OFFSET_BITS) -> List[int]:
    bits = bitstring[offset:]
    if len(bits) % 8 != 0:
        # Allow trailing fixed tail bit, which is not part of any byte.
        if bits[-1:] == str(FIXED_TAIL_BIT) and (len(bits) - 1) % 8 == 0:
            bits = bits[:-1]
        else:
            raise ValueError("Bit length after offset is not byte-aligned")
    bytes_out: List[int] = []
    for i in range(0, len(bits), 8):
        chunk = bits[i : i + 8]
        chunk = chunk[::-1]  # LSB-first within each byte
        bytes_out.append(int(chunk, 2))
    return bytes_out


# Main function
def main() -> int:
  args = parse_args()
  
  # Default power setting to "on"
  power = None if args.power is None else args.power == "on"

  # Use the base payload as the starting point for encoding, which represents a typical frame with default settings (24C, Swing 0, Fan 0, On)
  base_bits = bin(BASE_PAYLOAD)[2:].zfill(TOTAL_BITS)  # Convert the base payload to a binary string, removing the '0b' prefix and zero-padding to ensure it has the correct total number of bits
  bitstring = encode_frame(
    base_bits,
    power=power,
    temp_c=args.temp,
    fan=args.fan,
    swing=args.swing,
  )

  # If an output path is provided, write the encoded bitstring to a file in the ir_parsed format; otherwise, print the bitstring to the console
  if args.output:
      write_bitstring(args.output, bitstring)
  else:
      print(bitstring)

  if args.bytes:
      bytes_all = bits_to_bytes(bitstring)
      print("bytes:", " ".join(f"{b:02X}" for b in bytes_all))

  return 0


if __name__ == "__main__":
  raise SystemExit(main())

print(encode_temp_setting(23))


