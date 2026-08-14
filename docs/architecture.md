# 架构说明

## 模块

- `core.models`: 纯数据模型和枚举。
- `core.naming`: 输出文件命名。
- `core.hashing`: MD5 计算。
- `services.probe`: 视频信息探测。
- `services.planner`: 从素材和输出方案生成任务。
- `services.encoder`: FFmpeg 命令构建、进度解析、取消。
- `ui.main_window`: 新工作台式 UI 和调度。

## 数据流

1. 用户添加视频。
2. `ProbeThread` 调用 `MediaProbe` 分析视频。
3. UI 根据第一个视频自动建议分辨率和码率。
4. 用户点击开始后，`JobPlanner` 生成 `RenderJob`。
5. `EncodeThread` 调用 `VideoEncoder` 执行 FFmpeg。
6. UI 根据进度和完成信号刷新任务队列。

