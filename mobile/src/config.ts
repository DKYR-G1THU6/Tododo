/**
 * 应用配置常量 —— 与 PC 端 config.py 保持一致
 */

// Supabase 后端（与 PC 端同一个项目、同一套 RLS）
// publishable key 设计上就是公开的，真正的防线是云端 tasks 表的 RLS 策略
export const SUPABASE_URL = 'https://veipfzkrurcuiohhhylm.supabase.co';
export const SUPABASE_ANON_KEY = 'sb_publishable_-xGNvb8TBjHZcGilPPi3Fw_mIUjPAYo';
export const SUPABASE_VOICE_BUCKET = 'voice';

// 本地数据库
export const DATABASE_NAME = 'tasks.db';

// 同步轮询间隔（毫秒）
export const SYNC_POLL_INTERVAL_MS = 30_000;

// AsyncStorage 里存增量拉取高水位游标的键
export const SYNC_CURSOR_KEY = 'tododo.sync.pullCursor';

// 任务状态
export const TASK_STATUS_TODO = 'todo';
export const TASK_STATUS_IN_PROGRESS = 'in_progress';
export const TASK_STATUS_DONE = 'done';

export const TASK_STATUSES = [
  TASK_STATUS_TODO,
  TASK_STATUS_IN_PROGRESS,
  TASK_STATUS_DONE,
] as const;

export const COLUMN_TITLES: Record<string, string> = {
  [TASK_STATUS_TODO]: 'To Do',
  [TASK_STATUS_IN_PROGRESS]: 'In Progress',
  [TASK_STATUS_DONE]: 'Done',
};

// 任务类型对应的颜色条（与 PC 端一致：每日绿、一次性靛蓝）
export const TYPE_COLORS: Record<string, string> = {
  daily: '#10b981',
  one_time: '#6366f1',
};

/** 状态流转：To Do → In Progress → Done → To Do */
export function getNextStatus(current: string): string {
  switch (current) {
    case TASK_STATUS_TODO:
      return TASK_STATUS_IN_PROGRESS;
    case TASK_STATUS_IN_PROGRESS:
      return TASK_STATUS_DONE;
    default:
      return TASK_STATUS_TODO;
  }
}
