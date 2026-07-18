/**
 * 账号弹窗（M5）
 *
 * 主要用途：用电脑端已绑定的邮箱登录，让手机和电脑成为同一个账号，
 * 从而看到电脑上的全部任务。
 */
import { useEffect, useState } from 'react';
import {
  ActivityIndicator, Modal, Pressable, ScrollView, StyleSheet, Text, TextInput, View,
} from 'react-native';

import {
  bindEmail, friendlyAuthError, getAccountInfo, setPassword, signInWithPassword,
  type AccountInfo,
} from '../sync/supabase';

interface Props {
  visible: boolean;
  onClose: () => void;
  /** 登录到了另一个账号：外层需要清空本地数据并全量重新同步 */
  onAccountSwitched: () => void | Promise<void>;
}

export default function AccountScreen({ visible, onClose, onAccountSwitched }: Props) {
  const [info, setInfo] = useState<AccountInfo | null>(null);
  const [email, setEmail] = useState('');
  const [password, setPasswordInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [isError, setIsError] = useState(false);

  useEffect(() => {
    if (visible) {
      setMessage('');
      setIsError(false);
      getAccountInfo().then(setInfo).catch(() => setInfo(null));
    }
  }, [visible]);

  const say = (text: string, error = false) => {
    setMessage(text);
    setIsError(error);
  };

  const run = async (fn: () => Promise<void>) => {
    setBusy(true);
    try {
      await fn();
    } catch (e) {
      say(friendlyAuthError(e), true);
    } finally {
      setBusy(false);
    }
  };

  const handleLogin = () =>
    run(async () => {
      const target = email.trim();
      if (!target || !password) return say('请填写邮箱和密码', true);

      const switched = await signInWithPassword(target, password);
      setPasswordInput('');
      setInfo(await getAccountInfo());

      if (switched) {
        say('登录成功，正在拉取该账号的任务...');
        await onAccountSwitched();
        onClose();
      } else {
        say('登录成功（仍是同一个账号）。');
      }
    });

  const handleBind = () =>
    run(async () => {
      const target = email.trim();
      if (!target.includes('@')) return say('请输入有效的邮箱地址', true);
      await bindEmail(target);
      say(`确认邮件已发到 ${target}，点击邮件里的链接即可完成绑定。`);
    });

  const handleSetPassword = () =>
    run(async () => {
      if (password.length < 6) return say('密码至少 6 位', true);
      await setPassword(password);
      setPasswordInput('');
      say('密码设置成功。现在可以在电脑端用这个邮箱 + 密码登录了。');
    });

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <View style={styles.sheet}>
          <View style={styles.sheetHeader}>
            <Text style={styles.sheetTitle}>账号 / 设备同步</Text>
            <Pressable onPress={onClose} hitSlop={12}>
              <Text style={styles.close}>✕</Text>
            </Pressable>
          </View>

          <ScrollView contentContainerStyle={styles.body}>
            <Text style={styles.status}>
              {info?.email
                ? `当前账号：${info.email}`
                : `当前账号：匿名（${(info?.userId ?? '').slice(0, 8)}…）`}
            </Text>

            {info?.email ? null : (
              <Text style={styles.tip}>
                这台手机现在是独立的匿名账号，看不到电脑上的任务。
                用电脑端绑定的邮箱和密码登录即可合并。
              </Text>
            )}

            <Text style={styles.label}>邮箱</Text>
            <TextInput
              style={styles.input}
              value={email}
              onChangeText={setEmail}
              placeholder="you@example.com"
              placeholderTextColor="#9ca3af"
              autoCapitalize="none"
              keyboardType="email-address"
              autoCorrect={false}
            />

            <Text style={styles.label}>密码</Text>
            <TextInput
              style={styles.input}
              value={password}
              onChangeText={setPasswordInput}
              placeholder="在电脑端设置的密码"
              placeholderTextColor="#9ca3af"
              secureTextEntry
              autoCapitalize="none"
            />

            <Pressable
              style={[styles.btn, styles.btnPrimary, busy && styles.btnDisabled]}
              onPress={handleLogin}
              disabled={busy}
            >
              <Text style={styles.btnPrimaryText}>登录并同步</Text>
            </Pressable>

            <View style={styles.divider} />

            <Text style={styles.tip}>
              反过来，如果你想把「这台手机」的账号设为主账号：先绑定上面的邮箱，
              再给它设一个密码，然后在电脑端用同样的邮箱+密码登录。
            </Text>
            <Pressable
              style={[styles.btn, styles.btnGhost, busy && styles.btnDisabled]}
              onPress={handleBind}
              disabled={busy}
            >
              <Text style={styles.btnGhostText}>把上面的邮箱绑定到本机账号</Text>
            </Pressable>
            <Pressable
              style={[styles.btn, styles.btnGhost, busy && styles.btnDisabled]}
              onPress={handleSetPassword}
              disabled={busy}
            >
              <Text style={styles.btnGhostText}>把上面的密码设为本机账号密码</Text>
            </Pressable>

            {busy ? <ActivityIndicator style={styles.spinner} color="#6366f1" /> : null}
            {message ? (
              <Text style={[styles.message, isError && styles.messageError]}>{message}</Text>
            ) : null}
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.4)', justifyContent: 'flex-end' },
  sheet: {
    backgroundColor: '#ffffff', borderTopLeftRadius: 18, borderTopRightRadius: 18,
    maxHeight: '88%', paddingBottom: 20,
  },
  sheetHeader: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 20, paddingTop: 16, paddingBottom: 10,
  },
  sheetTitle: { fontSize: 17, fontWeight: '700', color: '#111827' },
  close: { fontSize: 18, color: '#6b7280' },

  body: { paddingHorizontal: 20, paddingBottom: 10 },
  status: { fontSize: 14, fontWeight: '600', color: '#111827', marginBottom: 8 },
  tip: { fontSize: 12, color: '#6b7280', lineHeight: 18, marginBottom: 12 },
  label: { fontSize: 12, color: '#4b5563', marginTop: 8, marginBottom: 6 },

  input: {
    backgroundColor: '#f3f4f6', borderRadius: 10, paddingHorizontal: 12,
    paddingVertical: 11, fontSize: 15, color: '#111827',
  },

  btn: { borderRadius: 10, paddingVertical: 12, alignItems: 'center', marginTop: 10 },
  btnPrimary: { backgroundColor: '#6366f1' },
  btnPrimaryText: { color: '#ffffff', fontSize: 14, fontWeight: '600' },
  btnGhost: { backgroundColor: '#eef0f3' },
  btnGhostText: { color: '#4b5563', fontSize: 13, fontWeight: '600' },
  btnDisabled: { opacity: 0.5 },

  divider: { height: 1, backgroundColor: '#e5e7eb', marginVertical: 18 },
  spinner: { marginTop: 12 },
  message: { marginTop: 12, fontSize: 12, color: '#6b7280', lineHeight: 18 },
  messageError: { color: '#dc2626' },
});
