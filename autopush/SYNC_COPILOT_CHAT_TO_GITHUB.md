# Copilot Chat GitHub 同步

如果你只想用 GitHub，同步聊天状态最稳的方式是：

1. 新建一个 GitHub 私有仓库。
2. 在每台工作站本地各自 clone 这个私有仓库。
3. 用本目录下的 GitHub 同步脚本，把 Copilot Chat 本地状态导出到这个私有仓库里。
4. 由脚本负责 pull、commit、push。

下面的命令默认从工作区根目录执行，所以脚本路径都写成 `./autopush/...`。

## 为什么不建议直接用当前项目仓库

当前工作区已经连着一个项目远程仓库。直接把聊天状态同步进这个项目仓库，会把个人聊天状态和项目历史混在一起，后面很难维护。

更好的做法是专门建一个仓库，例如：

`copilot-chat-sync-private`

这个仓库只用来存：

1. `vscode-copilot-sync/workspaces/...`
2. `vscode-copilot-sync/user/...`
3. `vscode-copilot-sync/chat-markdown/...`

## 按天整理的 Markdown 聊天归档

现在每次同步还会额外生成一套可读版本：

1. 每个聊天会单独导出成一个 Markdown 文件。
2. 文件会按日期整理到 `vscode-copilot-sync/chat-markdown/<WorkspaceName>/YYYY-MM-DD/`。
3. 每天目录里还会生成一个 `README.md`，列出当天所有聊天，方便另一台工作站直接阅读并继续接着聊。

这样另一台机器不需要去看原始 `jsonl`，只要打开这些 md 就能快速理解之前聊了什么。

## 一次性准备

先在 GitHub 上新建一个私有仓库，然后在本地 clone，例如：

```powershell
git clone https://github.com/<your-account>/copilot-chat-sync-private.git D:\GitHub\copilot-chat-sync-private
```

确保本机已经可以正常对这个仓库执行 `git pull` 和 `git push`。

## 手动同步

推荐使用 `auto` 模式。它会：

1. 先对 GitHub 私有仓库执行 `git pull --rebase --autostash`
2. 调用本地导出脚本同步聊天状态
3. 只对 `vscode-copilot-sync` 目录执行 `git add`
4. 如果有变化，就自动 commit
5. 最后 push 到 GitHub

示例命令：

```powershell
.\autopush\sync_copilot_chat_to_github.ps1 -RepoPath "D:\GitHub\copilot-chat-sync-private" -WorkspacePath "D:\system_folder\Desktop\Work On" -WorkspaceName "Work_On" -Mode auto
```

如果你只想把 GitHub 最新内容拉到本机：

```powershell
.\autopush\sync_copilot_chat_to_github.ps1 -RepoPath "D:\GitHub\copilot-chat-sync-private" -WorkspacePath "D:\system_folder\Desktop\Work On" -WorkspaceName "Work_On" -Mode pull
```

如果你只想把本机当前状态推上去：

```powershell
.\autopush\sync_copilot_chat_to_github.ps1 -RepoPath "D:\GitHub\copilot-chat-sync-private" -WorkspacePath "D:\system_folder\Desktop\Work On" -WorkspaceName "Work_On" -Mode push
```

## 每天零点后自动同步

你前面要求的是按天更新，并在零点后自动执行。GitHub 版已经单独做了计划任务注册脚本。

先预览，不实际注册：

```powershell
.\autopush\register_daily_copilot_chat_github_sync_task.ps1 -RepoPath "D:\GitHub\copilot-chat-sync-private" -WorkspacePath "D:\system_folder\Desktop\Work On" -WorkspaceName "Work_On" -DailyTime "00:05" -PreviewOnly
```

正式注册：

```powershell
.\autopush\register_daily_copilot_chat_github_sync_task.ps1 -RepoPath "D:\GitHub\copilot-chat-sync-private" -WorkspacePath "D:\system_folder\Desktop\Work On" -WorkspaceName "Work_On" -DailyTime "00:05"
```

## 多工作站建议

1. 每台工作站都 clone 同一个 GitHub 私有仓库。
2. 每台工作站都注册一个每日任务。
3. 建议把执行时间错开，例如一台 `00:05`，另一台 `00:12`。
4. 不要在两台机器上同时打开同一工作区并同时触发同步。

## 认证建议

建议优先使用下面两种方式之一：

1. Git Credential Manager
2. SSH key

这样计划任务在后台运行时更稳定，不容易弹出认证窗口。

## 当前工作区的建议

你当前这个仓库已经有 `origin` 指向项目仓库。为了避免把聊天状态提交到项目历史中，我建议不要把 `RepoPath` 设成当前项目根目录，而是单独 clone 一个私有同步仓库再使用上述脚本。
