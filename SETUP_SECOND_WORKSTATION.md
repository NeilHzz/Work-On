# 第二台工作站配置指南（给 Copilot/Sonnet 的操作指令）

本文件用于指导在第二台工作站上复现当前工作环境的全部配置，包括：
1. 克隆 GitHub 仓库
2. 安装 Python 虚拟环境
3. 安装 uv/uvx 工具
4. 配置 Zotero MCP 服务器
5. 安装 GitDoc 插件实现自动同步

---

## 步骤 1：克隆 GitHub 仓库

打开终端，将仓库克隆到本机（路径可自定义）：

```powershell
git clone <你的GitHub仓库地址> "D:\system_folder\Desktop\Work On"
cd "D:\system_folder\Desktop\Work On"
```

然后用 VS Code 打开该文件夹：

```powershell
code "D:\system_folder\Desktop\Work On"
```

---

## 步骤 2：创建 Python 虚拟环境

在工作区根目录下执行：

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> 如果没有 requirements.txt，跳过最后一行，后续按需安装包。

---

## 步骤 3：安装 uv/uvx（用于 Zotero MCP）

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

安装完成后验证：

```powershell
$env:Path = "C:\Users\$env:USERNAME\.local\bin;$env:Path"
uvx --version
```

---

## 步骤 4：配置 Zotero MCP 服务器

`.vscode/mcp.json` 已经存在于仓库中，但其中 `command` 路径是硬编码的，**需要更新为当前机器的实际路径**。

请 Copilot 执行以下操作：**将 `.vscode/mcp.json` 中的 `command` 字段替换为当前用户的 uvx 路径**：

```json
{
  "servers": {
    "zotero": {
      "type": "stdio",
      "command": "C:\\Users\\<当前用户名>\\.local\\bin\\uvx.exe",
      "args": ["--upgrade", "zotero-mcp"],
      "env": {
        "ZOTERO_LOCAL": "true",
        "ZOTERO_API_KEY": "",
        "ZOTERO_LIBRARY_ID": ""
      }
    }
  }
}
```

用以下命令获取当前用户名：

```powershell
$env:USERNAME
```

然后将 mcp.json 中的路径替换成 `C:\Users\<实际用户名>\.local\bin\uvx.exe`。

### Zotero 本地 API 启用（手动操作）

在 Zotero 桌面应用中：
> 编辑 → 设置 → 高级 → 勾选"允许此计算机上的其他应用程序与 Zotero 通信"

---

## 步骤 5：安装 GitDoc 插件（自动 Git 同步）

`.vscode/settings.json` 已在仓库中，配置已就绪。只需安装插件：

在 VS Code 中按 `Ctrl+Shift+X`，搜索 `GitDoc`，安装 `vsls-contrib.gitdoc`。

或让 Copilot 执行安装命令。

安装后 GitDoc 会自动：
- 保存文件时 auto-commit
- 30 秒后 auto-push 到 GitHub
- 30 秒后 auto-pull 拉取另一台机器的更改

---

## 验证清单

- [ ] `uvx --version` 输出版本号
- [ ] `.vscode/mcp.json` 中 command 路径已更新为本机用户名
- [ ] Zotero 已开启本地 API
- [ ] GitDoc 插件已安装，VS Code 右下角显示 GitDoc 状态
- [ ] 在 Copilot Chat 中可以看到 Zotero 相关工具

---

## 注意事项

- **不要同时在两台机器上修改同一文件**，否则会产生 Git 冲突
- `mcp.json` 中的路径每台机器可能不同，修改后**不要提交到 Git**（可在 .gitignore 中添加 `.vscode/mcp.json`）
- 如果 Zotero MCP 无法连接，确认 Zotero 桌面应用正在运行
