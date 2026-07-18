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
