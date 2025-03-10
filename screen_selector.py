import cv2
import ctypes
import platform
import utils
import tkinter as tk
import numpy as np
from PIL import ImageGrab, ImageTk, Image

class ScreenshotApp:
    def __init__(self, master):
        # 屏幕参数初始化
        if platform.system() == "Windows":
            self.user32 = ctypes.windll.user32
            self.scale_factor = utils.get_scaling_factor()
            self.screen_width = self.user32.GetSystemMetrics(0)
            self.screen_height = self.user32.GetSystemMetrics(1)
        else:
            # 跨平台替代方案（例如 Linux/macOS）
            self.scale_factor = 1.0
            screen = ImageGrab.grab()
            self.screen_width, self.screen_height = screen.size

        # 窗口配置
        self.master = master
        self.master.attributes("-fullscreen", True)
        self.master.attributes("-alpha", 0.3)
        self.master.configure(bg='black')
        self.master.bind("<Escape>", self.cancel_screenshot)

        # 截图画布
        self.canvas = tk.Canvas(self.master, cursor="cross", bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 状态变量
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.selection = None
        self.magnifier_size = 150  # 放大镜尺寸
        self.magnifier_scale = 2   # 放大倍数
        self.magnifier_window = None
        self.magnifier_label = None
        self.dragging = False  # 标记是否正在拖动

        # 绑定事件
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Motion>", self.show_magnifier)

        # 界面元素
        self.create_info_panel()

    def _get_windows_scaling(self):
        """获取系统缩放比例（仅限 Windows）"""
        hdc = self.user32.GetDC(0)
        LOGPIXELSX = 88
        scaling = ctypes.windll.gdi32.GetDeviceCaps(hdc, LOGPIXELSX) / 96
        self.user32.ReleaseDC(0, hdc)
        return scaling

    def create_info_panel(self):
        """创建信息面板"""
        self.info_text = tk.StringVar()
        self.info_label = tk.Label(self.canvas,
                                   textvariable=self.info_text,
                                   font=("Arial", 12),
                                   bg='#404040',
                                   fg='white',
                                   relief=tk.RAISED)
        self.info_label.place(x=10, y=10)

    def update_info(self, x1, y1, x2, y2):
        """更新信息面板"""
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        self.info_text.set(f"坐标: ({x1}, {y1})  尺寸: {width}x{height}")

    def on_press(self, event):
        self.dragging = True
        """鼠标按下事件"""
        try:
            self.start_x = self.master.winfo_pointerx()
            self.start_y = self.master.winfo_pointery()
            self.rect = self.canvas.create_rectangle(0, 0, 0, 0,
                                                     outline='#00ff00',
                                                     width=10,
                                                     dash=(4, 4))
        except Exception as e:
            print(f"Error in on_press: {e}")
            self.cancel_screenshot()

    def on_drag(self, event):
        """鼠标拖动事件"""
        try:
            # 新增：拖动时强制更新放大镜
            if self.dragging:
                self.show_magnifier(event)
            cur_x = self.master.winfo_pointerx()
            cur_y = self.master.winfo_pointery()

            # 更新选区
            self.canvas.coords(self.rect,
                               self.start_x, self.start_y,
                               cur_x, cur_y)

            # 更新信息面板
            self.update_info(self.start_x, self.start_y, cur_x, cur_y)

            # 更新遮罩
            self.update_mask(cur_x, cur_y)
        except Exception as e:
            print(f"Error in on_drag: {e}")

    def update_mask(self, end_x, end_y):
        """更新遮罩区域"""
        try:
            self.canvas.delete("mask")
            x1, y1 = min(self.start_x, end_x), min(self.start_y, end_y)
            x2, y2 = max(self.start_x, end_x), max(self.start_y, end_y)

            # 绘制四个遮罩区域
            self.canvas.create_rectangle(0, 0, self.screen_width, y1,
                                         fill='#000000', stipple='gray50', tags="mask")
            self.canvas.create_rectangle(0, y2, self.screen_width, self.screen_height,
                                         fill='#000000', stipple='gray50', tags="mask")
            self.canvas.create_rectangle(0, y1, x1, y2,
                                         fill='#000000', stipple='gray50', tags="mask")
            self.canvas.create_rectangle(x2, y1, self.screen_width, y2,
                                         fill='#000000', stipple='gray50', tags="mask")
        except Exception as e:
            print(f"Error in update_mask: {e}")

    def show_magnifier(self, event):
        """显示/更新放大镜窗口"""
        try:
            # 如果窗口已存在则更新，否则创建
            if not self.magnifier_window or not self.magnifier_window.winfo_exists():
                self._create_magnifier_window()

            # 实时更新位置和内容
            self._update_magnifier_position(event)
            self.update_magnifier_content(event)

        except Exception as e:
            print(f"Error in show_magnifier: {e}")

    def _create_magnifier_window(self):
        """创建放大镜窗口"""
        self.magnifier_window = tk.Toplevel(self.master)
        self.magnifier_window.overrideredirect(True)
        self.magnifier_label = tk.Label(self.magnifier_window)
        self.magnifier_label.pack()

    def _update_magnifier_position(self, event):
        """动态调整窗口位置避免超出屏幕"""
        x, y = event.x_root + 20, event.y_root + 20  # 基础偏移量
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        # 动态调整位置
        window_size = self.magnifier_size * self.magnifier_scale
        if x + window_size > screen_width:
            x = event.x_root - window_size - 20  # 左侧显示
        if y + window_size > screen_height:
            y = event.y_root - window_size - 20  # 上方显示

        self.magnifier_window.geometry(f"+{x}+{y}")

    def update_magnifier_content(self, event):
        """优化后的内容更新方法"""
        try:
            # 计算实际抓取坐标（考虑缩放）
            x = int(event.x_root * self.scale_factor)
            y = int(event.y_root * self.scale_factor)
            size = self.magnifier_size

            # 抓取屏幕区域
            grab_area = (
                x - size//2, y - size//2,
                x + size//2, y + size//2
            )

            # 优化图像处理流程
            img = ImageGrab.grab(grab_area).convert("RGB")
            img = img.resize((size, size))  # 初次缩放

            # 应用放大倍数（使用更高效的NEAREST插值）
            img = img.resize(
                (int(size * self.magnifier_scale),
                 int(size * self.magnifier_scale)),
                resample=Image.NEAREST
            )

            # 转换为OpenCV格式添加十字线
            cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            h, w = cv_img.shape[:2]
            cv2.line(cv_img, (w//2, 0), (w//2, h), (0, 255, 0), 1)
            cv2.line(cv_img, (0, h//2), (w, h//2), (0, 255, 0), 1)

            # 更新图像（使用PhotoImage缓存优化）
            photo = ImageTk.PhotoImage(image=Image.fromarray(cv_img))
            self.magnifier_label.config(image=photo)
            self.magnifier_label.image = photo  # 保持引用

        except Exception as e:
            print(f"Error in update_magnifier_content: {e}")

    def on_release(self, event):
        """鼠标释放事件"""
        self.dragging = False  # 清除拖动标记
        try:
            end_x = self.master.winfo_pointerx()
            end_y = self.master.winfo_pointery()

            # 标准化坐标
            x1 = int(min(self.start_x, end_x) * self.scale_factor)
            y1 = int(min(self.start_y, end_y) * self.scale_factor)
            x2 = int(max(self.start_x, end_x) * self.scale_factor)
            y2 = int(max(self.start_y, end_y) * self.scale_factor)

            # 有效区域检查
            if abs(x2 - x1) < 10 or abs(y2 - y1) < 10:
                self.cancel_screenshot()
                return

            self.selection = (x1, y1, x2, y2)
            self.master.quit()
        except Exception as e:
            print(f"Error in on_release: {e}")
            self.cancel_screenshot()

    def cancel_screenshot(self, event=None):
        """取消截图"""
        self.selection = None
        self.master.quit()

    def get_selection(self):
        """获取选区"""
        self.master.mainloop()
        self.master.destroy()
        return self.selection

def select_region():
    root = tk.Tk()
    root.withdraw()
    app = ScreenshotApp(tk.Toplevel())
    return app.get_selection()