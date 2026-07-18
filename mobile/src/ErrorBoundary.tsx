/**
 * 错误边界
 *
 * 没有它的话，任何渲染期异常都表现为「白屏 + 终端里什么都看不到」，
 * 排查起来非常痛苦（加 expo-audio 那次就是这样）。这里把错误直接显示在屏幕上。
 */
import { Component, type ErrorInfo, type ReactNode } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
  stack: string | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null, stack: null };

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    this.setState({ stack: info.componentStack ?? null });
    console.error('[Tododo] 渲染出错:', error, info.componentStack);
  }

  render() {
    const { error, stack } = this.state;
    if (!error) return this.props.children;

    return (
      <View style={styles.container}>
        <Text style={styles.title}>出错了</Text>
        <Text style={styles.hint}>
          把下面的内容发给开发者即可定位问题。重启 app 可恢复。
        </Text>
        <ScrollView style={styles.box}>
          <Text style={styles.message}>{error.message}</Text>
          {stack ? <Text style={styles.stack}>{stack}</Text> : null}
        </ScrollView>
      </View>
    );
  }
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff', padding: 24, paddingTop: 64 },
  title: { fontSize: 20, fontWeight: '700', color: '#dc2626', marginBottom: 6 },
  hint: { fontSize: 12, color: '#6b7280', marginBottom: 14, lineHeight: 18 },
  box: { flex: 1, backgroundColor: '#f9fafb', borderRadius: 10, padding: 12 },
  message: { fontSize: 13, color: '#111827', marginBottom: 12 },
  stack: { fontSize: 11, color: '#6b7280', lineHeight: 16 },
});
