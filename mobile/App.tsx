/**
 * Tododo 手机端主界面
 *
 * 功能对齐 PC 端：To Do / In Progress / Done 三态、点击流转状态、
 * 每日(绿) / 一次性(靛蓝) 颜色条、标题栏同步状态点。
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator, Alert, FlatList, Pressable, SafeAreaView, StyleSheet,
  Text, TextInput, View,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';

import {
  COLUMN_TITLES, SYNC_POLL_INTERVAL_MS, TASK_STATUSES, TYPE_COLORS, getNextStatus,
} from './src/config';
import {
  addTask, clearAllTasks, deleteTask, getAllTasks, initDatabase, resetDailyTasks,
  updateTaskStatus,
} from './src/db/database';
import { resetSyncCursor, runSync, type SyncStatus } from './src/sync/syncEngine';
import AccountScreen from './src/screens/AccountScreen';
import type { Task, TaskStatus, TaskType } from './src/types';

const SYNC_COLORS: Record<SyncStatus, string> = {
  idle: '#d1d5db',
  syncing: '#f59e0b',
  synced: '#10b981',
  offline: '#9ca3af',
};

const SYNC_LABELS: Record<SyncStatus, string> = {
  idle: '未同步',
  syncing: '同步中...',
  synced: '已同步',
  offline: '离线 — 恢复网络后自动同步',
};

export default function App() {
  const [ready, setReady] = useState(false);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [activeStatus, setActiveStatus] = useState<TaskStatus>('todo');
  const [syncStatus, setSyncStatus] = useState<SyncStatus>('idle');
  const [draft, setDraft] = useState('');
  const [draftType, setDraftType] = useState<TaskType>('daily');
  const [accountOpen, setAccountOpen] = useState(false);

  const refresh = useCallback(async () => {
    setTasks(await getAllTasks());
  }, []);

  const sync = useCallback(async () => {
    setSyncStatus('syncing');
    try {
      const { pulled } = await runSync();
      setSyncStatus('synced');
      // 只有云端确实带来了变化才刷新列表，避免无谓重渲染
      if (pulled > 0) await refresh();
    } catch {
      // 离线是常态，静默降级即可，本地功能照常可用
      setSyncStatus('offline');
    }
  }, [refresh]);

  // 用 ref 持有最新的 sync，避免轮询定时器捕获到过期闭包
  const syncRef = useRef(sync);
  syncRef.current = sync;

  useEffect(() => {
    let timer: ReturnType<typeof setInterval> | undefined;

    (async () => {
      await initDatabase();
      await resetDailyTasks();   // 跨天后把每日任务翻回 To Do
      await refresh();
      setReady(true);
      void syncRef.current();
      timer = setInterval(() => void syncRef.current(), SYNC_POLL_INTERVAL_MS);
    })();

    return () => {
      if (timer) clearInterval(timer);
    };
  }, [refresh]);

  const handleAdd = async () => {
    const title = draft.trim();
    if (!title) return;
    setDraft('');
    await addTask(title, draftType);
    await refresh();
    void syncRef.current();
  };

  const handleAdvance = async (task: Task) => {
    await updateTaskStatus(task.task_id, getNextStatus(task.status) as TaskStatus);
    await refresh();
    void syncRef.current();
  };

  /**
   * 登录到了另一个账号：本机现有任务属于旧账号，必须清空并重置游标后全量重拉，
   * 否则旧账号的任务会被当成待推送内容混进新账号。
   */
  const handleAccountSwitched = async () => {
    await clearAllTasks();
    await resetSyncCursor();
    await refresh();
    await syncRef.current();
    await refresh();
  };

  const handleDelete = (task: Task) => {
    Alert.alert('删除任务', `确定删除「${task.title}」？`, [
      { text: '取消', style: 'cancel' },
      {
        text: '删除',
        style: 'destructive',
        onPress: async () => {
          await deleteTask(task.task_id);
          await refresh();
          void syncRef.current();
        },
      },
    ]);
  };

  if (!ready) {
    return (
      <SafeAreaView style={[styles.screen, styles.center]}>
        <ActivityIndicator size="large" color="#6366f1" />
      </SafeAreaView>
    );
  }

  const visible = tasks.filter((t) => t.status === activeStatus);

  return (
    <SafeAreaView style={styles.screen}>
      <StatusBar style="dark" />

      {/* 标题栏 */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Tododo</Text>
        <View style={styles.headerRight}>
          <Pressable onPress={() => void syncRef.current()} hitSlop={12} style={styles.syncTouch}>
            <View style={[styles.syncDot, { backgroundColor: SYNC_COLORS[syncStatus] }]} />
            <Text style={styles.syncLabel}>{SYNC_LABELS[syncStatus]}</Text>
          </Pressable>
          <Pressable onPress={() => setAccountOpen(true)} hitSlop={12} style={styles.accountBtn}>
            <Text style={styles.accountBtnText}>账号</Text>
          </Pressable>
        </View>
      </View>

      <AccountScreen
        visible={accountOpen}
        onClose={() => setAccountOpen(false)}
        onAccountSwitched={handleAccountSwitched}
      />

      {/* 三态标签 */}
      <View style={styles.tabs}>
        {TASK_STATUSES.map((status) => {
          const count = tasks.filter((t) => t.status === status).length;
          const active = status === activeStatus;
          return (
            <Pressable
              key={status}
              onPress={() => setActiveStatus(status)}
              style={[styles.tab, active && styles.tabActive]}
            >
              <Text style={[styles.tabText, active && styles.tabTextActive]}>
                {COLUMN_TITLES[status]}{count > 0 ? ` (${count})` : ''}
              </Text>
            </Pressable>
          );
        })}
      </View>

      {/* 任务列表 */}
      <FlatList
        data={visible}
        keyExtractor={(item) => item.uuid}
        contentContainerStyle={visible.length === 0 ? styles.center : styles.listContent}
        ListEmptyComponent={<Text style={styles.empty}>这里还没有任务</Text>}
        renderItem={({ item }) => (
          <Pressable
            style={styles.card}
            onPress={() => void handleAdvance(item)}
            onLongPress={() => handleDelete(item)}
          >
            <View style={[styles.typeBar, { backgroundColor: TYPE_COLORS[item.task_type] }]} />
            <View style={styles.cardBody}>
              <Text
                style={[styles.cardTitle, item.status === 'done' && styles.cardTitleDone]}
                numberOfLines={2}
              >
                {item.title}
              </Text>
              <Text style={styles.cardMeta}>
                {item.task_type === 'daily' ? '每日' : '一次性'}
                {item.completed_date ? ` · 完成于 ${item.completed_date}` : ''}
              </Text>
            </View>
          </Pressable>
        )}
      />

      <Text style={styles.hint}>点击卡片切换状态 · 长按删除</Text>

      {/* 输入区 */}
      <View style={styles.inputRow}>
        <Pressable
          onPress={() => setDraftType(draftType === 'daily' ? 'one_time' : 'daily')}
          style={[styles.typeToggle, { backgroundColor: TYPE_COLORS[draftType] }]}
        >
          <Text style={styles.typeToggleText}>{draftType === 'daily' ? '每日' : '一次'}</Text>
        </Pressable>
        <TextInput
          style={styles.input}
          value={draft}
          onChangeText={setDraft}
          placeholder="添加新任务..."
          placeholderTextColor="#9ca3af"
          onSubmitEditing={() => void handleAdd()}
          returnKeyType="done"
        />
        <Pressable onPress={() => void handleAdd()} style={styles.addBtn}>
          <Text style={styles.addBtnText}>+</Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#f9fafb' },
  center: { flexGrow: 1, alignItems: 'center', justifyContent: 'center' },

  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 20, paddingVertical: 14,
  },
  headerTitle: { fontSize: 22, fontWeight: '700', color: '#111827' },
  headerRight: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  accountBtn: {
    paddingHorizontal: 10, paddingVertical: 5,
    borderRadius: 8, backgroundColor: '#eef0f3',
  },
  accountBtnText: { fontSize: 12, fontWeight: '600', color: '#4b5563' },
  syncTouch: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  syncDot: { width: 9, height: 9, borderRadius: 5 },
  syncLabel: { fontSize: 11, color: '#6b7280' },

  tabs: { flexDirection: 'row', paddingHorizontal: 16, gap: 8, marginBottom: 8 },
  tab: {
    flex: 1, paddingVertical: 9, borderRadius: 10,
    backgroundColor: '#eef0f3', alignItems: 'center',
  },
  tabActive: { backgroundColor: '#6366f1' },
  tabText: { fontSize: 12, fontWeight: '600', color: '#4b5563' },
  tabTextActive: { color: '#ffffff' },

  listContent: { paddingHorizontal: 16, paddingBottom: 8 },
  empty: { color: '#9ca3af', fontSize: 14 },

  card: {
    flexDirection: 'row', backgroundColor: '#ffffff', borderRadius: 12,
    marginBottom: 10, overflow: 'hidden', elevation: 1,
    shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 4, shadowOffset: { width: 0, height: 1 },
  },
  typeBar: { width: 4 },
  cardBody: { flex: 1, paddingVertical: 12, paddingHorizontal: 14 },
  cardTitle: { fontSize: 15, color: '#111827' },
  cardTitleDone: { textDecorationLine: 'line-through', color: '#9ca3af' },
  cardMeta: { fontSize: 11, color: '#9ca3af', marginTop: 4 },

  hint: { textAlign: 'center', fontSize: 11, color: '#c0c4cc', paddingBottom: 6 },

  inputRow: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    paddingHorizontal: 16, paddingVertical: 10,
    borderTopWidth: 1, borderTopColor: '#e5e7eb', backgroundColor: '#ffffff',
  },
  typeToggle: { paddingHorizontal: 10, paddingVertical: 10, borderRadius: 10 },
  typeToggleText: { color: '#ffffff', fontSize: 12, fontWeight: '700' },
  input: {
    flex: 1, backgroundColor: '#f3f4f6', borderRadius: 10,
    paddingHorizontal: 12, paddingVertical: 10, fontSize: 15, color: '#111827',
  },
  addBtn: {
    width: 42, height: 42, borderRadius: 10, backgroundColor: '#6366f1',
    alignItems: 'center', justifyContent: 'center',
  },
  addBtnText: { color: '#ffffff', fontSize: 22, lineHeight: 26, fontWeight: '600' },
});
