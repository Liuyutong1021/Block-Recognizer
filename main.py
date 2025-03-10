from debug_window import DebugWindow
from screen_selector import select_region
from template_loader import load_templates
from block_recognizer import BlockRecognizer
import cv2

def main():
    try:
        # 选择屏幕区域
        print("请框选游戏区域...")
        screen_region = select_region()
        print("已选择区域:", screen_region)

        # 加载模板
        template_dir = "block_templates"
        templates = load_templates(template_dir)
        if not templates:
            print("未找到模板图片，请检查block_templates文件夹")
            return

        # 初始化识别器
        recognizer = BlockRecognizer(screen_region, templates)
        recognizer.debug_window = DebugWindow()

        bLoop = True
        # 主循环
        while True:
            if bLoop:
                bLoop = recognizer.process_frame()
            key = cv2.waitKey(100) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('h'):  # 按h显示可消除的方块对
                screen_img = recognizer._capture_screen()
                recognizer.process_frame()
                recognizer._highlight_removable_pairs(screen_img)

    # except Exception as e:
    #     print(f"程序出错: {e}")
    finally:
        recognizer.debug_window.close()

if __name__ == "__main__":
    main()