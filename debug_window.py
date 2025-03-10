import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

class DebugWindow:
    def __init__(self):
        self.window_name = "Debug"
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 921, 1297)  # 初始默认尺寸

    def update(self, img, info="", pairs = []):
        """动态调整窗口尺寸并优化文字显示（支持中文）"""
        # 计算合适窗口尺寸（原图尺寸+20像素边框）
        h, w = img.shape[:2]

        # 提高分辨率：将图像放大到更高分辨率
        target_w = int(w)
        target_h = int(h)

        # 高质量缩放（使用 Lanczos 插值）
        display_img = cv2.resize(img, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)

        # 如果 info 不为空，添加中文文字
        if info:
            # 将 OpenCV 图像转换为 PIL 图像
            display_img_pil = Image.fromarray(cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(display_img_pil)

            # 加载中文字体（确保字体文件路径正确）
            font_path = "simsun.ttc"  # 使用宋体，或者替换为其他支持中文的字体文件
            font = ImageFont.truetype(font_path, 24)  # 字体大小随分辨率放大

            # 绘制中文文字（启用抗锯齿）
            draw.text((20, 20), info, font=font, fill=(255, 0, 0), antialias=True)

            # 将 PIL 图像转换回 OpenCV 格式
            display_img = cv2.cvtColor(np.array(display_img_pil), cv2.COLOR_RGB2BGR)

        if pairs:
            for (a, b) in pairs:
                (col1, row1), (col2, row2) = a, b
                x1 = (a_coord[0] + a_coord[2]) // 2  # 方块中心坐标
                y1 = (a_coord[1] + a_coord[3]) // 2
                x2 = (b_coord[0] + b_coord[2]) // 2
                y2 = (b_coord[1] + b_coord[3]) // 2
                cv2.line(display_img, (x1, y1), (x2, y2), (0, 255, 255), 2)
                cv2.putText(display_img, f"Pair", (x1+5, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 1)

        # 更新窗口
        cv2.imshow(self.window_name, display_img)
        cv2.waitKey(1)

    def close(self):
        """关闭调试窗口"""
        cv2.destroyAllWindows()