---
name: feedback
description: 'Use this skill when the user wants to report a bug, request a feature, give feedback, or when you detect that a scenario is unsupported. Triggers: ''bug'', ''issue'', ''problem'', ''broken'', ''not working'', ''feature request'', ''suggestion'', ''报bug'', ''提issue'', ''反馈'', ''问题'', ''不好用'', ''功能建议'', or when you realize the current task cannot be completed due to a limitation.'
---

# Feedback — 提交 Issue 到 GitHub

用户遇到 bug 或有功能建议时，帮他们直接提交 GitHub Issue。

## 前置检查

提交前必须按顺序检查：

1. **`gh` CLI 是否安装**
   ```bash
   which gh
   ```
   没有 → 提示安装：
   - macOS: `brew install gh`
   - Windows: `winget install GitHub.cli`
   - Linux: `sudo apt install gh` 或 `sudo dnf install gh`

2. **GitHub 是否已认证**
   ```bash
   gh auth status
   ```
   没有 → 提示用户执行 `gh auth login`，选 GitHub.com → HTTPS → 浏览器授权

3. **获取 GitHub 用户名**
   ```bash
   gh api user --jq .login
   ```

任何一步失败就停下，给出对应的操作指引，不要跳过。

## Issue 规范

### 标题格式

```
🐛 [Bug] <一句话描述问题>
💡 [Feature] <一句话描述需求>
```

- Bug: 以实际现象为标题，不用技术术语（"搜索结果表格无法复制" 不是 "clipboard API 异常"）
- Feature: 以用户视角描述（"支持导出为 Excel" 不是 "实现 XLSX 序列化"）

### 正文模板

**Bug:**

```markdown
## 问题描述
<!-- 一句话说清楚：做了什么 → 期望什么 → 实际发生什么 -->

## 复现步骤
1.
2.
3.

## 期望行为

## 实际行为

## 环境信息
- **App**: Cortex Desktop vX.X.X
- **平台**: macOS arm64 / Windows x64 / Linux x64
- **模式**: Chat / Cowork

---
*Submitted via Cortex Feedback Skill by @username*
```

**Feature:**

```markdown
## 需求描述
<!-- 用户想要什么能力，解决什么问题 -->

## 使用场景
<!-- 什么情况下需要这个功能 -->

## 期望行为
<!-- 理想的交互方式 -->

## 环境信息
- **App**: Cortex Desktop vX.X.X
- **平台**: macOS arm64 / Windows x64 / Linux x64

---
*Submitted via Cortex Feedback Skill by @username*
```

### Labels

- Bug → `bug`
- Feature → `enhancement`

## 环境信息自动获取

```bash
# App 版本（从 package.json）
cat package.json | jq -r .version

# 平台
uname -ms
```

如果拿不到版本号（不在项目目录），让用户提供或写 "未知"。

## 提交流程

1. **整理内容** — 从对话上下文提取问题描述、复现步骤等，按模板填充
2. **展示给用户确认** — 把完整的 title + body 展示出来，问用户 "这样提交可以吗？需要修改什么？"
3. **用户确认后提交**
   ```bash
   gh issue create \
     --repo HiQ-AI/cortex-desktop \
     --title "🐛 [Bug] ..." \
     --body "..." \
     --label "bug"
   ```
4. **返回 Issue URL** — 告诉用户 issue 已创建，附上链接

## 注意事项

- **必须用户确认后才能提交**，不能自动提交
- **不要泄露敏感信息** — 正文中不要包含 API Key、token、密码、内部 URL
- **语言跟随用户** — 用户用中文就中文写 issue，英文就英文
- **一个 issue 只描述一个问题** — 多个问题分开提
