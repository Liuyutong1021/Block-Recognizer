![](icon.png)
# Block Recognizer (方块识别器)

一个用于自动识别和消除游戏中方块的工具，支持自动校准、多模板匹配、连通性检测等功能。适用于"砖了个砖"的辅助程序。

## 功能特性

- **自动校准**：通过模板匹配自动定位初始方块位置
- **多线程模板匹配**：并行加速识别过程
- **动态调试窗口**：实时显示识别结果和校准状态
- **连通性检测**：支持直线和单拐点路径检查
- **高精度识别**：结合SSIM、颜色直方图和模板匹配的综合评分算法
- **屏幕缩放适配**：自动处理不同DPI缩放比例

## 依赖项

- Python 3.7+
- OpenCV (`pip install opencv-python`)
- Pillow (`pip install Pillow`)
- scikit-image (`pip install scikit-image`)
- NumPy (`pip install numpy`)

## 安装指南

bash
git clone https://github.com/Liuyutong1021/BlockAnalyzer.git
cd BlockAnalyzer


## 使用方法

1. **准备模板**：
    - 将方块模板图片（PNG格式）放入 `block_templates` 目录（目前已备好基础样式）
    - 命名规则：`方块名称.png`（如 `baicai.png`, `luobo.png`）
    - 图片尺寸应为 78×82 像素（宽×高）

2. **运行程序**：
   ```bash
   python main.py
   ```

3. **操作指引**：
    - 启动后框选游戏区域（按ESC取消）
    - 自动校准成功后进入识别模式
    - 按 `H` 高亮可消除方块对
    - 按 `Q` 退出程序

## 项目结构

```
.
├── block_recognizer.py    # 核心识别逻辑
├── debug_window.py        # 调试窗口实现
├── main.py                # 主程序入口
├── screen_selector.py     # 屏幕区域选择工具
├── template_loader.py     # 模板加载模块
├── utils.py               # 系统工具函数
└── block_templates/       # 模板图片目录
```

## 配置参数

在 `block_recognizer.py` 中可调整：
```python
self.block_w, self.block_h = 78, 82   # 单个方块尺寸
self.grid_cols, self.grid_rows = 10, 14  # 网格行列数
self.h_gap = 7   # 横向间隙
self.v_gap = 3   # 纵向间隙
```

## 常见问题

**Q: 校准失败怎么办？**  
A: 检查生成的 `debug_failed_calibration.png`，确保：
1. 模板图片与游戏方块完全匹配
2. 框选的区域包含完整方块
3. 模板图片尺寸正确（78×82）

**Q: 识别准确率低怎么办？**  
A: 尝试：
1. 增加模板图片数量和多样性
2. 调整 `_match_block` 中的权重参数
3. 检查屏幕缩放比例设置

**Q: 路径检测不准确？**  
A: 确认：
1. `h_gap` 和 `v_gap` 参数与实际间隙匹配
2. 游戏区域没有动态特效干扰

## 开发指南

欢迎贡献！

## 许可证

[MIT License](LICENSE) © 2025 Liuyutong1021

---

> **注意**：本项目仅供学习和技术研究用途，请遵守相关游戏的使用条款。