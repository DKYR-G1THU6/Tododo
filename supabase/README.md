# Supabase 后端（M2）

Tododo 双端同步的云端部分:`tasks` 表 + RLS + Realtime + `voice` 存储桶 + `transcribe` Edge Function(Groq 语音转文字)。

## 目录

```
supabase/
├── migrations/
│   ├── 0001_tasks.sql          # tasks 表、索引、RLS、Realtime
│   └── 0002_storage_voice.sql  # voice 桶 + 对象级 RLS
└── functions/
    └── transcribe/index.ts     # 录音转文字（调 Groq whisper-large-v3）
```

## 你需要先做的(控制台操作,我无法代劳)

1. 在 [supabase.com](https://supabase.com) 建一个项目。
2. 记下 **Project URL** 和 **anon public key**(Project Settings → API)——之后 M3 填进 PC 端 `config.py`。
3. **Authentication → Providers**:打开 **Anonymous sign-ins**;并按需打开 **Email**(magic link)供"绑定邮箱找回"。
4. 给 Edge Function 配 Groq 密钥(见下)。

## 应用方式二选一

### A. 用 Supabase CLI(推荐)

```bash
# 安装并登录
npm i -g supabase
supabase login

# 关联到你的项目(project-ref 在项目 URL 里)
supabase link --project-ref <your-project-ref>

# 应用数据库迁移
supabase db push

# 配置 Groq 密钥并部署 Edge Function
supabase secrets set GROQ_API_KEY=<你的_groq_key>
supabase functions deploy transcribe
```

### B. 纯控制台(不装 CLI)

- 打开 **SQL Editor**,把 `migrations/0001_tasks.sql`、`migrations/0002_storage_voice.sql` 内容依次粘贴执行。
- **Edge Functions** → 新建 `transcribe`,粘贴 `functions/transcribe/index.ts`;在其 **Secrets** 里加 `GROQ_API_KEY`。

> `SUPABASE_URL` / `SUPABASE_ANON_KEY` 在 Edge Function 运行时自动可用,无需手动配置;只需额外配 `GROQ_API_KEY`。

## 设计要点

- **身份**:`tasks.user_id` 插入时由 `auth.uid()` 自动填充;RLS 保证每人只能读写自己的数据,朋友之间天然隔离。
- **录音路径约定**:`voice` 桶内对象名为 `{user_id}/{uuid}.{ext}`;`transcribe` 靠路径首段(= user_id)配合 RLS 校验归属。任务行的 `audio_url` 存这个对象路径。
- **时钟**:采用**客户端权威时钟**,`updated_at` 由客户端上推时携带(统一 RFC3339 UTC,如 `2026-07-18T12:34:56Z`),云端原样存储、按时间戳做 LWW。若日后要改服务端权威时钟,见 `0001_tasks.sql` 末尾的可选触发器。
- **转写回传**:`transcribe` 写回 `transcript` 时会更新 `updated_at`,因此结果通过正常 pull/Realtime 自动同步到两端。
- **墓碑清理(可选)**:如需物理清理超期的 `deleted=1` 行,可在数据库加 `pg_cron` 定时任务(本期未包含)。

## 验证(M3 接入客户端后)

- 用 anon key + 匿名登录插入一条任务 → 另一设备/会话能 `select` 到。
- 上传一段录音到 `voice/{user_id}/{uuid}.m4a` → 调用 `transcribe` → 任务行 `transcript` 被填、`transcribe_status='done'`。
- 用另一个用户的 JWT 访问 → 读不到别人的行/录音(RLS 生效)。
