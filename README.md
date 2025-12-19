# AI 更新翻译官 (AI Update Translator)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)
![Version](https://img.shields.io/badge/version-1.0.1-blue.svg?style=for-the-badge)

一个利用 Home Assistant 内置 AI 会话代理（Conversation Agent）自动翻译软件更新日志的集成。

## 🌟 功能特点

- **自动翻译**：实时监控所有 `update` 实体，发现新版本时自动翻译更新摘要（Release Summary）。
- **原生体验**：直接修改 `update` 实体的属性，使翻译后的内容直接显示在 Home Assistant 标准更新卡片中。
- **灵活配置**：支持选择任意已安装的 AI 会话代理（如 OpenAI, Gemini, Ollama 等）。
- **深度适配**：支持从 GitHub Release URL 自动抓取详细的更新日志并进行翻译。

## 🚀 安装说明

### 方法 1: 通过 HACS 安装 (推荐)

1. 打开 Home Assistant，进入 **HACS** 面板。
2. 点击右上角的三个点，选择 **自定义存储库 (Custom repositories)**。
3. 输入地址：`https://github.com/farion1231/ai_update_translator`
4. 类别选择 **集成 (Integration)**。
5. 点击 **添加**，然后在列表中找到 **AI 更新翻译官** 并点击 **下载**。
6. 重启 Home Assistant。

### 方法 2: 手动安装

1. 下载本仓库。
2. 将 `custom_components/ai_update_translator` 文件夹复制到你的 Home Assistant 配置目录下的 `custom_components` 文件夹中。
3. 重启 Home Assistant。

## ⚙️ 配置方法

1. 进入 **设置 -> 设备与服务**。
2. 点击右下角的 **添加集成**。
3. 搜索并选择 **AI 更新翻译官**。
4. 在配置窗口中：
   - 选择你想要使用的 **AI 系统 (Conversation Agent)**。
   - (可选) 修改 **翻译提示词 (Prompt)** 以调整翻译风格。

## 💡 使用提示

- 确保你已经安装并配置了至少一个 **会话代理 (Conversation Agent)**，如 OpenAI 或 Google Generative AI。
- 集成会自动处理所有 `update` 实体，你不需要为每个设备单独配置。

## 👤 作者

[@farion1231](https://github.com/farion1231)

## 📄 许可证

MIT License
