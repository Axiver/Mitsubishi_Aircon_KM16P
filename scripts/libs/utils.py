"""
IR protocol helpers for Mitsubishi KM16P frames.

This module decodes known fields from parsed bitstreams and
re-encodes new frames with a valid checksum.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

# Properties of the IR signal based on observed structure
TOTAL_BITS = 143
OFFSET_BITS = 6 # The first 6 bits of the signal seem to be a fixed header that doesn't change across frames, so we can ignore them when processing the data
FIXED_TAIL_BIT = 1 # The last bit of the signal seems to be a fixed "1" bit that is not part of any byte, so we can ignore it when processing the data
CHECKSUM_CONST = 0x23 # The checksum seems to be a simple sum of the payload bytes plus this constant, modulo 256. This was determined empirically by analyzing multiple frames and their checksums.

# Bit positions (0-based) in the raw parsed bitstring
POWER_BIT = 43
TEMP_BITS = [54, 55, 56, 57]  # 4 bits, LSB-first, value is tempC - 16
FAN_BITS = [70, 71, 72]       # 3 bits, LSB-first
SWING_BITS = [73, 74, 75, 76] # 4 bits, LSB-first
CHECKSUM_BITS = list(range(134, 142))

FAN_SETTING_TO_CODE = {
    0: 1,  # fan0 -> bits 100 (LSB-first value 1)
    1: 2,  # fan1 -> bits 010 (LSB-first value 2)
    2: 3,  # fan2 -> bits 110 (LSB-first value 3)
    3: 4,  # fan3 -> bits 001 (LSB-first value 4)
}

SWING_SETTING_TO_CODE = {
    0: 9,   # swing0 -> bits 1001 (LSB-first value 9)
    1: 10,  # swing1 -> bits 0101 (LSB-first value 10)
    2: 11,  # swing2 -> bits 1101 (LSB-first value 11)
    3: 12,  # swing3 -> bits 0011 (LSB-first value 12)
    4: 13,  # swing4 -> bits 1011 (LSB-first value 13)
}


@dataclass(frozen=True)
class DecodedFrame:
    power: bool
    temp_c: int
    fan: int
    swing: int
    checksum: int
    checksum_expected: int
    checksum_ok: bool

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

def apply_bytes(bitstring: str, bytes_in: Iterable[int], offset: int = OFFSET_BITS) -> str:
    if len(bitstring) != TOTAL_BITS:
        raise ValueError(f"Expected {TOTAL_BITS} bits, got {len(bitstring)}")
    bits = list(bitstring)
    for byte_index, value in enumerate(bytes_in):
        for bit_index in range(8):
            out_index = offset + (byte_index * 8) + bit_index
            if out_index >= TOTAL_BITS - 1:
                raise ValueError("Byte data exceeds total bit length")
            bit_value = (value >> bit_index) & 1
            bits[out_index] = "1" if bit_value else "0"
    return "".join(bits)


def encode_lsb_first(value: int, width: int) -> str:
    if value < 0 or value >= (1 << width):
        raise ValueError(f"Value {value} does not fit in {width} bits")
    return f"{value:0{width}b}"[::-1]

def set_bits(bitstring: str, positions: Iterable[int], bits_lsb_first: str) -> str:
    bits = list(bitstring)
    for pos, bit in zip(positions, bits_lsb_first):
        bits[pos] = bit
    return "".join(bits)


def compute_checksum(payload_bytes: List[int]) -> int:
    return (sum(payload_bytes) + CHECKSUM_CONST) & 0xFF


def update_checksum(bitstring: str) -> str:
    bytes_all = bits_to_bytes(bitstring)
    if len(bytes_all) < 2:
        raise ValueError("Bitstring is too short to contain checksum")
    payload = bytes_all[:-1]
    checksum = compute_checksum(payload)
    bytes_all[-1] = checksum
    return apply_bytes(bitstring, bytes_all)


def resolve_fan_code(fan_setting: int) -> int:
    if fan_setting in FAN_SETTING_TO_CODE:
        return FAN_SETTING_TO_CODE[fan_setting]
    raise ValueError("Fan setting must be 0-3")


def resolve_swing_code(swing_setting: int) -> int:
    if swing_setting in SWING_SETTING_TO_CODE:
        return SWING_SETTING_TO_CODE[swing_setting]
    raise ValueError("Swing setting must be 0-4")

def encode_frame(
    base_bitstring: str,
    power: bool | None = None,
    temp_c: int | None = None,
    fan: int | None = None,
    swing: int | None = None,
) -> str:
    bits = base_bitstring
    if power is not None:
        bits = set_bits(bits, [POWER_BIT], "1" if power else "0")
    if temp_c is not None:
        if temp_c < 16 or temp_c > 30:
            raise ValueError("Temperature must be between 16 and 30")
        temp_bits = encode_lsb_first(temp_c - 16, 4)
        bits = set_bits(bits, TEMP_BITS, temp_bits)
    if fan is not None:
        fan_bits = encode_lsb_first(resolve_fan_code(fan), 3)
        bits = set_bits(bits, FAN_BITS, fan_bits)
    if swing is not None:
        swing_bits = encode_lsb_first(resolve_swing_code(swing), 4)
        bits = set_bits(bits, SWING_BITS, swing_bits)

    return update_checksum(bits)