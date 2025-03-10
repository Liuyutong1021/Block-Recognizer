import os
import cv2

def load_templates(template_dir):
    """
    加载模板图片并确保尺寸一致
    :param template_dir: 模板图片目录
    :return: 模板字典 {name: image}
    """
    templates = {}
    for filename in os.listdir(template_dir):
        if filename.endswith(".png"):
            name = os.path.splitext(filename)[0]
            img_path = os.path.join(template_dir, filename)

            # 读取彩色图像
            img = cv2.imread(img_path, cv2.IMREAD_COLOR)
            if img is None:
                print(f"警告: 无法加载模板图片 {filename}")
                continue

            # 确保模板尺寸正确
            if img.shape[:2] != (82, 78):  # 高度82，宽度78
                img = cv2.resize(img, (78, 82), interpolation=cv2.INTER_AREA)

            templates[name] = img

    print(f"加载了 {len(templates)} 个模板")
    return templates