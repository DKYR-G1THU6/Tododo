# Tododo 同步数据契约(schema)

> 单一真相源。PC(Python/SQLite)、手机(Expo/SQLite)、云端(Supabase/Postgres)三处的 `tasks` 表必须遵守本文件。改字段先改这里。

## `tasks` 表字段

| 字段 | 类型 | 说明 | 是否上云 |
|---|---|---|---|
| `task_id` | INTEGER 自增 | 本地设备内部 PK,**不跨设备** | 否(本地) |
| `uuid` | TEXT (UUIDv4) | **全局同步主键**,新建时生成 | 是 |
| `title` | TEXT | 任务标题 | 是 |
| `status` | TEXT | `todo` / `in_progress` / `done` | 是 |
| `created_date` | TEXT | `YYYY-MM-DD`,本地创建日 | 是 |
| `completed_date` | TEXT/NULL | `YYYY-MM-DD`,完成时置位 | 是 |
| `task_type` | TEXT | `daily` / `one_time` | 是 |
| `created_at` | TIMESTAMP | 创建时间(UTC) | 是 |
| `updated_at` | TIMESTAMP | 最后修改时间(UTC),**LWW 判定依据** | 是 |
| `deleted` | INTEGER 0/1 | 软删除墓碑 | 是 |
| `deleted_at` | TIMESTAMP/NULL | 删除时间 | 是 |
| `dirty` | INTEGER 0/1 | 本地待推送标记 | 否(本地) |
| `has_voice` | INTEGER 0/1 | 是否带语音 | 是 |
| `audio_path` | TEXT/NULL | 本地录音文件路径 | 否(本地) |
| `audio_url` | TEXT/NULL | 云端 Storage 录音路径/URL | 是 |
| `transcript` | TEXT/NULL | 语音转出的文字 | 是 |
| `transcribe_status` | TEXT/NULL | `pending` / `done` / `failed` | 是 |
| `user_id` | TEXT | 归属用户(云端 RLS 隔离);本地存当前登录用户 | 云端必须 |

`user_id` 仅在接入 Supabase(M2/M3)时加入;M1 的本地表尚未包含。

## 同步规则

- **主键**:一律用 `uuid` 匹配跨设备的同一条任务;`task_id` 只在本机有意义。
- **冲突**:同一 `uuid` 两端都改 → `updated_at` 更晚者整行胜出(last-write-wins)。
- **时间戳格式**:统一 UTC。SQLite 用 `CURRENT_TIMESTAMP`(`YYYY-MM-DD HH:MM:SS`)。跨端(Postgres 的 ISO8601)在 sync 层需归一化后再按字符串比较。
- **删除**:不物理删除,置 `deleted=1` + `deleted_at`;墓碑照常同步。云端可用 `pg_cron` 定期清理超期墓碑。
- **推送**:本地任何写操作置 `dirty=1`;推送成功后置 `dirty=0`。老数据经 v3 迁移回填 uuid 时统一置 `dirty=1`,首次登录整批上云。
- **载荷**:上云只发"是否上云=是"的字段(见 `Task.to_remote_dict()`),本地专用字段(`task_id`/`dirty`/`audio_path`)不上传。

## 每日任务重置

`daily` 任务按本地日历日重置:跨天后,前一天处于 `in_progress`/`done` 的 daily 任务被改回 `todo`(`completed_date` 清空)。多设备下走 LWW 收敛;假设同一用户设备同时区。详见计划文件的"每日重置与时区"一节。

## Schema 版本

本地 SQLite 版本号由 `config.DB_SCHEMA_VERSION` 驱动,`storage/migrator.py` 增量迁移。当前 **v3**(v3 引入上述全部同步字段)。
