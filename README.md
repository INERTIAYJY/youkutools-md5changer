# 视频 MD5 重构工具 V2

Windows 桌面应用（Python + PySide6），通过 **FFmpeg 重新编码**视频来修改文件 MD5。支持批量任务、分辨率/码率预设、一键适配 AI 导入格式、深/浅主题等。

- 主包名：`md5_rebuilder`
- 入口：`python main.py` 或 `python -m md5_rebuilder`
- 打包产物：`dist\视频MD5重构工具.exe`

## 功能特性

- 批量添加视频，支持文件选择和拖拽导入。
- 自动分析视频宽高、时长、大小，并按横版/竖版推荐预设。
- 支持 `720p 横版` / `720p 竖版` / `1080p 横版` / `1080p 竖版` 四档预设。
- 支持 `CRF 质量优先` 和 `CBR 固定码率` 两种编码模式。
- CRF、码率、开始秒、结束秒支持直接输入、上下箭头调整，也支持鼠标按住整行左右拖动调整。
- 输出音频开关（关闭后 FFmpeg 使用 `-an` 去音频）；支持按时间段截取。
- 支持原目录输出或指定目录输出；保持源文件名作为输出基础名，冲突自动追加 `_1`、`_2` 序号。
- 底部单一状态按钮：空闲时为 `开始重构`，运行时切换为 `取消任务`。
- 最多 4 个并发转码任务，显示总进度、任务队列、运行日志和输出 MD5。
- `一键适配AI导入格式`：自动应用 720p 横/竖版、CBR 5.0 Mbps、0–15 秒截取、`_AI适配版` 后缀。
- 浅色/深色主题，默认自动跟随系统。

## 快速开始

```powershell
python -m pip install -r requirements.txt
python main.py
```

或使用 src 布局运行：

```powershell
$env:PYTHONPATH = 'src'
python -m md5_rebuilder
```

> ⚠️ **FFmpeg**：`ffmpeg_bin\ffmpeg.exe`（约 220MB）未随仓库提交，运行/打包前请按 [ffmpeg_bin/README.md](ffmpeg_bin/README.md) 放置（gyan.dev 或 BtbN 的 release-full 构建）。

## 测试

```powershell
python -m pytest
```

若系统临时目录权限异常，可把 pytest 临时目录指到项目内：

```powershell
New-Item -ItemType Directory -Force .\verify_tmp\tmp | Out-Null
$env:TEMP = (Resolve-Path .\verify_tmp\tmp).Path
$env:TMP = $env:TEMP
python -m pytest -q -p no:cacheprovider --basetemp=.\verify_tmp\pytest_tmp
```

## 打包

```powershell
build\build.bat
```

或直接运行：

```powershell
python -m PyInstaller build\app.spec --clean --noconfirm
```

打包输出：`dist\视频MD5重构工具.exe`。若提示 `PermissionError: 拒绝访问`，通常是旧 EXE 正在运行，关闭后重试。

## 项目结构

```text
.
├─ build\                 PyInstaller 打包脚本（app.spec / build.bat）
├─ docs\                  架构说明与 V1 开发记录
├─ ffmpeg_bin\            内置 FFmpeg/FFprobe 目录（不入库）
├─ src\
│  ├─ run.py              PyInstaller 入口
│  └─ md5_rebuilder\
│     ├─ app.py           应用启动入口
│     ├─ core\            数据模型、命名、MD5 等核心逻辑
│     ├─ resources\       图标和控件箭头资源
│     ├─ services\        视频探测、任务规划、编码执行
│     ├─ ui\              PySide6 主窗口、样式、工作线程
│     └─ utils\           配置、路径、日志、格式化工具
├─ tests\                 单元测试
├─ main.py                开发入口
├─ pyproject.toml         工程元数据与工具链配置（pytest / ruff）
├─ requirements.txt       运行时依赖
└─ LICENSE                MIT 许可
```

## 配置与日志

- 配置文件：`~\.md5_rebuilder\settings.json`（输出目录不持久化，重启后默认清空）
- 日志文件：`~\.md5_rebuilder\logs\app.log`

## 相关文档

- [docs/architecture.md](docs/architecture.md) — 模块架构与数据流
- [docs/conversion.txt](docs/conversion.txt) — V1 项目开发记录（历史资料）

## 许可

[MIT License](LICENSE)
