# PalmControl

[阅读中文版说明](README_zh-CN.md)

## Overview

PalmControl is a desktop application for hands-free computer operation, driven by a webcam. It captures and interprets hand gestures and facial movements in real-time, translating them into native mouse and keyboard events. This provides an alternative, intuitive input modality for interacting with the host operating system and its applications.

The application is built with a modular and extensible architecture, prioritizing performance and user experience. It features a switchable backend for computer vision tasks, allowing users to balance between processing speed and recognition accuracy by choosing a CPU-bound or a GPU-accelerated engine.

## Core Features

- **Gesture-based Input Emulation**: 
  - **Mouse Control**: Smooth, low-latency cursor movement mapped to hand or head position.
  - **Click Events**: Differentiates between left and right-click gestures (e.g., finger pinch vs. V-sign).
  - **Scrolling**: Vertical scrolling controlled by hand gestures.
- **System Integration**:
  - **System Tray Icon**: Runs unobtrusively in the background. The tray icon provides essential controls to start/stop recognition, open the settings panel, and exit the application.
  - **Cross-Platform Autostart**: A toggle in the settings panel configures the application to launch automatically at system startup. This is handled gracefully across Windows, macOS, and Linux.
- **Configuration and Customization**:
  - **Modern GUI**: A clean, user-friendly settings panel built with `customtkinter` allows for easy adjustment of all parameters.
  - **Engine Selection**: Switch between the `mediapipe` (CPU) and `gpu` (placeholder) recognizer backends.
  - **Camera Selection**: If multiple cameras are present, the user can select the desired input source.
  - **Sensitivity Tuning**: Adjust the sensitivity of cursor movement to match user preference.
  - **Persistent Settings**: All user configurations are saved to a `config.json` file and are automatically loaded on startup.

## Architecture

The application is composed of several key modules:

- `main.py`: The entry point of the application. It initializes all components, manages the application lifecycle, and handles threading for the camera feed and system tray.
- `app_gui.py`: Manages the `customtkinter`-based graphical user interface, including the settings window and all its interactive components.
- `config_manager.py`: A robust utility for reading from and writing to the `config.json` file, ensuring that user settings persist across sessions.
- `input_controller.py`: Handles the translation of normalized coordinates from the recognizer into OS-level mouse and keyboard events using `pyautogui`.
- `autostart_manager.py`: An OS-aware module that abstracts the logic for enabling or disabling the application's auto-launch on system startup.
- `recognizers/`:
  - `__init__.py`: Makes the directory a Python package.
  - `mediapipe_recognizer.py`: The default, CPU-efficient recognition engine powered by Google's MediaPipe framework. It performs hand tracking and basic gesture recognition.
  - `gpu_recognizer.py`: A placeholder module designed for a more powerful, custom-trained, GPU-accelerated model. It provides a clear interface for developers to integrate their own deep learning models (e.g., PyTorch, TensorFlow).

## Getting Started

### Prerequisites

- Python 3.8 or newer
- A connected webcam, accessible by the OS

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-username/PalmControl.git
    cd PalmControl
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies from `requirements.txt`**:
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

Execute the main script from the project root:

```bash
python main.py
```

To show the GUI on startup, even if `start_silently` is enabled, use the `--show` flag:

```bash
python main.py --show
```

## Building a Standalone Executable

PyInstaller can be used to package the application into a single executable file for distribution.

1.  **Install PyInstaller**:
    ```bash
    pip install pyinstaller
    ```

2.  **Run the build command for your OS**:

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

    The resulting executable will be placed in the `dist/` directory.

## Contributing

We welcome contributions to improve PalmControl. If you wish to contribute, please follow these steps:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix (`git checkout -b feature/your-feature-name`).
3.  Commit your changes with clear, descriptive messages.
4.  Push your changes to the branch (`git push origin feature/your-feature-name`).
5.  Open a pull request against the `main` branch.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.