# BoardConfig.py
import numpy as np

class BoardManager:
    def __init__(self):
        # 0-63 --> a1-h8
        self.coords_table = {
            # White's perspective (a1 is closest, h8 is farthest)
            0:  [8.5, 7.0],    1: [8.5, 5.0],   2: [8.8, 3.2],     3: [9, 1.5],    4: [9.4, -0.5],    5: [9.6, -2.0],   6: [9.8, -3.8],    7: [10, -6.0],
            8:  [10.9, 7.33],   9: [10.9, 5.0],  10: [10.9, 3.2],  11: [10.9, 1.5],  12: [10.9, -0.5],  13: [11.2, -2.0],  14: [11.5, -3.8],  15: [11.8, -6.0],
            16: [13.3, 7.5],  17: [13.3, 5.0],  18: [13.3, 3.2],  19: [13.3, 1.5],  20: [13.3, -0.5],  21: [13.6, -2.0],  22: [14, -3.8],  23: [14.3, -6.0],
            24: [15.7, 8.0],  25: [15.7, 5.0],  26: [15.7, 3.2],  27: [15.7, 1.5],  28: [15.7, -0.5],  29: [16, -2.0],  30: [16.1, -3.8],  31: [16.2, -6.0],
            32: [18.1, 7.5],  33: [18.1, 4.71],  34: [18.1, 1.93],  35: [18.1, -0.86],  36: [18.1, -3.64],  37: [18.1, -6.43],  38: [18.1, -9.21],  39: [18.1, -12.0],
            40: [20.5, 7.5],  41: [20.5, 4.71],  42: [20.5, 1.93],  43: [20.5, -0.86],  44: [20.5, -3.64],  45: [20.5, -6.43],  46: [20.5, -9.21],  47: [20.5, -12.0],
            48: [24.25, 7.5], 49: [24.25, 4.71], 50: [24.25, 1.93], 51: [24.25, -0.86], 52: [24.25, -3.64], 53: [24.25, -6.43], 54: [24.25, -9.21], 55: [24.25, -12.0],
            56: [28.0, 7.5],  57: [28.0, 4.71],  58: [28.0, 1.93],  59: [28.0, -0.86],  60: [28.0, -3.64],  61: [28.0, -6.43],  62: [28.0, -9.21],  63: [28.0, -12.0]
        }

        self.files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        self.ranks = ['1', '2', '3', '4', '5', '6', '7', '8']

        self.capture_coords = []
        for x_val in [8.5, 11.5]:
            for i in range(8):
                self.capture_coords.append([x_val, 11.0 + i * 3.0])

        self.captured_count = 0

    def get_slot_coords(self, side, notation):
        """
        :param side: "black" or "white" for perspective
        :param notation: Chess notation like "e4"
        :return: [x, y, z] coordinates for the given slot, P.S. Z is set to a default safe height of 5.0 cm
        """
        file_char = notation[0].lower()
        rank_char = notation[1]

        f_idx = self.files.index(file_char) # a->0, h->7
        r_idx = self.ranks.index(rank_char) # 1->0, 8->7

        raw_index = r_idx * 8 + f_idx

        '''
        Perspective mapping:
        If playing black, the board is "flipped" so we need to invert the index to get the correct coordinates.
        If playing white, the index maps directly.
        '''
        if side == "black":
            target_index = 63 - raw_index
        else:
            target_index = raw_index

        if target_index in self.coords_table:
            xy = self.coords_table[target_index]
            return [xy[0], xy[1], 5.0]
        else:
            raise IndexError(f"Index {target_index} not calibrated in coords_table")

    def get_next_capture_slot(self):
        if self.captured_count < len(self.capture_coords):
            xy = self.capture_coords[self.captured_count]
            self.captured_count += 1
            return [xy[0], xy[1], 5.0]
        else:
            self.captured_count = 0
            return [self.capture_coords[0][0], self.capture_coords[0][1], 5.0]

    def reset_capture_count(self):
        self.captured_count = 0
