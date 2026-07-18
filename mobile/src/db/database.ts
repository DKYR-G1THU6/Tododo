/**
 * 本地 SQLite 数据层 —— 镜像 PC 端 storage/database.py 的语义
 *
 * 关键约定（与 PC 端必须一致，见 docs/schema.md）：
 *  - uuid 是跨设备主键；task_id 只在本机有意义
 *  - 删除是软删除（墓碑），不物理删
 *  - 任何本地写入都置 dirty=1，推送成功后清 0
 *  - 时间戳取到毫秒，否则同一秒内的改动无法用 LWW 定序
 */
import * as SQLite from 'expo-sqlite';
import * as Crypto from 'expo-crypto';

import { DATABASE_NAME, TASK_STATUS_TODO, TASK_STATUS_IN_PROGRESS, TASK_STATUS_DONE } from '../config';
import type { Task, RemoteTask, TaskStatus, TaskType } from '../types';

// 毫秒精度 UTC 时间戳（SQLite 的 CURRENT_TIMESTAMP 只有秒精度，不够定序）
const NOW_MS = "strftime('%Y-%m-%d %H:%M:%f','now')";

const TASK_COLUMNS = `
  task_id, uuid, title, status, created_date, completed_date, task_type,
  updated_at, deleted, deleted_at, dirty, has_voice, audio_path, audio_url,
  transcript, transcribe_status
`;

let db: SQLite.SQLiteDatabase | null = null;

async function getDb(): Promise<SQLite.SQLiteDatabase> {
  if (db === null) {
    db = await SQLite.openDatabaseAsync(DATABASE_NAME);
  }
  return db;
}

/** 本地日历日（与 PC 端 datetime.now() 一致，用本地时区而非 UTC） */
function localDateString(d: Date = new Date()): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export async function initDatabase(): Promise<void> {
  const database = await getDb();
  await database.execAsync(`
    PRAGMA journal_mode = WAL;
    CREATE TABLE IF NOT EXISTS tasks (
      task_id INTEGER PRIMARY KEY AUTOINCREMENT,
      uuid TEXT,
      title TEXT NOT NULL,
      status TEXT NOT NULL,
      created_date TEXT NOT NULL,
      completed_date TEXT,
      task_type TEXT DEFAULT 'daily',
      deleted INTEGER DEFAULT 0,
      deleted_at TIMESTAMP,
      dirty INTEGER DEFAULT 0,
      has_voice INTEGER DEFAULT 0,
      audio_path TEXT,
      audio_url TEXT,
      transcript TEXT,
      transcribe_status TEXT,
      created_at TIMESTAMP DEFAULT (strftime('%Y-%m-%d %H:%M:%f','now')),
      updated_at TIMESTAMP DEFAULT (strftime('%Y-%m-%d %H:%M:%f','now'))
    );
    CREATE UNIQUE INDEX IF NOT EXISTS tasks_uuid_idx ON tasks(uuid);
  `);
}

// ============================
// 写操作（一律置 dirty=1）
// ============================

export async function addTask(title: string, taskType: TaskType = 'daily'): Promise<string> {
  const database = await getDb();
  const uuid = Crypto.randomUUID();
  await database.runAsync(
    `INSERT INTO tasks (uuid, title, status, created_date, task_type, dirty, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, 1, ${NOW_MS}, ${NOW_MS})`,
    [uuid, title, TASK_STATUS_TODO, localDateString(), taskType]
  );
  return uuid;
}

/** 软删除：打墓碑标记，让删除能同步到其它设备 */
export async function deleteTask(taskId: number): Promise<void> {
  const database = await getDb();
  await database.runAsync(
    `UPDATE tasks
     SET deleted = 1, deleted_at = ${NOW_MS}, updated_at = ${NOW_MS}, dirty = 1
     WHERE task_id = ? AND deleted = 0`,
    [taskId]
  );
}

export async function updateTaskStatus(taskId: number, newStatus: TaskStatus): Promise<void> {
  const database = await getDb();
  const completedDate = newStatus === TASK_STATUS_DONE ? localDateString() : null;
  await database.runAsync(
    `UPDATE tasks
     SET status = ?, completed_date = ?, updated_at = ${NOW_MS}, dirty = 1
     WHERE task_id = ?`,
    [newStatus, completedDate, taskId]
  );
}

export async function updateTaskTitle(taskId: number, newTitle: string): Promise<void> {
  const database = await getDb();
  await database.runAsync(
    `UPDATE tasks SET title = ?, updated_at = ${NOW_MS}, dirty = 1 WHERE task_id = ?`,
    [newTitle, taskId]
  );
}

export async function updateTaskType(taskId: number, newType: TaskType): Promise<void> {
  const database = await getDb();
  await database.runAsync(
    `UPDATE tasks SET task_type = ?, updated_at = ${NOW_MS}, dirty = 1 WHERE task_id = ?`,
    [newType, taskId]
  );
}

