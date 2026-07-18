/**
 * 时间戳归一化 —— 与 PC 端 services/sync_service.py 的 local_to_iso / iso_to_local 对应
 *
 * 本地 SQLite: 'YYYY-MM-DD HH:MM:SS.mmm'（UTC）
 * 云端 Postgres: RFC3339，如 '2026-07-18T12:34:56.789+00:00'
 * 两边都保持 UTC 且统一到毫秒，转换后仍可直接按字典序比较。
 */

/** 本地时间戳 -> RFC3339 UTC（上推 / 做游标时用） */
export function localToIso(ts: string | null): string | null {
  if (!ts) return null;
  const s = ts.trim();
  if (s.includes('T')) return s; // 已经是 ISO
  return s.replace(' ', 'T') + 'Z';
}

/** RFC3339 -> 本地毫秒格式（拉取后写库前用） */
export function isoToLocal(ts: string | null): string | null {
  if (!ts) return null;
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return ts;
  // toISOString() 固定输出 3 位小数，切到 23 字符正好是 'YYYY-MM-DD HH:MM:SS.mmm'
  return d.toISOString().replace('T', ' ').slice(0, 23);
}
