"""
Generates IR frames to be transmitted to the AC unit
"""

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
from typing import List

from libs.utils import (
    TOTAL_BITS,
    encode_lsb_first,
    set_bits,
    update_checksum,
)
from encode_irctl import build_timings, write_irctl


# Classes
@dataclass(frozen=True)
class ConfigData:
    start_pos: int
    end_pos: int


"""
  Script Arguments
"""
common_args = [
    # {"name": "--base", "type": Path, "help": "Base ir_parsed file override"},
    {"name": "--power", "choices": ["on", "off"], "help": "Power setting"},
    {"name": "--temp", "type": int, "help": "Temperature in Celsius"},
    {"name": "--fan", "type": int, "help": "Fan setting (0-3)"},
    {"name": "--swing", "type": int, "help": "Swing setting (0-5)"},
]

script_args = {
    # "decode": {
    #   "description": "Decode a parsed bitstream",
    #   "arguments": [
    #     {"name": "input", "type": Path, "help": "Path to ir_parsed file"},
    #     {"name": "--bytes", "action": "store_true", "help": "Print byte dump"},
    #   ],
    # },
    "transmit": {
        "description": "Transmit an IR Frame with the specified settings (Control your AC!)",
        "arguments": [arg.copy() for arg in common_args],
    },
    "encode": {
        "description": "Encode a new KM16P IR Frame",
        "arguments": [* [arg.copy() for arg in common_args],
            {"name": "--debug", "action": "store_true", "help": "Print bitstream dump"},
            {
                "name": "--output",
                "type": Path,
                "help": "Output path (ir_parsed format)",
            },
        ],
    },
}

"""
  IR Data Configurations (The bit ranges where the data resides in the IR signal)
"""
# The sizes of the data segments vary, and may not necessarily have a even number of bits
# They're not grouped into bytes either, so the bit positions are purely arbitrary and based on the observed structure of the IR signal
# Bit positions (0-based) in the raw parsed bitstring
POWER_DATA: ConfigData = ConfigData(
    start_pos=43, end_pos=43
)  # Typically 1 bit (0 for off, 1 for on)
TEMP_DATA: ConfigData = ConfigData(start_pos=54, end_pos=57)  # Typically 4 bits
FAN_DATA: ConfigData = ConfigData(start_pos=70, end_pos=72)  # Typically 3 bits
SWING_DATA: ConfigData = ConfigData(start_pos=73, end_pos=76)  # Typically 4 bits
CHECKSUM_DATA: ConfigData = ConfigData(start_pos=134, end_pos=142)  # Typically 8 bits

"""
  Settings (The actual values to be transmitted for each setting)
  The binary values are small-endian because the AC unit seems to read the bits in reverse order (seems to be a common convention in IR signals)
"""
# (Unused for now but might be helpful in the future)
FILL_DATA = {
    "header": 0b000100110100110110010010000000000000000000,  # Pos 0-43
    "header2": 0b0000011000,  # Pos 45-54
}

# Bits representing each fan setting
FAN_SETTING_TO_CODE = {
    0: 1,  # fan0 -> bits 100 (LSB-first value 1) (Low)
    1: 2,  # fan1 -> bits 010 (LSB-first value 2) (Medium)
    2: 3,  # fan2 -> bits 110 (LSB-first value 3) (High)
    3: 4,  # fan3 -> bits 001 (LSB-first value 4) (Turbo)
}

# Bits representing each swing setting
SWING_SETTING_TO_CODE = {
    0: 9,  # swing0 -> bits 1001 (LSB-first value 9) (Highest)
    1: 10,  # swing1 -> bits 0101 (LSB-first value 10) (High)
    2: 11,  # swing2 -> bits 1101 (LSB-first value 11) (Medium)
    3: 12,  # swing3 -> bits 0011 (LSB-first value 12) (Low)
    4: 13,  # swing4 -> bits 1011 (LSB-first value 13) (Lowest)
    5: 15,  # swing auto -> bits 1111 (LSB-first value 15) (Auto)
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
    result = bin(temp_celsius - 16)[2:].zfill(
        4
    )  # Remove '0b' prefix and zero-pad to 4 bits

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


def resolve_fan_code(fan_setting: int) -> int:
    if fan_setting in FAN_SETTING_TO_CODE:
        return FAN_SETTING_TO_CODE[fan_setting]
    raise ValueError("Fan setting must be 0-3")


def resolve_swing_code(swing_setting: int) -> int:
    if swing_setting in SWING_SETTING_TO_CODE:
        return SWING_SETTING_TO_CODE[swing_setting]
    raise ValueError("Swing setting must be 0-5, where 5 is auto")


def encode_frame(
    base_bitstring: str,
    power: bool | None = None,
    temp_c: int | None = None,
    fan: int | None = None,
    swing: int | None = None,
) -> str:
    bits = base_bitstring
    if power is not None:
        bits = set_bits(bits, [POWER_DATA], "1" if power else "0")
    if temp_c is not None:
        if temp_c < 16 or temp_c > 30:
            raise ValueError("Temperature must be between 16 and 30")
        temp_bits = encode_lsb_first(temp_c - 16, 4)
        bits = set_bits(
            bits, range(TEMP_DATA.start_pos, TEMP_DATA.end_pos + 1), temp_bits
        )
    if fan is not None:
        fan_bits = encode_lsb_first(resolve_fan_code(fan), 3)
        bits = set_bits(bits, range(FAN_DATA.start_pos, FAN_DATA.end_pos + 1), fan_bits)
    if swing is not None:
        swing_bits = encode_lsb_first(resolve_swing_code(swing), 4)
        bits = set_bits(
            bits, range(SWING_DATA.start_pos, SWING_DATA.end_pos + 1), swing_bits
        )

    return update_checksum(bits)


def send_ir_frame(bitstring: str) -> None:
    # Convert the bitstring into ir-ctl timings
    timings = build_timings(bitstring)

    # Save to a temp file
    write_irctl(Path("./temp_timings"), timings)

    # Send the IR frame
    os.system("ir-ctl -d /dev/lirc0 --send=./temp_timings --carrier=38000")

    # Delete the temp file
    os.remove("./temp_timings")

    return


# Main function
def main() -> int:
    args = parse_args()

    # Default power setting to "on"
    power = None if args.power is None else args.power == "on"

    # Use the base payload as the starting point for encoding, which represents a typical frame with default settings (24C, Swing 0, Fan 0, On)
    base_bits = bin(BASE_PAYLOAD)[2:].zfill(
        TOTAL_BITS
    )  # Convert the base payload to a binary string. Also removing the '0b' prefix and the header bits

    # Check that it has the expected length of bits
    if len(base_bits) != TOTAL_BITS:
        raise ValueError(f"Base payload must be {TOTAL_BITS} bits long")

    bitstring = encode_frame(
        base_bits,
        power=power,
        temp_c=args.temp,
        fan=args.fan,
        swing=args.swing,
    )

    # If an output path is provided, write the encoded bitstring to a file in the ir_parsed format
    if args.command == "encode":
        if args.output:
            write_bitstring(args.output, bitstring)

        # If debug flag is set, print the bitstring to the console
        if args.debug:
            print(bitstring)

        # if args.bytes:
        #     bytes_all = bits_to_bytes(bitstring)
        #     print("bytes:", " ".join(f"{b:02X}" for b in bytes_all))

    # Send the IR frame using the generated bitstring if the transmit command is used
    if args.command == "transmit":
        send_ir_frame(bitstring)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