/** 每日重置：把前一天的 daily 任务翻回 To Do（与 PC 端逻辑一致） */
export async function resetDailyTasks(): Promise<number> {
  const database = await getDb();
  const today = localDateString();
  const result = await database.runAsync(
    `UPDATE tasks
     SET status = ?, completed_date = NULL, updated_at = ${NOW_MS}, dirty = 1
     WHERE deleted = 0 AND task_type = 'daily' AND created_date < ?
       AND (status = ? OR status = ?)`,
    [TASK_STATUS_TODO, today, TASK_STATUS_IN_PROGRESS, TASK_STATUS_DONE]
  );
  return result.changes;
}

// ============================
// 读操作（一律过滤 deleted=0）
// ============================

/** 主界面可见任务：所有每日任务 + 未完成的一次性任务 + 今天完成的一次性任务 */
export async function getAllTasks(): Promise<Task[]> {
  const database = await getDb();
  return database.getAllAsync<Task>(
    `SELECT ${TASK_COLUMNS} FROM tasks
     WHERE deleted = 0
       AND (
         task_type = 'daily'
         OR (task_type = 'one_time'
             AND (status != ? OR (status = ? AND completed_date = ?)))
       )
     ORDER BY created_at ASC`,
    [TASK_STATUS_DONE, TASK_STATUS_DONE, localDateString()]
  );
}

export async function getCompletedOneTimeTasks(): Promise<Task[]> {
  const database = await getDb();
  return database.getAllAsync<Task>(
    `SELECT ${TASK_COLUMNS} FROM tasks
     WHERE deleted = 0 AND task_type = 'one_time' AND status = ?
     ORDER BY completed_date DESC, created_at DESC`,
    [TASK_STATUS_DONE]
  );
}

export async function getTaskByUuid(uuid: string): Promise<Task | null> {
  const database = await getDb();
  return database.getFirstAsync<Task>(
    `SELECT ${TASK_COLUMNS} FROM tasks WHERE uuid = ?`,
    [uuid]
  );
}

// ============================
// 同步支持
// ============================

/** 待推送的行，含已软删除的墓碑 */
export async function getDirtyTasks(): Promise<Task[]> {
  const database = await getDb();
  return database.getAllAsync<Task>(`SELECT ${TASK_COLUMNS} FROM tasks WHERE dirty = 1`);
}

export async function markSynced(uuids: string[]): Promise<void> {
  if (uuids.length === 0) return;
  const database = await getDb();
  const placeholders = uuids.map(() => '?').join(',');
  await database.runAsync(`UPDATE tasks SET dirty = 0 WHERE uuid IN (${placeholders})`, uuids);
}

/**
 * 物理清空本地所有任务。
 *
 * 仅用于「登录到另一个账号」：此时本地数据属于旧账号，必须清干净，
 * 否则会被当成待推送内容混进新账号。清空后由同步层全量重新拉取。
 */
export async function clearAllTasks(): Promise<void> {
  const database = await getDb();
  await database.runAsync('DELETE FROM tasks');
}

/**
 * 把云端行合并进本地（LWW：仅当 remote.updated_at 更晚才覆盖）。
 * 传入的 updated_at / deleted_at 必须已归一化为本地毫秒格式。
 * 返回实际写入的行数。
 */
export async function upsertFromRemote(rows: RemoteTask[]): Promise<number> {
  const database = await getDb();
  let written = 0;

  for (const r of rows) {
    if (!r.uuid) continue;

    const existing = await database.getFirstAsync<{ updated_at: string | null; dirty: number }>(
      `SELECT updated_at, dirty FROM tasks WHERE uuid = ?`,
      [r.uuid]
    );

    if (existing === null) {
      await database.runAsync(
        `INSERT INTO tasks (
           uuid, title, status, created_date, completed_date, task_type,
           updated_at, deleted, deleted_at, dirty, has_voice, audio_url,
           transcript, transcribe_status
         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)`,
        [
          r.uuid, r.title, r.status, r.created_date, r.completed_date,
          r.task_type ?? 'daily', r.updated_at, r.deleted ?? 0, r.deleted_at,
          r.has_voice ?? 0, r.audio_url, r.transcript, r.transcribe_status,
        ]
      );
      written += 1;
      continue;
    }

    // 本地还有未推送的改动：保留本地，等下一轮 push 上去后再合并，
    // 避免 push 失败时本地编辑被云端旧值覆盖丢失。
    if (existing.dirty) continue;

    const localUpdated = existing.updated_at;
    if (r.updated_at && (localUpdated === null || r.updated_at > localUpdated)) {
      await database.runAsync(
        `UPDATE tasks SET
           title = ?, status = ?, created_date = ?, completed_date = ?,
           task_type = ?, updated_at = ?, deleted = ?, deleted_at = ?,
           has_voice = ?, audio_url = ?, transcript = ?, transcribe_status = ?,
           dirty = 0
         WHERE uuid = ?`,
        [
          r.title, r.status, r.created_date, r.completed_date,
          r.task_type ?? 'daily', r.updated_at, r.deleted ?? 0, r.deleted_at,
          r.has_voice ?? 0, r.audio_url, r.transcript, r.transcribe_status,
          r.uuid,
        ]
      );
      written += 1;
    }
  }

  return written;
}
