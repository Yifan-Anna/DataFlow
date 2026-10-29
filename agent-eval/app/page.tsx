'use client';

import { FormEvent, useMemo, useState } from 'react';

import { AppHeader } from './components/AppHeader';
import { TracePanel } from './components/TracePanel';
import { runAgent } from './lib/api';
import type { AgentRun } from './lib/types';

const examples = [
  '查询 2026 年 9 月 GMV',
  '查询 2026 年 9 月订单量',
  '查询 2026 年 9 月 GMV，并比较 8 月环比',
];

export default function PlaygroundPage() {
  const [query, setQuery] = useState(examples[2]);
  const [version, setVersion] = useState('v1.0');
  const [run, setRun] = useState<AgentRun | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function execute() {
    if (!query.trim() || loading) return;
    setLoading(true);
    setError('');
    try {
      setRun(await runAgent(query.trim(), version));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : '请求失败');
    } finally {
      setLoading(false);
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    void execute();
  }

  const result = run?.structured_result as Record<string, unknown> | null | undefined;
  const runTime = useMemo(() => new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
  }).format(new Date()), [run?.run_id]);

  return (
    <div className="app-frame">
      <AppHeader />
      <main className="playground-page page-container">
        <section className="playground-toolbar">
          <div className="playground-title">
            <span className="section-kicker">AGENT WORKSPACE</span>
            <h2>Agent Playground</h2>
            <p>与被测 Agent 交互，观察执行过程并验证结果质量。</p>
          </div>

          <div className="control-strip">
            <label>
              <span>选择 Agent</span>
              <select aria-label="选择 Agent" defaultValue="DataPilot v1.0">
                <option>DataPilot v1.0</option>
              </select>
            </label>
            <label>
              <span>Agent 版本</span>
              <select aria-label="Agent 版本" value={version} onChange={(event) => setVersion(event.target.value)}>
                <option value="v1.0">v1.0 · 标准流程</option>
                <option value="v0.9-direct">v0.9 · Badcase</option>
              </select>
            </label>
            <div className="runtime-status">
              <span>运行状态</span>
              <strong className={loading ? 'busy' : run?.status === 'failed' ? 'failed' : 'idle'}>
                <i />{loading ? '运行中' : run?.status === 'failed' ? '失败' : '空闲'}
              </strong>
            </div>
            <button className="run-button" disabled={loading} onClick={() => void execute()}>
              {loading ? <><span className="spinner" />执行中</> : <><b>▶</b>运行</>}
            </button>
          </div>
        </section>

        {version === 'v0.9-direct' && (
          <div className="badcase-banner">
            <strong>Badcase 演示</strong>
            <span>该版本故意跳过指标口径工具，用于展示“结果可能正确，但过程评测失败”。</span>
          </div>
        )}

        <section className="playground-columns">
          <article className="workspace-panel agent-panel">
            <header className="workspace-heading">
              <div className="heading-icon agent-icon">DP</div>
              <div>
                <h3>DataPilot 对话区</h3>
                <p>轻量电商经营数据分析 Agent</p>
              </div>
              <button className="ghost-button" onClick={() => { setRun(null); setError(''); }}>清空对话</button>
            </header>

            <div className="run-meta">
              <span><i className="cube-mark" />Agent: DataPilot</span>
              <span>Version: {run?.agent_version ?? version}</span>
              <span>Run ID: {run?.run_id ?? '—'}</span>
              <span>{run ? runTime : '等待运行'}</span>
            </div>

            <div className="chat-canvas">
              {run ? (
                <>
                  <div className="chat-line user-line">
                    <div className="chat-bubble user-bubble">{run.query}</div>
                    <div className="avatar user-avatar">U</div>
                  </div>
                  <div className="chat-line agent-line">
                    <div className="avatar bot-avatar">AI</div>
                    <div className={run.status === 'completed' ? 'chat-bubble agent-bubble' : 'chat-bubble agent-bubble failed-bubble'}>
                      <p>{run.final_answer}</p>
                      {result && <ResultTable result={result} />}
                      <footer><span>{runTime}</span><span>{run.total_latency_ms} ms</span></footer>
                    </div>
                  </div>
                </>
              ) : (
                <div className="chat-placeholder">
                  <div className="placeholder-orbit"><span>DP</span></div>
                  <h4>DataPilot 已就绪</h4>
                  <p>选择一个示例问题并点击运行，左侧展示回答，右侧同步生成完整执行轨迹。</p>
                </div>
              )}
            </div>

            <div className="composer-area">
              <form className="composer" onSubmit={submit}>
                <textarea
                  aria-label="输入测试问题"
                  placeholder="输入测试问题，例如：查询 2026 年 9 月 GMV"
                  rows={2}
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' && !event.shiftKey) {
                      event.preventDefault();
                      void execute();
                    }
                  }}
                />
                <button aria-label="发送问题" disabled={loading || !query.trim()} type="submit">➤</button>
              </form>
              <div className="composer-footer">
                <div className="example-menu">
                  <span>示例问题</span>
                  {examples.map((example) => <button key={example} onClick={() => setQuery(example)}>{example.replace('查询 2026 年 ', '')}</button>)}
                </div>
                <small>Enter 发送 · Shift + Enter 换行</small>
              </div>
              {error && <div className="request-error">{error}</div>}
            </div>
          </article>

          <article className="workspace-panel trace-workspace">
            <header className="workspace-heading">
              <div className="heading-icon trace-icon">≡</div>
              <div>
                <h3>Execution Trace</h3>
                <p>完整展示 Tool Calling、输入输出与单步耗时</p>
              </div>
              <span className="trace-summary">{run ? `${run.trace.length} steps · ${run.total_latency_ms} ms` : '等待执行'}</span>
            </header>
            <div className="trace-scroll">
              <TracePanel trace={run?.trace ?? []} />
            </div>
            <footer className="trace-footer">
              <div><span>Result</span><strong className={run?.status === 'completed' ? 'pass' : ''}>{run ? (run.status === 'completed' ? 'PASS' : 'FAIL') : '—'}</strong></div>
              <div><span>Tool Calls</span><strong>{run?.trace.length ?? '—'}</strong></div>
              <div><span>Total Latency</span><strong>{run ? `${run.total_latency_ms} ms` : '—'}</strong></div>
            </footer>
          </article>
        </section>
      </main>
    </div>
  );
}

function ResultTable({ result }: { result: Record<string, unknown> }) {
  const metric = String(result.metric ?? '指标');
  const value = Number(result.value ?? 0);
  const previousValue = result.previous_value == null ? null : Number(result.previous_value);
  const rate = result.mom_rate == null ? null : Number(result.mom_rate);
  const unit = String(result.unit ?? '');
  const year = Number(result.year ?? 0);
  const month = Number(result.month ?? 0);

  return (
    <div className="result-table">
      <div className="result-row result-head"><span>月份</span><span>{metric}（{unit}）</span><span>环比变化</span></div>
      <div className="result-row"><span>{year}-{String(month).padStart(2, '0')}</span><strong>{value.toLocaleString()}</strong><b className={rate != null && rate < 0 ? 'negative' : 'positive'}>{rate == null ? '—' : `${rate > 0 ? '+' : ''}${(rate * 100).toFixed(1)}%`}</b></div>
      {previousValue != null && <div className="result-row"><span>上月</span><strong>{previousValue.toLocaleString()}</strong><b>—</b></div>}
    </div>
  );
}
