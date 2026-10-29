'use client';

import { useEffect, useMemo, useState } from 'react';

import { AppHeader } from '../components/AppHeader';
import { TracePanel } from '../components/TracePanel';
import { getCases, getRun, runEvaluation } from '../lib/api';
import type { AgentRun, EvaluationCase, EvaluationResult } from '../lib/types';

const dimensionMeta: Record<string, { label: string; color: string }> = {
  result: { label: '结果正确性', color: '#f3c846' },
  tool_selection: { label: '工具选择', color: '#e86aa8' },
  trajectory: { label: '执行轨迹', color: '#45b8ad' },
};

export default function EvaluationPage() {
  const [cases, setCases] = useState<EvaluationCase[]>([]);
  const [caseId, setCaseId] = useState('');
  const [version, setVersion] = useState('v1.0');
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null);
  const [run, setRun] = useState<AgentRun | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    getCases().then((items) => {
      setCases(items);
      setCaseId(items[0]?.case_id ?? '');
    }).catch((requestError) => setError(requestError instanceof Error ? requestError.message : '测试集加载失败'));
  }, []);

  const selectedCase = useMemo(() => cases.find((item) => item.case_id === caseId), [cases, caseId]);

  async function execute() {
    if (!caseId || loading) return;
    setLoading(true);
    setError('');
    setEvaluation(null);
    setRun(null);
    try {
      const result = await runEvaluation(caseId, version);
      setEvaluation(result);
      setRun(await getRun(result.run_id));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : '评测失败');
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <AppHeader />
      <main className="page-container page-main">
        <section className="section-heading">
          <div>
            <span className="section-kicker">EVALUATION RUNNER</span>
            <h2>执行单 Case 自动化评测</h2>
            <p>同一次真实 Agent Run，同时评价结果、工具选择与执行轨迹。</p>
          </div>
        </section>

        <section className="runner-bar panel">
          <label>测试 Case<select value={caseId} onChange={(event) => setCaseId(event.target.value)}>{cases.map((item) => <option value={item.case_id} key={item.case_id}>{item.case_id} · {item.name}</option>)}</select></label>
          <label>Agent Version<select value={version} onChange={(event) => setVersion(event.target.value)}><option value="v1.0">v1.0 · 标准流程</option><option value="v0.9-direct">v0.9 · Badcase</option></select></label>
          <button className="primary-button" onClick={execute} disabled={loading || !caseId}>{loading ? <><span className="spinner" />评测中</> : <>Run Evaluation <span>→</span></>}</button>
        </section>

        {selectedCase && <section className="case-strip"><div><span>QUESTION</span><strong>{selectedCase.query}</strong></div><div className="tag-list">{selectedCase.tags.map((tag) => <i key={tag}>{tag}</i>)}</div></section>}
        {version === 'v0.9-direct' && <div className="badcase-note"><strong>Badcase 演示模式</strong><span>旧版本会跳过指标口径工具。即使 SQL 恰好得到正确结果，过程评测仍应失败。</span></div>}
        {error && <p className="request-error standalone">{error}</p>}

        <section className="metric-grid evaluation-metrics">
          <MetricCard label="Overall" value={evaluation ? (evaluation.overall_pass ? 'PASS' : 'FAIL') : '—'} meta={evaluation ? evaluation.evaluation_id : '等待评测'} tone={evaluation ? (evaluation.overall_pass ? 'green' : 'pink') : 'plain'} />
          <MetricCard label="Score" value={evaluation ? `${Math.round(evaluation.score * 100)}%` : '—'} meta="3 个维度等权平均" />
          <MetricCard label="Agent Status" value={run ? (run.status === 'completed' ? 'Completed' : 'Failed') : '—'} meta={run?.agent_version ?? '真实模型运行'} tone={run ? (run.status === 'completed' ? 'blue' : 'pink') : 'plain'} />
          <MetricCard label="Latency" value={run ? `${(run.total_latency_ms / 1000).toFixed(2)}s` : '—'} meta={run ? `${run.trace.length} 个 Trace Step` : '包含模型与工具耗时'} />
        </section>

        <section className="evaluation-grid">
          <div className="panel dimension-panel">
            <div className="panel-heading"><div><span className="panel-number">01</span><h3>评测维度</h3></div>{evaluation && <span className={evaluation.overall_pass ? 'status success' : 'status failure'}>{evaluation.overall_pass ? 'OVERALL PASS' : 'OVERALL FAIL'}</span>}</div>
            <div className="dimension-list">
              {Object.entries(dimensionMeta).map(([key, meta]) => {
                const item = evaluation?.dimensions[key];
                const score = item ? Math.round(item.score * 100) : 0;
                return <div className="dimension-row" key={key}>
                  <div className="dimension-label"><strong>{meta.label}</strong><span>{item ? (item.pass ? 'PASS' : 'FAIL') : '—'} · {item ? `${score}%` : '等待运行'}</span></div>
                  <div className="score-track"><span style={{ width: `${score}%`, background: meta.color }} /></div>
                  <p>{item?.message ?? '运行评测后显示判断依据'}</p>
                </div>;
              })}
            </div>
            {evaluation && evaluation.failure_types.length > 0 && <div className="failure-box"><span>FAILURE TYPES</span><div>{evaluation.failure_types.map((failure) => <code key={failure}>{failure}</code>)}</div></div>}
          </div>

          <div className="panel evaluation-trace-panel">
            <div className="panel-heading"><div><span className="panel-number">02</span><h3>本次执行轨迹</h3></div>{run && <span className="subtle-pill">{run.run_id}</span>}</div>
            <TracePanel trace={run?.trace ?? []} />
          </div>
        </section>
      </main>
    </>
  );
}

function MetricCard({ label, value, meta, tone = 'plain' }: { label: string; value: string; meta: string; tone?: string }) {
  return <article className={`metric-card ${tone}`}><span>{label}</span><strong>{value}</strong><small>{meta}</small></article>;
}
