# youkutools-md5changer

视频 MD5 重构工具（Windows 桌面应用，PySide6）。通过 FFmpeg 重新编码视频来修改文件 MD5，支持批量任务、分辨率/码率预设、一键适配 AI 导入格式、深浅主题等。

## 仓库结构

```text
youkutools-md5changer
├─ rebuild_2nd_MD5change\    V2 主项目 (Python 包 md5_rebuilder)
├─ conversion.txt            V1 项目开发记录 (历史资料)
└─ README.md
```

## 快速开始

```powershell
cd rebuild_2nd_MD5change
python -m pip install -r requirements.txt
python main.py
```

> 注意：`rebuild_2nd_MD5change\ffmpeg_bin\ffmpeg.exe`（约 220MB）未随仓库提交，运行前请按 [ffmpeg_bin/README.md](rebuild_2nd_MD5change/ffmpeg_bin/README.md) 放置 FFmpeg。

详细说明见 [rebuild_2nd_MD5change/README.md](rebuild_2nd_MD5change/README.md)。
