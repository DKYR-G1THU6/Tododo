/**
 * Task 类型 —— 与 PC 端 models/task.py 及 docs/schema.md 一一对应
 */

export type TaskStatus = 'todo' | 'in_progress' | 'done';
export type TaskType = 'daily' | 'one_time';
export type TranscribeStatus = 'pending' | 'done' | 'failed';

/** 本地一行任务（含仅存在于本机的字段） */
export interface Task {
  task_id: number;              // 本地自增 ID，不跨设备
  uuid: string;                 // 全局同步主键
  title: string;
  status: TaskStatus;
  created_date: string;         // YYYY-MM-DD
  completed_date: string | null;
  task_type: TaskType;
  updated_at: string;           // 'YYYY-MM-DD HH:MM:SS.mmm'（UTC），LWW 依据
  deleted: number;              // 0/1 软删除墓碑
  deleted_at: string | null;
  dirty: number;                // 0/1 本地待推送
  has_voice: number;            // 0/1
  audio_path: string | null;    // 本地录音路径（不上云）
  audio_url: string | null;     // 云端 Storage 对象路径
  transcript: string | null;
  transcribe_status: TranscribeStatus | null;
}

/** 上云载荷：剔除本地专用字段（task_id / dirty / audio_path） */
export interface RemoteTask {
  uuid: string;
  title: string;
  status: TaskStatus;
  created_date: string;
  completed_date: string | null;
  task_type: TaskType;
  updated_at: string | null;    // 线上统一 RFC3339 UTC
  deleted: number;
  deleted_at: string | null;
  has_voice: number;
  audio_url: string | null;
  transcript: string | null;
  transcribe_status: TranscribeStatus | null;
}

export function toRemoteTask(t: Task, toIso: (s: string | null) => string | null): RemoteTask {
  return {
    uuid: t.uuid,
    title: t.title,
    status: t.status,
    created_date: t.created_date,
    completed_date: t.completed_date,
    task_type: t.task_type,
    updated_at: toIso(t.updated_at),
    deleted: t.deleted,
    deleted_at: toIso(t.deleted_at),
    has_voice: t.has_voice,
    audio_url: t.audio_url,
    transcript: t.transcript,
    transcribe_status: t.transcribe_status,
  };
}
