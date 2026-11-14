# 邮箱账号管理工具 / Email Address Manager

[中文](#chinese) | [English](#english)

<a id="chinese"></a>

## 中文

`email_manager.py` 是一个 PyQt5 桌面工具，用于维护本地邮箱账号列表。它支持手动添加邮箱、基于基础邮箱随机生成新邮箱、维护邮箱状态，并把数据保存到同目录下的 `emails.json`。

### 功能

- 手动添加邮箱地址。
- 在邮箱 `@` 前追加随机小写字母和数字后缀，生成不重复的新邮箱。
- 为邮箱设置 `可用` 或 `封禁` 状态。
- 支持单条删除、单条状态切换。
- 支持当前页批量选择、批量封禁、批量恢复、批量删除。
- 表格分页展示，每页固定 `10` 条记录。
- 点击邮箱地址或基础邮箱可复制到剪贴板。

### 文件说明

| 文件 | 说明 |
| --- | --- |
| `email_manager.py` | 主程序，包含界面、数据读写和邮箱生成逻辑 |
| `emails.json` | 邮箱数据文件，程序自动读写 |

`emails.json` 中每条记录大致包含：

```json
{
  "email": "user12@example.invalid",
  "status": "可用",
  "base": "user@example.invalid"
}
```

### 依赖

```powershell
python -m pip install -r requirements.txt
```

### 运行

在仓库根目录执行：

```powershell
python email_manager.py
```

### 使用提示

- 基础邮箱必须包含 `@`，并且本地名和域名不能为空。
- 随机后缀长度可在界面中设置，长度越短越容易发生重复。
- 数据保存在本地 JSON 文件中，重要数据建议定期备份 `emails.json`。
- 真实账号数据不随仓库分发；`emails.json` 已被忽略，首次运行从空列表开始。

<a id="english"></a>

## English

`email_manager.py` is a PyQt5 desktop application for managing a local list of email addresses. It supports manually adding addresses, generating address variants from a base address, tracking availability, and saving records to `emails.json` beside the script. The application interface is in Chinese.

### Features

- Add email addresses manually.
- Append random lowercase letters and digits to the local part before `@` to generate unique address variants in the list.
- Mark records as available (`可用`) or blocked (`封禁`).
- Delete an individual record or change its status.
- Select, block, restore, or delete records in batches on the current page.
- Browse records in pages of 10 rows.
- Click an email address or its base address to copy it to the clipboard.

### Files

| File | Purpose |
| --- | --- |
| `email_manager.py` | User interface, local data storage, and address generation |
| `emails.json` | Local records read and written by the application |

A record in `emails.json` has a structure similar to:

```json
{
  "email": "user12@example.invalid",
  "status": "可用",
  "base": "user@example.invalid"
}
```

### Install and run

From the repository root:

```powershell
python -m pip install -r requirements.txt
python email_manager.py
```

### Usage and local data

- A base address must contain `@`, with a nonempty local part and domain.
- The random suffix length is configurable. Shorter suffixes are more likely to produce duplicates.
- Records are stored in a local JSON file. Back up `emails.json` when needed.
- Real address records are not distributed with the repository. The file is ignored by Git; a fresh clone starts with an empty list.
