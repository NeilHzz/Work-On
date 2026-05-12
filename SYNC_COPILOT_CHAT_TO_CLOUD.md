# Copilot Chat 云端同步

这个方案的目标不是只备份 transcript，而是尽量把“能影响聊天连续性”的本地状态一起同步到云盘目录。

## 同步内容

脚本会同步这些位置：

1. `%APPDATA%\Code\User\workspaceStorage\<当前工作区>\GitHub.copilot-chat`
2. `%APPDATA%\Code\User\workspaceStorage\<当前工作区>\chatSessions`
3. `%APPDATA%\Code\User\workspaceStorage\<当前工作区>\chatEditingSessions`
4. `%APPDATA%\Code\User\globalStorage\github.copilot-chat`
5. `%APPDATA%\Code\User\settings.json`
6. `%APPDATA%\Code\User\mcp.json`
7. `%APPDATA%\Code\User\chatLanguageModels.json`
8. `%APPDATA%\Code\User\prompts`，如果这个目录存在

## 重要限制

1. 这不是官方保证兼容的同步接口，因为 Copilot Chat 的本地存储格式未来可能变化。
2. 另一台机器第一次使用前，最好先用 VS Code 打开一次同一个工作区，让本地生成对应的 workspaceStorage 条目。
3. 最稳的做法是：同步前先关闭 VS Code，同步完再打开。
4. 如果两台机器同时写入同一个聊天状态，云盘可能发生冲突文件。不要双开同一工作区的聊天会话。
5. 工作区路径可以不同。脚本不会直接复用本机的 workspace 哈希，而是按工作区名建立云端目录，再映射回本机当前的 workspaceStorage 条目。

## 使用方式

假设你的云盘本地目录是：

`D:\Cloud\VSCodeState`

当前机器推送到云端：

```powershell
.
\sync_copilot_chat_to_cloud.ps1 -CloudRoot "D:\Cloud\VSCodeState" -WorkspacePath "D:\system_folder\Desktop\Work On" -Mode push
```

另一台机器拉取到本地：

```powershell
.
\sync_copilot_chat_to_cloud.ps1 -CloudRoot "D:\Cloud\VSCodeState" -WorkspacePath "D:\system_folder\Desktop\Work On" -Mode pull
```

如果两台机器上工作区路径不同，可以额外固定一个名字：

```powershell
.
\sync_copilot_chat_to_cloud.ps1 -CloudRoot "D:\Cloud\VSCodeState" -WorkspacePath "E:\Projects\Work On" -WorkspaceName "Work_On" -Mode pull
```

## 推荐操作顺序

1. 当前工作站关闭 VS Code。
2. 运行 `push`。
3. 等云盘同步完成。
4. 新工作站先打开一次对应工作区，再关闭 VS Code。
5. 运行 `pull`。
6. 重新打开 VS Code，继续工作。

## 建议搭配

1. 打开 VS Code 自带的 Settings Sync，同步扩展、主题、快捷键和用户设置。
2. 继续把真正长期有价值的流程说明、prompt、实验 SOP 放在工作区文件里或仓库里，而不是只留在聊天记录中。
3. 如果你后面想把这个脚本做成“一键 push + pull + 云盘检测”，可以再继续扩展。