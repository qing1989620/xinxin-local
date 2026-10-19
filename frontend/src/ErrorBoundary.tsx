import { Component, type ReactNode } from "react";

type Props = {
  children: ReactNode;
  // 路由等关键标识变化时自动清除错误状态，切页即恢复，无需整页刷新。
  resetKey?: string;
};

type State = { error: Error | null };

// 渲染异常的兜底界面：任何未捕获的渲染错误都会落到这里，
// 而不是整个应用白屏。数据都在后端，刷新即可恢复。
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: { componentStack?: string | null }) {
    console.error("界面渲染出错：", error, info.componentStack);
  }

  componentDidUpdate(previous: Props) {
    if (previous.resetKey !== this.props.resetKey && this.state.error) {
      this.setState({ error: null });
    }
  }

  render() {
    const { error } = this.state;
    if (!error) return this.props.children;
    return (
      <main className="boot">
        <span className="brand-mark">x</span>
        <h1>界面出了一点问题</h1>
        <p className="muted">
          这一页没有正常显示，但你的资料和任务都安全地保存在后端。
          重新加载通常就能恢复；也可以回到工作台。
        </p>
        <div className="error-actions">
          <button
            className="button primary"
            onClick={() => window.location.reload()}
          >
            重新加载页面
          </button>
          <button
            className="button secondary"
            onClick={() => {
              window.location.href = "/";
            }}
          >
            回到工作台
          </button>
        </div>
        <details className="error-detail">
          <summary>查看技术细节</summary>
          <pre>{error.message || String(error)}</pre>
        </details>
      </main>
    );
  }
}
