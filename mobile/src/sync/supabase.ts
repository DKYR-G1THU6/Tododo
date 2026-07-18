/**
 * Supabase 客户端 + 匿名登录
 *
 * 与 PC 端连同一个项目、同一套 RLS。会话由 supabase-js 持久化到 AsyncStorage，
 * 换句话说：装上 app 第一次打开就自动有身份，不需要注册登录。
 * （扫码配对第二台设备 / 绑定邮箱找回在 M5 做。）
 */
import 'react-native-url-polyfill/auto';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { createClient, type Session } from '@supabase/supabase-js';

import { SUPABASE_URL, SUPABASE_ANON_KEY } from '../config';

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    storage: AsyncStorage,
    autoRefreshToken: true,
    persistSession: true,
    // RN 里没有浏览器地址栏，必须关掉，否则 supabase-js 会报警
    detectSessionInUrl: false,
  },
});

/** 确保有可用会话；首次运行自动匿名登录 */
export async function ensureSession(): Promise<Session> {
  const { data } = await supabase.auth.getSession();
  if (data.session) return data.session;

  const { data: signed, error } = await supabase.auth.signInAnonymously();
  if (error) throw error;
  if (!signed.session) throw new Error('anonymous sign-in returned no session');
  return signed.session;
}

export async function getUserId(): Promise<string | null> {
  const { data } = await supabase.auth.getSession();
  return data.session?.user.id ?? null;
}

// ============================
// 账号（M5：与 PC 认作同一个人）
// ============================

export interface AccountInfo {
  userId: string | null;
  email: string | null;
  isAnonymous: boolean;
}

export async function getAccountInfo(): Promise<AccountInfo> {
  const { data } = await supabase.auth.getUser();
  const user = data.user;
  return {
    userId: user?.id ?? null,
    email: user?.email ?? null,
    isAnonymous: user?.is_anonymous ?? !user?.email,
  };
}

/** 给本机匿名账号绑定邮箱（升级为正式账号，user_id 不变） */
export async function bindEmail(email: string): Promise<void> {
  const { error } = await supabase.auth.updateUser({ email });
  if (error) throw error;
}

/** 发送登录验证码。shouldCreateUser=false：只允许登录已存在的账号，避免手滑建出新账号 */
export async function sendLoginCode(email: string): Promise<void> {
  const { error } = await supabase.auth.signInWithOtp({
    email,
    options: { shouldCreateUser: false },
  });
  if (error) throw error;
}

/**
 * 校验验证码完成登录。
 * 返回 true 表示切换到了**另一个** user —— 调用方必须清空本地库和同步游标。
 */
export async function verifyLoginCode(email: string, code: string): Promise<boolean> {
  const previous = (await supabase.auth.getSession()).data.session?.user.id ?? null;
  const { data, error } = await supabase.auth.verifyOtp({
    email,
    token: code,
    type: 'email',
  });
  if (error) throw error;
  return (data.user?.id ?? null) !== previous;
}

/** 把 Supabase 的原始报错翻成人话 */
export function friendlyAuthError(err: unknown): string {
  const msg = (err instanceof Error ? err.message : String(err)).toLowerCase();
  if (msg.includes('network') || msg.includes('fetch')) return '连不上服务器，请检查网络后重试。';
  if (msg.includes('expired')) return '验证码已过期，请重新发送。';
  if (msg.includes('invalid') && msg.includes('token')) return '验证码不正确，请检查后重试。';
  if (msg.includes('should_create_user') || msg.includes('signups not allowed') || msg.includes('user not found'))
    return '这个邮箱还没有账号。请先在电脑端「绑定邮箱」。';
  if (msg.includes('rate') || msg.includes('429')) return '发送太频繁，请过几分钟再试。';
  if (msg.includes('email_exists') || msg.includes('already been registered'))
    return '该邮箱已被注册，请改用「用邮箱登录」。';
  return `操作失败：${err instanceof Error ? err.message : String(err)}`;
}
