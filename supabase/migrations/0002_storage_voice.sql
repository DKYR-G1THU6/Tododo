-- voice 存储桶：存放任务录音。对象路径约定为 {user_id}/{uuid}.{ext}
-- 通过对象名的第一段（= user_id）做隔离，配合 RLS 保证只能读写自己的录音。

insert into storage.buckets (id, name, public)
values ('voice', 'voice', false)
on conflict (id) do nothing;

-- storage.objects 上的策略（bucket_id = 'voice' 且路径首段 = 自己的 uid）
drop policy if exists voice_select_own on storage.objects;
create policy voice_select_own on storage.objects
    for select using (
        bucket_id = 'voice'
        and (storage.foldername(name))[1] = auth.uid()::text
    );

drop policy if exists voice_insert_own on storage.objects;
create policy voice_insert_own on storage.objects
    for insert with check (
        bucket_id = 'voice'
        and (storage.foldername(name))[1] = auth.uid()::text
    );

drop policy if exists voice_update_own on storage.objects;
create policy voice_update_own on storage.objects
    for update using (
        bucket_id = 'voice'
        and (storage.foldername(name))[1] = auth.uid()::text
    );

drop policy if exists voice_delete_own on storage.objects;
create policy voice_delete_own on storage.objects
    for delete using (
        bucket_id = 'voice'
        and (storage.foldername(name))[1] = auth.uid()::text
    );
