import cv2
import utils
import numpy as np
from PIL import ImageGrab
from debug_window import DebugWindow
from concurrent.futures import ThreadPoolExecutor
from skimage.metrics import structural_similarity as ssim

class BlockRecognizer:
    def __init__(self, screen_region, templates):
        """
        初始化方块识别器
        :param screen_region: 屏幕区域 (x1, y1, x2, y2)
        :param templates: 模板字典 {name: image}
        """
        self.screen_region = screen_region
        self.templates = templates
        self.block_w, self.block_h = 78, 82  # 每个方块的尺寸
        self.grid_cols, self.grid_rows = 10, 14  # 横向10个，纵向14个方块
        self.last_state = None  # 上一次识别结果

        # 调试窗口
        self.debug_window = DebugWindow()
        self.scale = utils.get_scaling_factor()

        # 校准参数
        self.calibrated = False
        self.start_x = self.start_y = 0  # 第一个方块的左上角坐标
        self.h_gap = 7  # 横向间隙
        self.v_gap = 3  # 纵向间隙

    def process_frame(self):
        """
        处理每一帧图像，包括校准、识别和状态检测
        """
        screen_img = self._capture_screen()
        if not self.calibrated:
            self._auto_calibrate(screen_img)
            return True
        else:
            self.last_state = self._recognize_blocks(screen_img)
            return False

    def _capture_screen(self):
        """
        捕获屏幕区域
        :return: 彩色图像
        """
        img = ImageGrab.grab(bbox=self.screen_region)
        screen_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        # 检查捕获的图像是否为空
        if screen_img is None or screen_img.size == 0:
            raise Exception("捕获的屏幕图像为空，请检查 screen_region 参数")

        return screen_img

    def _auto_calibrate(self, screen_img):
        """并行匹配多模板进行校准"""
        debug_img = screen_img.copy()
    
        def match_template(name, template):
            res = cv2.matchTemplate(screen_img, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            return name, template, max_val, max_loc
    
        # 并行匹配所有非空白模板
        with ThreadPoolExecutor() as executor:
            futures = []
            for name, template in self.templates.items():
                if name == "None":
                    continue
                futures.append(executor.submit(match_template, name, template))
    
            # 找到匹配值最高的模板
            best_match = None
            best_val = -1
            for future in futures:
                name, template, max_val, max_loc = future.result()
                if max_val > best_val:
                    best_val = max_val
                    best_match = (name, template, max_loc)
    
        if best_val < 0.6:
            cv2.imwrite("debug_failed_calibration.png", debug_img)
            raise Exception("校准失败：未找到匹配的模板")
    
        # 使用最佳匹配模板进行校准
        name, template, max_loc = best_match
        self.start_x, self.start_y = max_loc
        roi = screen_img[self.start_y:self.start_y + self.block_h,
              self.start_x:self.start_x + self.block_w]
        res = cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED)
        _, local_max_val, _, _ = cv2.minMaxLoc(res)
    
        if local_max_val < 0.7:
            raise Exception("二次校准失败")

        cv2.rectangle(debug_img, (int(self.start_x), int(self.start_y)), (int(self.start_x + self.block_w), int(self.start_y + self.block_h)), (0, 255, 0), 3)
        # 显示校准结果
        self.debug_window.update(debug_img, f"校准成功（使用模板: {name}）")
        self.calibrated = True
        print(f"校准成功: 使用模板 '{name}'，起点({self.start_x}, {self.start_y}) 横向间隙{self.h_gap} 纵向间隙{self.v_gap}")

    def _find_all_blocks(self, screen_img):
        """从校准方块开始，向四周逐个遍历，找到所有方块"""
        positions = {}  # 存储方块位置 {(col, row): (x1, y1, x2, y2)}
        visited = set()  # 记录已访问的方块
    
        # 定义方向：右、左、下、上
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    
        # 初始化队列：从校准方块开始
        queue = [(0, 0, int(self.start_x), int(self.start_y))]  # (col, row, x, y)
    
        while queue:
            col, row, x, y = queue.pop(0)
            if (col, row) in visited:
                continue
            visited.add((col, row))
    
            # 截取方块区域
            x1, y1 = int(x), int(y)
            x2, y2 = int(x + self.block_w), int(y + self.block_h)
    
            # 检查坐标是否在图像范围内
            if x1 < 0 or y1 < 0 or x2 > screen_img.shape[1] or y2 > screen_img.shape[0]:
                continue
    
            # 截取方块图像
            block = screen_img[y1:y2, x1:x2]
            if block.size == 0:
                continue
    
            # 匹配方块
            best_match, confidence = self._match_block(block)
            if best_match == "unknown":
                continue  # 如果匹配结果为未知，停止向该方向扩展
    
            # 记录方块位置
            positions[(col, row)] = {
                'name': best_match,
                'coordinate': (x1, y1, x2, y2)
            }
    
            # 向四周扩展
            for dx, dy in directions:
                new_col = col + dx
                new_row = row + dy
                new_x = x + dx * (self.block_w + self.h_gap)
                new_y = y + dy * (self.block_h + self.v_gap)
                queue.append((new_col, new_row, int(new_x), int(new_y)))
    
        return positions

    def _recognize_blocks(self, screen_img):
        """识别所有方块"""
        debug_img = screen_img.copy()
    
        # 获取所有方块的位置
        positions = self._find_all_blocks(screen_img)
    
        for _, value in positions.items():
            name = value['name']
            x1, y1, x2, y2 = value['coordinate']
            if value['name'] != "None":
                # 绘制方块的矩形框
                cv2.rectangle(debug_img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                
                # 添加文字标注（带背景矩形）
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.4
                font_thickness = 1
                text_size, _ = cv2.getTextSize(name, font, font_scale, font_thickness)
        
                # 计算背景矩形位置
                text_x = int(x1) + 5
                text_y = int(y1) + 20
                bg_x1 = text_x
                bg_y1 = text_y - text_size[1]
                bg_x2 = text_x + text_size[0]
                bg_y2 = text_y
        
                # 绘制背景矩形
                cv2.rectangle(debug_img, (bg_x1, bg_y1), (bg_x2, bg_y2), (255, 255, 255), -1)  # 白色背景
        
                # 绘制文字
                cv2.putText(debug_img, name, (text_x, text_y), font, font_scale, (0, 0, 0), font_thickness)
    
        self.debug_window.update(debug_img, "识别完成")
        return positions

    def _match_block(self, block):
        """多维度特征匹配"""
        best_match = "unknown"
        max_confidence = 0

        # 统一区块尺寸（解决缩放问题）
        resized_block = cv2.resize(block, (78, 82))

        for name, template in self.templates.items():
            # if name == "None":
            #     continue

            # 特征1: 结构相似性（SSIM）
            gray_block = cv2.cvtColor(resized_block, cv2.COLOR_BGR2GRAY)
            gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            ssim_score = ssim(gray_block, gray_template)

            # 特征2: 颜色直方图
            hist_block = cv2.calcHist([resized_block], [0,1,2], None, [8,8,8], [0,256]*3)
            hist_template = cv2.calcHist([template], [0,1,2], None, [8,8,8], [0,256]*3)
            hist_score = cv2.compareHist(hist_block, hist_template, cv2.HISTCMP_CORREL)

            # 特征3: 模板匹配
            match_result = cv2.matchTemplate(resized_block, template, cv2.TM_CCOEFF_NORMED)
            _, template_score, _, _ = cv2.minMaxLoc(match_result)

            # 综合评分（可调节权重）
            combined_score = 0.8*ssim_score + 0.8*hist_score + 0.8*template_score

            if combined_score > max_confidence:
                max_confidence = combined_score
                best_match = name

        return best_match, max_confidence

    def _highlight_removable_pairs(self, screen_img):
        """高亮显示所有可消除的方块对"""
        debug_img = screen_img.copy()
        removable_pairs = []

        # 检查所有可能的方块对
        positions = list(self.last_state.keys())
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                pos1, pos2 = positions[i], positions[j]
                if self.check_elimination(pos1, pos2):
                    removable_pairs.append((pos1, pos2))

        # 高亮显示可消除的方块对
        for pos1, pos2 in removable_pairs[:1]:
            x1, y1, x2, y2 = self.last_state[pos1]['coordinate']
            cv2.rectangle(debug_img, (int(x1), int(y1)), (int(x2), int(y2)), (255, 255, 0), 3)  # 青色框
            x1, y1, x2, y2 = self.last_state[pos2]['coordinate']
            cv2.rectangle(debug_img, (int(x1), int(y1)), (int(x2), int(y2)), (255, 255, 0), 3)  # 青色框

        self.debug_window.update(debug_img, f"可消除的方块对: {len(removable_pairs)} 对")

    def check_elimination(self, pos1, pos2):
        """
        检查两个方块是否可以消除
        :param pos1: 第一个方块的网格坐标 (col1, row1)
        :param pos2: 第二个方块的网格坐标 (col2, row2)
        :return: 是否可以消除
        """
        # 基础检查：类型相同且不为空
        if self.last_state[pos1]['name'] != self.last_state[pos2]['name']:
            return False
        if self.last_state[pos1]['name'] == "None" or self.last_state[pos2]['name'] == "None":
            return False
    
        # 检查直接相连的直线路径
        if self._is_directly_connected(pos1, pos2):
            return True
    
        # 检查单拐点路径（两种类型）
        return (self._check_corner_path(pos1, pos2) or
                self._check_corner_path(pos2, pos1))
    
    def _is_directly_connected(self, pos1, pos2):
        """检查直线连通性"""
        col1, row1 = pos1
        col2, row2 = pos2
    
        if col1 == col2:
            return self._is_vertical_clear(col1, row1, row2)
        if row1 == row2:
            return self._is_horizontal_clear(col1, row1, col2)
        return False
    
    def _check_corner_path(self, posA, posB):
        """检查拐点路径（A->拐点->B）"""
        colA, rowA = posA
        colB, rowB = posB
    
        # 水平拐点检查（A先水平移动，再垂直移动）
        if self._is_horizontal_clear(colA, rowA, colB) and \
                self._is_vertical_clear(colB, rowA, rowB) and \
                self.last_state.get((colB, rowA), {}).get('name') == "None":
            return True
    
        # 垂直拐点检查（A先垂直移动，再水平移动）
        if self._is_vertical_clear(colA, rowA, rowB) and \
                self._is_horizontal_clear(colA, rowB, colB) and \
                self.last_state.get((colA, rowB), {}).get('name') == "None":
            return True
    
        return False
    
    def _is_horizontal_clear(self, start_col, row, end_col):
        """检查水平路径是否畅通"""
        if start_col == end_col:
            return True
        step = 1 if end_col > start_col else -1
        for col in range(start_col + step, end_col, step):
            if self.last_state.get((col, row), {}).get('name') != "None":
                return False
        return True
    
    def _is_vertical_clear(self, col, start_row, end_row):
        """检查垂直路径是否畅通"""
        if start_row == end_row:
            return True
        step = 1 if end_row > start_row else -1
        for row in range(start_row + step, end_row, step):
            if self.last_state.get((col, row), {}).get('name') != "None":
                return False
        return True
                