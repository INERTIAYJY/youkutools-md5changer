# 视频 MD5 重构工具V2

`rebuild_2nd_MD5change` 是视频 MD5 修改工具的 V2 重构版本。项目没有沿用旧版 `video_md5_changer` 的 UI 和内部实现，而是重新拆分为 `md5_rebuilder` 包，重建了桌面界面、任务队列、FFmpeg 编码链路、配置保存、测试与打包流程。

## 当前状态

- 应用名称：视频 MD5 重构工具V2
- 作者：YJY
- 主包名：`md5_rebuilder`
- 主要入口：`main.py`、`python -m md5_rebuilder`
- 打包产物：`dist\视频MD5重构工具.exe`
- 默认配置文件：`~\.video_md5_changer\settings.json`

## 主要功能

- 批量添加视频，支持文件选择和拖拽导入。
- 导入新素材后自动清空输出目录，重新打开软件时输出目录也默认清空。
- 自动分析视频宽高、时长、大小，并按横版/竖版推荐预设。
- 支持 `720p 横版`、`720p 竖版`、`1080p 横版`、`1080p 竖版`。
- 支持 `CRF 质量优先` 和 `CBR 固定码率` 两种编码模式。
- `CRF`、`码率 Mbps`、`开始秒`、`结束秒` 支持直接输入、上下箭头调整，也支持鼠标按住左右拖动调整。
- 右侧输出设置提供 `重置` 按钮，可一键恢复默认输出参数。
- 支持输出音频开关，默认输出音频；关闭后 FFmpeg 使用 `-an` 去除音频。
- 支持启用截取，按开始秒和结束秒输出指定时间段。
- 支持原目录输出或指定目录输出。
- 保持导入视频原文件名作为输出基础名，避免输出名变成分辨率预设名。
- 底部使用一个状态按钮：空闲时为 `开始重构`，运行时切换为 `取消任务`。
- 最多 4 个并发转码任务。
- 显示总进度、任务队列状态、运行日志和输出 MD5。
- 支持浅色/深色主题，默认自动跟随系统；点击标题旁主题按钮可切换并保存。

## 一键适配 AI 导入格式

右侧输出设置中提供 `一键适配AI导入格式` 按钮。鼠标悬停会显示说明：

```text
按下后自动修改规格为，规格为横版/竖版 720p，码率为5Mpbs，时长默认为0-15秒
```

点击后会自动应用：

- 分辨率：按当前素材方向选择 `720p 横版` 或 `720p 竖版`
- 码率模式：`CBR 固定码率`
- 码率：`5.0 Mbps`
- 截取：启用
- 开始秒：`0.0`
- 结束秒：`15.0`
- 文件后缀：`_AI适配版`

如果还没有导入素材，则根据当前分辨率预设方向决定横版或竖版。

## 输出命名规则

输出文件始终以源视频文件名为基础：

- 原目录输出：`原文件名_后缀.ext`
- 指定目录输出：`原文件名_后缀.ext`
- 默认后缀：`new`
- 一键 AI 后缀：`_AI适配版`
- 如果目标文件已存在，会自动追加 `_1`、`_2` 等序号。

示例：

```text
input.mp4 -> input_new.mp4
input.mp4 + 一键 AI -> input_AI适配版.mp4
input.mp4 + 冲突 -> input_new_1.mp4
```

## FFmpeg 处理

> `ffmpeg_bin\ffmpeg.exe`（约 220MB）未随 git 仓库提交，运行/打包前请按 `ffmpeg_bin\README.md` 放置（gyan.dev 或 BtbN 的 release-full 构建）。

- 程序优先使用项目内置 `ffmpeg_bin\ffmpeg.exe`。
- 如果补充 `ffmpeg_bin\ffprobe.exe`，分析阶段会优先使用 ffprobe JSON。
- 如果 ffprobe 不存在或失败，会回退到 `ffmpeg -i` 文本解析。
- 编码进度通过 `-progress pipe:1` 逐行读取，避免旧版逐字符读取造成高 CPU。
- 成功编码后会记录输出文件 MD5。

## 开发运行

```powershell
python -m pip install -r requirements.txt
python main.py
```

或：

```powershell
$env:PYTHONPATH='src'
python -m md5_rebuilder
```

## 测试

项目包含核心逻辑测试，覆盖配置、命名、FFmpeg 命令、音频开关、进度解析、视频信息解析等。

```powershell
python -m pytest
```

如果系统临时目录权限异常，可以把 pytest 临时目录指到项目内：

```powershell
New-Item -ItemType Directory -Force .\verify_tmp\tmp | Out-Null
$env:TEMP=(Resolve-Path .\verify_tmp\tmp).Path
$env:TMP=$env:TEMP
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

打包输出：

```text
dist\视频MD5重构工具.exe
```

如果打包时报 `PermissionError: 拒绝访问 dist\视频MD5重构工具.exe`，通常是旧 EXE 正在运行。关闭旧进程后重新打包即可。

## 项目结构

```text
rebuild_2nd_MD5change
├─ build\                 PyInstaller spec 和打包脚本
├─ docs\                  架构说明
├─ ffmpeg_bin\            内置 FFmpeg/FFprobe 目录
├─ resources\             图标和控件箭头资源
├─ src\
│  ├─ run.py              PyInstaller 入口
│  └─ md5_rebuilder\
│     ├─ app.py           应用启动入口
│     ├─ core\            数据模型、命名、MD5 等核心逻辑
│     ├─ services\        视频探测、任务规划、编码执行
│     ├─ ui\              PySide6 主窗口、样式、工作线程
│     └─ utils\           配置、路径、日志、格式化工具
└─ tests\                 单元测试
```

## 最近修改记录

- 顶部标题改为 `视频 MD5 重构工具V2`。
- 顶部说明保留功能说明，并标注 `作者：YJY`。
- 将主题切换按钮移动到标题旁边。
- 新增浅色/深色主题切换，默认跟随系统。
- 新增输出音频开关，默认开启。
- 开始和取消合并为右下角单一状态按钮。
- 新增 `一键适配AI导入格式`，并移动到 `输出音频 / 启用截取` 旁边。
- 一键 AI 会自动设置 720p、CBR 5.0 Mbps、0-15 秒截取和 `_AI适配版` 后缀。
- `CRF`、`码率 Mbps`、`开始秒`、`结束秒` 支持鼠标左右拖动调节。
- 数值拖动触发区域扩大到整条设置行，不再局限于输入框内部。
- 输出目录已独立为任务队列上方的整行设置。
- 新增 `重置` 按钮，用于恢复默认分辨率、码率、后缀、音频和截取设置。
- 修复输出目录保存旧路径的问题：导入新素材和重新启动后默认清空。
- 修复输出命名错误：输出文件继续沿用导入视频名称。
