import numpy as np
import cv2

class SimpleCaptchaSolver:
    def __init__(self):
        # 標準字典：適用於第 2, 3, 4 碼
        self.standard_map = {
            159: "0", 104: "1", 111: "2", 116: "3", 123: "4",
            113: "5", 136: "6", 94:  "7", 138: "8", 132: "9"
        }
        # 第一碼專用字典：包含了左側邊框固定雜訊
        self.first_digit_map = {
            181: "0", 120: "1", 127: "2", 132: "3", 142: "4",
            128: "5", 154: "6", 109: "7", 159: "8", 150: "9"
        }

    def _find_closest_digit(self, pixel_count, is_first_digit):
        """絕對精準配對"""
        target_map = self.first_digit_map if is_first_digit else self.standard_map
        if pixel_count in target_map:
            return target_map[pixel_count]
        
        # 遇到未知像素數量時啟動模糊比對
        print(f"  [警告] 出現未知的像素數量：{pixel_count}，啟動模糊比對...")
        closest_count = min(target_map.keys(), key=lambda k: abs(k - pixel_count))
        return target_map[closest_count]

    def solve_from_bytes(self, image_bytes):
        """優化：直接從記憶體 byte array 解碼，不寫入硬碟"""
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img_gray = cv2.imdecode(np_arr, cv2.IMREAD_GRAYSCALE)
        
        if img_gray is None:
            return "ERROR"

        # 極端二值化 (254, 255)
        _, img_binary = cv2.threshold(img_gray, 254, 255, cv2.THRESH_BINARY_INV)
        img_binary = img_binary // 255

        # 垂直投影與切割區塊
        vertical_projection = np.sum(img_binary, axis=0)
        chars_x_coords = []
        in_character = False
        start_x = 0

        for x in range(len(vertical_projection)):
            if vertical_projection[x] > 0 and not in_character:
                in_character = True
                start_x = x
            elif vertical_projection[x] == 0 and in_character:
                in_character = False
                end_x = x
                if end_x - start_x > 2:
                    chars_x_coords.append((start_x, end_x))

        if in_character and len(vertical_projection) - start_x > 2:
            chars_x_coords.append((start_x, len(vertical_projection)))

        # 辨識數字
        result = ""
        for i, (start_x, end_x) in enumerate(chars_x_coords):
            char_matrix = img_binary[:, start_x:end_x]
            pixel_count = np.sum(char_matrix)
            is_first = (i == 0)
            result += self._find_closest_digit(pixel_count, is_first)

        return result