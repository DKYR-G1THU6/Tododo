/**
 * 同步引擎 —— 与 PC 端 services/sync_service.py 逻辑一一对应
 *
 * 每轮固定「先推后拉」：本地未推送的改动先上云，再把云端更新拉下来做 LWW 合并，
 * 这样 push 失败时也不会被云端旧值覆盖本地编辑。
 */
import AsyncStorage from '@react-native-async-storage/async-storage';

import { SYNC_CURSOR_KEY } from '../config';
import { getDirtyTasks, markSynced, upsertFromRemote } from '../db/database';
import { toRemoteTask, type RemoteTask } from '../types';
import { supabase, ensureSession } from './supabase';
import { localToIso, isoToLocal } from './timestamps';

export type SyncStatus = 'idle' | 'syncing' | 'synced' | 'offline';

export interface SyncResult {
  pushed: number;
  pulled: number;
}

/** 推送本地 dirty 行（含软删除墓碑） */
async function push(): Promise<number> {
  const dirty = await getDirtyTasks();
  if (dirty.length === 0) return 0;

  const rows = dirty.map((t) => toRemoteTask(t, localToIso));
  // user_id 不传，由云端 default auth.uid() 填充
  const { error } = await supabase.from('tasks').upsert(rows, { onConflict: 'uuid' });
  if (error) throw error;

  await markSynced(dirty.map((t) => t.uuid));
  return rows.length;
}

/**
 * 按高水位游标增量拉取。
 * 游标只依据服务端返回值推进 —— 用本地 max(updated_at) 当游标会漏掉
 * 另一台设备时间戳更早的改动。
 */
async function pull(): Promise<number> {
  const cursor = await AsyncStorage.getItem(SYNC_CURSOR_KEY);

  let query = supabase
    .from('tasks')
    .select('*')
    .order('updated_at', { ascending: true })
    .limit(1000);

  if (cursor) query = query.gt('updated_at', cursor);

  const { data, error } = await query;
  if (error) throw error;
  if (!data || data.length === 0) return 0;

  // 服务端已按 updated_at 升序返回，最后一条即最新
  const newest: string | null = data[data.length - 1].updated_at ?? null;

  const normalized: RemoteTask[] = data.map((r: any) => ({
    ...r,
    updated_at: isoToLocal(r.updated_at),
    deleted_at: isoToLocal(r.deleted_at),
  }));

  const written = await upsertFromRemote(normalized);
  if (newest) await AsyncStorage.setItem(SYNC_CURSOR_KEY, newest);
  return written;
}

/** 跑一轮完整同步。失败（多半是离线）时抛出，由调用方降级处理。 */
export async function runSync(): Promise<SyncResult> {
  await ensureSession();
  const pushed = await push();
  const pulled = await pull();
  return { pushed, pulled };
}

/** 清空游标：切换账号 / 重新配对后需要全量重拉 */
export async function resetSyncCursor(): Promise<void> {
  await AsyncStorage.removeItem(SYNC_CURSOR_KEY);
}
