# Tododo 开发速查

> 下次回来忘了怎么启动时看这里。

## 一句话架构

```
PC 端 (Python/PyQt5)  ┐
                      ├── Supabase (Postgres + Auth + Storage + Edge Function)
手机端 (Expo/RN)       ┘
```

两端各有一份本地 SQLite，**离线可用**；联网后自动双向同步（先推后拉，冲突按 `updated_at` 取新）。
**没有需要你自己开的后端服务器** —— Supabase 是托管的，永远在线。

---

## 启动 PC 端

```bash
cd D:\Xina_App\Tododo
python main.py            # 带控制台，能看日志
# 或
pythonw main.py           # 无控制台窗口（平时用这个）
```

日志：`%APPDATA%\Tododo\tododo.log`
数据库：`%APPDATA%\Tododo\tasks.db`
登录会话：`%APPDATA%\Tododo\session.json`
同步游标：`%APPDATA%\Tododo\sync_state.json`

---

## 启动手机端（开发模式）

**前提：手机上已装 development build 的 APK，且手机和电脑在同一个 WiFi。**

```bash
cd D:\Xina_App\Tododo\mobile
npx expo start            # 卡住/行为诡异时加 --clear 清缓存
```

然后打开手机上的 Tododo，扫终端里的二维码（或它会自动列出开发服务器）。

> ⚠️ **注意别在 `expo start` 运行时执行 `npm install` / `expo install`** ——
> npm 改动 node_modules 会把 Metro 的文件监视器搞崩。先 Ctrl+C 停掉再装。

---

## 什么时候必须重新构建 APK

| 改动类型 | 需要重新构建吗 |
|---|---|
| 改 JS/TS 代码、样式、界面 | ❌ 不用，热更新即可 |
| **新增原生模块**（`expo install` 某个带原生代码的包） | ✅ **必须** |
| 改 `app.json` 的插件/权限配置 | ✅ 必须 |
| 升级 Expo SDK | ✅ 必须 |

重新构建：

```bash
cd D:\Xina_App\Tododo\mobile
npx eas-cli build --profile development -p android
```

⚠️ 注意 CLI 包名是 **`eas-cli`**，`npx eas` 会报 "could not determine executable"。

构建完成后终端给两个二维码，**它们作用不同**：
1. **Build finished 后的那个** → 下载安装 APK（新构建必须先装这个）
2. **`expo start` 后的那个** → 让已安装的 app 连开发服务器

---

## Supabase 后端

项目：`https://veipfzkrurcuiohhhylm.supabase.co`

| 东西 | 位置 |
|---|---|
| 建表/RLS/Realtime SQL | `supabase/migrations/0001_tasks.sql` |
| voice 存储桶 + 策略 | `supabase/migrations/0002_storage_voice.sql` |
| 转写函数 | `supabase/functions/transcribe/index.ts` |

**改了 SQL** → 控制台 SQL Editor 粘贴执行
**改了 Edge Function** → 控制台 Edge Functions → transcribe → 粘贴 → Deploy

### 已配置的 Secrets（Edge Functions → Secrets）

- `GROQ_API_KEY` —— 转写用的 Groq 密钥（必需）
- `GROQ_MODEL` —— 可选，不设时默认 `whisper-large-v3`；想试快一点的填 `whisper-large-v3-turbo`

### 已知的后台限制

- **内置邮件 2 封/小时**。所以设备间登录用的是**邮箱+密码**（不发邮件），而不是验证码。
- 编辑邮件模板需要先配自定义 SMTP —— 目前没配，也用不上。

---

## 账号 / 多设备

- 首次打开自动**匿名登录**，零门槛
- 想让第二台设备看到同样的数据：
  1. PC：☰ → 账号/设备同步 → ① 绑定邮箱 → ② 设置密码
  2. 手机：设置 → 账号 → 用同一邮箱+密码登录

当前主账号：`darrenkyr@gmail.com`

---

## 常见问题

| 现象 | 原因 / 处理 |
|---|---|
| 手机白屏或红屏 `Cannot find native module` | 装的还是旧 APK，需要重新构建并**安装新 APK** |
| 手机改了但电脑没变 | 正常有几秒延迟；切到电脑窗口会立刻触发同步 |
| Metro 报 `ENOENT: watch ...` | 在 expo start 运行时装过包，Ctrl+C 后重新 `npx expo start --clear` |
| 同步状态点一直是灰的 | 离线。改动都存在本地，联网后会自动补推 |

---

## 数据安全

- **删除是软删除**：内容不会真的消失，只是标记 `deleted=1`。所以**别把密钥之类的东西写进任务标题**。
- PC 数据库备份：直接复制 `%APPDATA%\Tododo\tasks.db`
