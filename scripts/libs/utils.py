"""
IR protocol helpers for Mitsubishi KM16P frames.

This module decodes known fields from parsed bitstreams and
re-encodes new frames with a valid checksum.
"""

from typing import Iterable, List

# Properties of the IR signal based on observed structure
TOTAL_BITS = 143
OFFSET_BITS = 6  # The first 6 bits of the signal seem to be a fixed header that doesn't change across frames, so we can ignore them when processing the data
FIXED_TAIL_BIT = 1  # The last bit of the signal seems to be a fixed "1" bit that is not part of any byte, so we can ignore it when processing the data
CHECKSUM_CONST = 0x23  # The checksum seems to be a simple sum of the payload bytes plus this constant, modulo 256. This was determined empirically by analyzing multiple frames and their checksums.

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


def apply_bytes(
    bitstring: str, bytes_in: Iterable[int], offset: int = OFFSET_BITS
) -> str:
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


def set_bits(bitstring: str, positions: range, bits_lsb_first: str) -> str:
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
