# PalmControl

[English Version](README.md)

## 概述

PalmControl 是一款桌面应用程序，旨在通过网络摄像头实现免提的计算机操作。它能够实时捕捉并解析手势和面部动作，并将其转换成本地的鼠标和键盘事件，为用户提供一种全新的、直观的人机交互方式。

本应用采用模块化、可扩展的架构设计，并优先考虑了性能和用户体验。它内置了可切换的计算机视觉后端，允许用户在处理速度和识别精度之间进行权衡，选择使用依赖CPU的引擎或GPU加速的引擎。

## 核心功能

- **基于手势的输入模拟**:
  - **鼠标控制**: 将手部或头部的位置平滑、低延迟地映射为光标移动。
  - **点击事件**: 区分不同的手势以实现左键和右键点击（例如，捏合手势与“V”字手势）。
  - **滚动**: 通过手势控制垂直滚动。
- **系统集成**:
  - **系统托盘图标**: 程序在后台静默运行，系统托盘图标提供了快速控制功能，包括启动/停止识别、打开设置面板和退出程序。
  - **跨平台开机自启**: 在设置面板中可以轻松设置开机自启动，支持 Windows、macOS 和 Linux 系统。
- **配置与定制**:
  - **现代化图形界面**: 基于 `customtkinter` 的简洁美观的设置面板，方便用户调整各项参数。
  - **识别引擎切换**: 用户可以在 `mediapipe` (CPU) 和 `gpu` (占位符) 识别引擎之间自由切换。
  - **摄像头选择**: 如果连接了多个摄像头，用户可以选择使用哪一个。
  - **灵敏度调节**: 根据个人偏好调整光标移动的灵敏度。
  - **配置持久化**: 所有用户设置将保存在 `config.json` 文件中，并在下次启动时自动加载。

## 软件架构

本应用由以下几个核心模块组成：

- **`main.py`**: 应用程序的入口点，负责初始化所有组件、管理应用生命周期，并处理摄像头画面捕捉和系统托盘图标的多线程任务。
- **`app_gui.py`**: 管理基于 `customtkinter` 的图形用户界面，包括设置窗口及其所有交互元素。
- **`config_manager.py`**: 用于读写 `config.json` 文件的工具模块，确保用户设置能够持久化保存。
- **`input_controller.py`**: 将识别器输出的归一化坐标转换为操作系统级的鼠标和键盘事件。
- **`autostart_manager.py`**: 跨平台的开机自启动功能模块。
- **`recognizers/`**:
  - **`__init__.py`**: 使目录成为一个 Python 包。
  - **`mediapipe_recognizer.py`**: 默认的、基于CPU的识别引擎，由 Google 的 MediaPipe 框架驱动，负责手部跟踪和基本的手势识别。
  - **`gpu_recognizer.py`**: 一个占位符模块，为未来集成更强大的、基于GPU加速的自定义模型（如 PyTorch 或 TensorFlow）提供了清晰的接口。

## 快速开始

### 环境要求

- Python 3.8 或更高版本
- 一个连接到电脑并能正常工作的网络摄像头

### 安装步骤

1.  **克隆代码仓库**:

    ```bash
    git clone https://github.com/your-username/PalmControl.git
    cd PalmControl
    ```
2.  **创建并激活虚拟环境**:

    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows 用户请使用 `venv\Scripts\activate`
    ```
3.  **安装依赖**:

    ```bash
    pip install -r requirements.txt
    ```

### 运行程序

在项目根目录下执行以下命令：

```bash
python main.py
```

如果希望在启动时直接显示设置界面（即使已设置为静默启动），请使用 `--show` 参数：

```bash
python main.py --show
```

## 打包为可执行文件

您可以使用 PyInstaller 将本应用打包成一个独立的可执行文件，以便于分发。

1.  **安装 PyInstaller**:

    ```bash
    pip install pyinstaller
    ```
2.  **根据您的操作系统执行打包命令**:

    **Windows**:
    ```bash
    pyinstaller --noconfirm --onefile --windowed --add-data "icon.png;." --add-data "config.json;." --name "PalmControl" main.py
    ```

    **macOS**:
    ```bash
    pyinstaller --noconfirm --onefile --windowed --add-data "icon.png:." --add-data "config.json:." --hidden-import="pystray._darwin" --name "PalmControl" main.py
    ```

    **Linux**:
    ```bash
    pyinstaller --noconfirm --onefile --windowed --add-data "icon.png:." --add-data "config.json:." --name "PalmControl" main.py
    ```

    打包完成后，可执行文件将生成在 `dist/` 目录下。

## 贡献代码

我们欢迎各种形式的贡献，无论是功能建议、代码优化还是错误修复。如果您有兴趣参与，请遵循以下步骤：

1.  Fork 本仓库。
2.  创建一个新的分支 (`git checkout -b feature/your-feature-name`)。
3.  提交您的更改 (`git commit -m 'Add some amazing feature'`)。
4.  将您的分支推送到远程仓库 (`git push origin feature/your-feature-name`)。
5.  创建一个新的 Pull Request。

## 许可证

本项目采用 [MIT 许可证](LICENSE)。
