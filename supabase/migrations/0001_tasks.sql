-- Tododo 云端 tasks 表 + RLS + Realtime
-- 对齐 docs/schema.md。字段类型刻意与本地 SQLite 保持一致（deleted/has_voice 用 0/1；
-- created_date/completed_date 用 text 的 YYYY-MM-DD，避免时区重解释）。

create table if not exists public.tasks (
    -- 全局同步主键（本地 task_id 是设备内部自增，不上云）
    uuid              uuid primary key,
    -- 归属用户；插入时由 auth.uid() 自动填充，客户端无需传
    user_id           uuid not null default auth.uid() references auth.users(id) on delete cascade,

    title             text not null,
    status            text not null check (status in ('todo','in_progress','done')),
    created_date      text not null,
    completed_date    text,
    task_type         text not null default 'daily' check (task_type in ('daily','one_time')),

    -- 软删除墓碑
    deleted           smallint not null default 0 check (deleted in (0,1)),
    deleted_at        timestamptz,

    -- 语音
    has_voice         smallint not null default 0 check (has_voice in (0,1)),
    audio_url         text,               -- voice 桶内对象路径：{user_id}/{uuid}.{ext}
    transcript        text,
    transcribe_status text check (transcribe_status in ('pending','done','failed')),

    created_at        timestamptz not null default now(),
    -- 客户端权威时钟：LWW 依据。客户端上推时携带 UTC 时间戳；本表原样存储，不用触发器覆盖。
    -- （见 docs/schema.md 的时钟约定；如日后要改为服务端权威时钟，见文件末尾可选触发器。）
    updated_at        timestamptz not null default now()
);

-- 增量拉取用索引：pull "where user_id = me and updated_at > cursor order by updated_at"
create index if not exists tasks_user_updated_idx on public.tasks (user_id, updated_at);

-- ============================
-- 行级安全（RLS）：每个用户只能看/改自己的行
-- ============================
alter table public.tasks enable row level security;

drop policy if exists tasks_select_own on public.tasks;
create policy tasks_select_own on public.tasks
    for select using (auth.uid() = user_id);

drop policy if exists tasks_insert_own on public.tasks;
create policy tasks_insert_own on public.tasks
    for insert with check (auth.uid() = user_id);

drop policy if exists tasks_update_own on public.tasks;
create policy tasks_update_own on public.tasks
    for update using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists tasks_delete_own on public.tasks;
create policy tasks_delete_own on public.tasks
    for delete using (auth.uid() = user_id);

-- ============================
-- Realtime：让两端订阅本表变更
-- ============================
alter table public.tasks replica identity full;

do $$
begin
    if not exists (
        select 1 from pg_publication_tables
        where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = 'tasks'
    ) then
        alter publication supabase_realtime add table public.tasks;
    end if;
end $$;

-- ============================
-- 可选（默认不启用）：服务端权威时钟
-- 若要改为"以服务器 now() 排序"，取消下面注释并同步调整 sync 层（推送后回读 updated_at）。
-- create or replace function public.tasks_set_updated_at()
-- returns trigger language plpgsql as $$
-- begin new.updated_at = now(); return new; end; $$;
-- create trigger tasks_set_updated_at before insert or update on public.tasks
--   for each row execute function public.tasks_set_updated_at();
