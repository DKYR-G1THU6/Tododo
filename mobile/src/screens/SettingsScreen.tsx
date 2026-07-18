/**
 * 设置弹窗
 *
 * 对齐 PC 端菜单里的几项：账号、手动同步、历史记录（已完成的一次性任务）、退出登录。
 */
import { useEffect, useState } from 'react';
import {
  ActivityIndicator, Alert, Modal, Pressable, ScrollView, StyleSheet, Text, View,
} from 'react-native';

import { getCompletedOneTimeTasks } from '../db/database';
import { friendlyAuthError, getAccountInfo, signOut, type AccountInfo } from '../sync/supabase';
import type { Task } from '../types';

interface Props {
  visible: boolean;
  onClose: () => void;
  onOpenAccount: () => void;
  onSyncNow: () => void;
  /** 退出登录后：清空本地数据、重置游标、重新以匿名身份开始 */
  onSignedOut: () => void | Promise<void>;
}

export default function SettingsScreen({
  visible, onClose, onOpenAccount, onSyncNow, onSignedOut,
}: Props) {
  const [info, setInfo] = useState<AccountInfo | null>(null);
  const [history, setHistory] = useState<Task[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!visible) return;
    setShowHistory(false);
    getAccountInfo().then(setInfo).catch(() => setInfo(null));
    getCompletedOneTimeTasks().then(setHistory).catch(() => setHistory([]));
  }, [visible]);

  const handleSignOut = () => {
    Alert.alert(
      '退出登录',
      '本机的任务会被清空（云端数据不受影响，重新登录即可取回）。确定要退出吗？',
      [
        { text: '取消', style: 'cancel' },
        {
          text: '退出',
          style: 'destructive',
          onPress: async () => {
            setBusy(true);
            try {
              await signOut();
              await onSignedOut();
              onClose();
            } catch (e) {
              Alert.alert('退出失败', friendlyAuthError(e));
            } finally {
              setBusy(false);
            }
          },
        },
      ]
    );
  };

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <View style={styles.sheet}>
          <View style={styles.sheetHeader}>
            <Text style={styles.sheetTitle}>设置</Text>
            <Pressable onPress={onClose} hitSlop={12}>
              <Text style={styles.close}>✕</Text>
            </Pressable>
          </View>

          <ScrollView contentContainerStyle={styles.body}>
            <Text style={styles.sectionLabel}>账号</Text>
            <Pressable style={styles.row} onPress={onOpenAccount}>
              <Text style={styles.rowText}>
                {info?.email ?? `匿名（${(info?.userId ?? '').slice(0, 8)}…）`}
              </Text>
              <Text style={styles.rowArrow}>›</Text>
            </Pressable>

            <Text style={styles.sectionLabel}>同步</Text>
            <Pressable style={styles.row} onPress={onSyncNow}>
              <Text style={styles.rowText}>立即同步</Text>
              <Text style={styles.rowArrow}>›</Text>
            </Pressable>
            <Text style={styles.note}>
              另一台设备改动后会通过实时推送立刻同步；断线时每 10 秒兜底轮询一次。
            </Text>

            <Text style={styles.sectionLabel}>历史记录</Text>
            <Pressable style={styles.row} onPress={() => setShowHistory(!showHistory)}>
              <Text style={styles.rowText}>已完成的一次性任务（{history.length}）</Text>
              <Text style={styles.rowArrow}>{showHistory ? '⌄' : '›'}</Text>
            </Pressable>
            {showHistory ? (
              <View style={styles.historyBox}>
                {history.length === 0 ? (
                  <Text style={styles.note}>还没有已完成的一次性任务。</Text>
                ) : (
                  history.map((t) => (
                    <View key={t.uuid} style={styles.historyItem}>
                      <Text style={styles.historyTitle} numberOfLines={1}>{t.title}</Text>
                      <Text style={styles.historyDate}>{t.completed_date ?? t.created_date}</Text>
                    </View>
                  ))
                )}
              </View>
            ) : null}

            <Text style={styles.sectionLabel}>其它</Text>
            <Pressable style={styles.row} onPress={handleSignOut} disabled={busy}>
              <Text style={[styles.rowText, styles.danger]}>退出登录</Text>
            </Pressable>
            <Text style={styles.note}>每日任务会在跨天后自动回到 To Do。</Text>
            <Text style={styles.version}>Tododo 手机版 1.0.0</Text>

            {busy ? <ActivityIndicator style={styles.spinner} color="#6366f1" /> : null}
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
  sectionLabel: {
    fontSize: 11, fontWeight: '700', color: '#9ca3af',
    marginTop: 18, marginBottom: 6, letterSpacing: 1,
  },
  row: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    backgroundColor: '#f3f4f6', borderRadius: 10,
    paddingHorizontal: 14, paddingVertical: 13, marginBottom: 6,
  },
  rowText: { fontSize: 14, color: '#111827', flex: 1 },
  rowArrow: { fontSize: 16, color: '#9ca3af', marginLeft: 8 },
  danger: { color: '#dc2626' },

  note: { fontSize: 11, color: '#9ca3af', lineHeight: 17, marginTop: 2, marginBottom: 4 },

  historyBox: { backgroundColor: '#fafafa', borderRadius: 10, padding: 10, marginBottom: 6 },
  historyItem: {
    flexDirection: 'row', justifyContent: 'space-between',
    paddingVertical: 7, borderBottomWidth: 1, borderBottomColor: '#eef0f3',
  },
  historyTitle: { fontSize: 13, color: '#374151', flex: 1, marginRight: 8 },
  historyDate: { fontSize: 11, color: '#9ca3af' },

  version: { fontSize: 11, color: '#c0c4cc', textAlign: 'center', marginTop: 20 },
  spinner: { marginTop: 12 },
});
