# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------


# ##### BEGIN COPYRIGHT BLOCK #####
#
# initial script copyright (c)2013 Alexander Nussbaumer
#
# ##### END COPYRIGHT BLOCK #####

## this is a basic, partial and stripped implementation to read
## [LZO:1X]: Lempel-Ziv-Oberhumer lossless data compression algorithm
## http://www.oberhumer.com/opensource/lzo/
## this python implementation based on the java implementation from:
## http://www.oberhumer.com/opensource/lzo/download/LZO-v1/java-lzo-1.00.tar.gz


class Lzo_Codec:

    LZO_E_OK                  =  0
    LZO_E_ERROR               = -1
    LZO_E_INPUT_OVERRUN       = -4
    LZO_E_LOOKBEHIND_OVERRUN  = -6
    LZO_E_INPUT_NOT_CONSUMED  = -8

    @staticmethod
    def Lzo1x_Decompress(src, src_offset, src_length, dst, dst_offset):
        """
        src = bytes
        dst = bytearray

        returns: error, result_index
        """
        src_index = src_offset
        dst_index = dst_offset
        value = 0
        pos = 0
        error = Lzo_Codec.LZO_E_OK
        result_index = dst_index

        value = src[src_index]
        src_index += 1
        if value > 17:
            value -= 17
            while True: ## do while value > 0
                dst[dst_index] = src[src_index]
                value -= 1
                if value <= 0:
                    break ## do while value > 0
            dst_index += 1
            src_index += 1
            value = src[src_index]
            src_index += 1
            if value < 16:
                error = Lzo_Codec.LZO_E_ERROR
                return error, result_index

        ## loop:
        loop = False
        src_index -= 1 ## 1 for (;;value = src[src_index++])
        while not loop: ## 1 for (;;value = src[src_index++])
            value = src[src_index] ## 1 for (;;value = src[src_index++])
            src_index += 1 ## 1 for (;;value = src[src_index++])
            if value < 16:
                if value == 0:
                    while src[src_index] == 0:
                        value += 255
                        src_index += 1
                    value += 15 + src[src_index]
                    src_index += 1
                value += 3
                while True: ## do while value > 0
                    dst[dst_index] = src[src_index]
                    dst_index += 1
                    src_index += 1
                    value -= 1
                    if value <= 0:
                        break ## do while value > 0
                value = src[src_index]
                src_index += 1
                if value < 16:
                    pos = dst_index - 0x801 - (value >> 2) - (src[src_index] << 2)
                    src_index += 1
                    if pos < dst_offset:
                        error = Lzo_Codec.LZO_E_LOOKBEHIND_OVERRUN
                        loop = True
                        break ## loop
                    value = 3
                    while True: ## do while value > 0
                        dst[dst_index] = dst[pos]
                        dst_index += 1
                        pos += 1
                        value -= 1
                        if value <= 0:
                            break ## do while value > 0
                    value = src[src_index-2] & 3
                    if value == 0:
                        continue ## 1 for (;;value = src[src_index++])
                    while True: ## do while value > 0
                        dst[dst_index] = src[src_index]
                        dst_index += 1
                        src_index += 1
                        value -= 1
                        if value <= 0:
                            break ## do while value > 0
                    value = src[src_index]
                    src_index += 1

            src_index -= 1 ## 2 for (;;value = src[src_index++])
            while not loop: ## 2 for (;;value = src[src_index++])
                value = src[src_index] ## 2 for (;;value = src[src_index++])
                src_index += 1 ## 2 for (;;value = src[src_index++])
                if value >= 64:
                    pos = dst_index - 1 - ((value >> 2) & 7) - (src[src_index] << 3)
                    src_index += 1
                    value = (value >> 5) - 1
                elif value >= 32:
                    value &= 31
                    if value == 0:
                        while src[src_index] == 0:
                            value += 255
                            src_index += 1
                        value += 31 + src[src_index]
                        src_index += 1
                    pos = dst_index - 1 - (src[src_index] >> 2)
                    src_index += 1
                    pos -= (src[src_index] << 6)
                    src_index += 1
                elif value >= 16:
                    pos = dst_index - ((value & 8) << 11)
                    value &= 7
                    if value == 0:
                        while src[src_index] == 0:
                            value += 255
                            src_index += 1
                        value += 7 + src[src_index]
                        src_index += 1
                    pos -= (src[src_index] >> 2)
                    src_index += 1
                    pos -= (src[src_index] << 6)
                    src_index += 1
                    if pos == dst_index:
                        loop = True
                        break ## loop
                    pos -= 0x4000
                else:
                    pos = dst_index - 1 - (value >> 2) - (src[src_index] << 2)
                    src_index += 1
                    value = 0
                if pos < dst_offset:
                    error = Lzo_Codec.LZO_E_LOOKBEHIND_OVERRUN
                    loop = True
                    break ## loop
                value += 2
                while True: ## do while value > 0
                    dst[dst_index] = dst[pos]
                    dst_index += 1
                    pos += 1
                    value -= 1
                    if value <= 0:
                        break ## do while value > 0
                value = src[src_index - 2] & 3
                if value == 0:
                    break
                while True: ## do while value > 0
                    dst[dst_index] = src[src_index]
                    dst_index += 1
                    src_index += 1
                    value -= 1
                    if value <= 0:
                        break ## do while value > 0

        src_index -= src_offset
        dst_index -= dst_offset
        result_index = dst_index
        if error < Lzo_Codec.LZO_E_OK:
            return error, result_index
        if src_index < src_length:
            error = Lzo_Codec.LZO_E_INPUT_NOT_CONSUMED
            return error, result_index
        if src_index > src_length:
            error = Lzo_Codec.LZO_E_INPUT_OVERRUN
            return error, result_index
        if value != 1:
            error = Lzo_Codec.LZO_E_ERROR
            return error, result_index
        return error, result_index

###############################################################################


###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------
# ##### END OF FILE #####
