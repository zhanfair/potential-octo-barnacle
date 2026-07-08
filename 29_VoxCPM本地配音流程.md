# VoxCPM 本地配音流程

## 当前状态

- 已安装 Python 3.12.10。
- 已创建独立环境：`.venv-voxcpm/`。
- 已安装 GPU 版 PyTorch：`2.11.0+cu128`。
- PyTorch 已确认能识别本机显卡：`NVIDIA GeForce RTX 4070 Ti SUPER`。
- 已安装 VoxCPM：`voxcpm 2.0.3`。
- 已下载 VoxCPM2 模型到：`pretrained_models/`。
- 已跑通最小中文语音测试。
- 已完成一次参考声音克隆测试。

测试音频：

```powershell
voice_outputs\voxcpm_smoke_test.wav
```

测试结果：

- 采样率：48kHz
- 声道：单声道
- 时长：约 6.56 秒

参考声音：

```powershell
voice_refs\user_reference_85.m4a
voice_refs\user_reference_85.wav
voice_refs\user_reference_90.m4a
voice_refs\user_reference_90.wav
```

克隆试听：

```powershell
voice_outputs\clone_reference_85_test.wav
voice_outputs\clone_reference_90_test.wav
```

克隆试听结果：

- `clone_reference_85_test.wav`：48kHz、单声道、约 11.04 秒。
- `clone_reference_90_test.wav`：48kHz、单声道、约 13.28 秒。

## 最小测试命令

在项目目录运行：

```powershell
.venv-voxcpm\Scripts\python.exe tools\voxcpm_smoke_test.py
```

生成文件会放到：

```powershell
voice_outputs\voxcpm_smoke_test.wav
```

## 生成指定文本

```powershell
.venv-voxcpm\Scripts\python.exe tools\voxcpm_smoke_test.py --text "这里换成你要生成的中文口播。"
```

如果要指定输出文件：

```powershell
.venv-voxcpm\Scripts\python.exe tools\voxcpm_smoke_test.py --text "这里换成你要生成的中文口播。" --output voice_outputs\test_01.wav
```

## 用参考声音做克隆

把授权使用的参考声音放到：

```powershell
voice_refs\
```

推荐参考音频：

- 10 到 30 秒。
- 单人说话。
- 背景干净，没有音乐。
- 情绪和最终视频接近。
- 必须是你本人，或明确授权给你使用的声音。

当前参考音频 `user_reference_85.wav`：

- 时长：约 23.08 秒。
- 格式：48kHz、单声道 wav。
- 可直接用于 VoxCPM 克隆测试。

当前参考音频 `user_reference_90.wav`：

- 时长：约 34.85 秒。
- 格式：48kHz、单声道 wav。
- 可直接用于 VoxCPM 克隆测试。

基础克隆命令：

```powershell
.venv-voxcpm\Scripts\python.exe tools\voxcpm_smoke_test.py --text "这里是要生成的口播。" --reference-wav voice_refs\your_voice.wav --output voice_outputs\clone_test.wav
```

更强的克隆方式需要同时给参考音频和这段参考音频的逐字稿：

```powershell
.venv-voxcpm\Scripts\python.exe tools\voxcpm_smoke_test.py --text "这里是要生成的口播。" --reference-wav voice_refs\your_voice.wav --prompt-wav voice_refs\your_voice.wav --prompt-text "这里填参考音频里真实说过的话。" --output voice_outputs\clone_ultimate_test.wav
```

## 用在宫崎骏第一条视频上

下一步建议不要一次性生成完整 5 到 7 分钟音频，而是按 `26_宫崎骏第一条视频完整口播稿.md` 的 S01 到 S13 分段生成。

原因：

- 每段可以单独听，坏了只重生成一段。
- 方便和 `27_宫崎骏第一条视频画面匹配表.md` 对齐。
- 后期剪辑时更容易移动、留白、调整节奏。

推荐输出结构：

```powershell
voice_outputs\miyazaki_first_video\S01.wav
voice_outputs\miyazaki_first_video\S02.wav
voice_outputs\miyazaki_first_video\S03.wav
...
```

当前宫崎骏第一条视频已完成一次分段配音导出，记录见：

```powershell
30_宫崎骏第一条视频配音导出记录.md
```

## 注意事项

- `voice_outputs/`、`voice_refs/`、`pretrained_models/` 已加入忽略规则，不会提交到 Git。
- 第一次运行会下载模型，之后会直接复用本地缓存。
- 克隆声音只用于你本人或已获得授权的声音。
- 如果未来发布 AI 生成配音，建议在工作流或说明里保留“AI 辅助生成”的标记，避免声音使用风险。
