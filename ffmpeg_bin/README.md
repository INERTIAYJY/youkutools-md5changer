# ffmpeg_bin

程序运行时需要的 FFmpeg 可执行文件（约 220MB），**未随 git 仓库提交**，请手动放置：

| 文件 | 必需 | 说明 |
| --- | --- | --- |
| `ffmpeg.exe` | ✅ 必需 | 视频编码 / 信息解析 |
| `ffprobe.exe` | 可选 | 存在时分析阶段优先使用 JSON 输出 |

## 下载

- gyan.dev 完整版: <https://www.gyan.dev/ffmpeg/builds/>
- BtbN 构建: <https://github.com/BtbN/FFmpeg-Builds/releases>

建议选择 `ffmpeg-release-full` 版本，解压后把 `bin\ffmpeg.exe`（和可选的 `bin\ffprobe.exe`）复制到本目录即可。

> 提示：旧版 V1 项目打包时使用 FFmpeg 8.1 (gyan.dev full_build)。
