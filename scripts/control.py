"""
  Generates IR frames to be transmitted to the AC unit
"""
from dataclasses import dataclass

# Classes
@dataclass(frozen=True)
class ConfigData:
	start_pos: int
	end_pos: int

"""
  Configurations (The bit ranges where the data resides in the IR signal)
"""
# The sizes of the data segments vary, and may not necessarily have a even number of bits
# They're not grouped into bytes either, so the bit positions are purely arbitrary and based on the observed structure of the IR signal
ON_OFF_DATA: ConfigData = ConfigData(start_pos=44, end_pos=44) # Typically 1 bit (0 for off, 1 for on)
TEMP_DATA: ConfigData = ConfigData(start_pos=55, end_pos=58) # Typically 4 bits
FAN_DATA: ConfigData = ConfigData(start_pos=71, end_pos=73) # Typically 3 bits
SWING_DATA: ConfigData = ConfigData(start_pos=74, end_pos=77) # Typically 4 bits
ZERO_FILL_DATA: ConfigData = ConfigData(start_pos=106, end_pos=134) # Seems to have a fixed sequence of 29 bits that are always "0"
CHECKSUM_DATA: ConfigData = ConfigData(start_pos=135, end_pos=143) # Typically 8 bits
# Final bit in the signal is a fixed "1" bit

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

print(encode_temp_setting(23))