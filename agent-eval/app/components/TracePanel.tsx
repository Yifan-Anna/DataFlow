import type { TraceStep } from '../lib/types';

const toolDescriptions: Record<string, string> = {
  get_metric_definition: '读取业务指标定义与计算口径',
  get_table_schema: '检查数据库字段，避免 Schema 猜测',
  run_sql: '执行只读 SQL 并返回真实数据',
};

export function TracePanel({ trace }: { trace: TraceStep[] }) {
  if (!trace.length) {
    return (
      <div className="empty-trace">
        <div className="trace-flow">
          {['指标口径', '表结构', '执行 SQL'].map((label, index) => (
            <div className="flow-item" key={label}>
              <span>{index + 1}</span><strong>{label}</strong>
              {index < 2 && <i>→</i>}
            </div>
          ))}
        </div>
        <p>运行 DataPilot 后，这里会显示每一次真实工具调用。</p>
      </div>
    );
  }

  return (
    <div className="trace-list">
      {trace.map((step, index) => (
        <div className="trace-row" key={`${step.step}-${step.tool}`}>
          <div className="trace-rail">
            <span className={step.status === 'success' ? 'step-index ok' : 'step-index failed'}>{String(step.step).padStart(2, '0')}</span>
            {index < trace.length - 1 && <div className="rail-line" />}
          </div>
          <details className="trace-card" open>
            <summary>
              <div>
                <code>{step.tool}</code>
                <p>{toolDescriptions[step.tool] ?? '工具调用'}</p>
              </div>
              <div className="trace-meta">
                <span className={step.status === 'success' ? 'status success' : 'status failure'}>{step.status === 'success' ? 'SUCCESS' : 'FAILED'}</span>
                <span>{step.latency_ms} ms</span>
              </div>
            </summary>
            <div className="payload-grid">
              <div><small>INPUT</small><pre>{JSON.stringify(step.input, null, 2)}</pre></div>
              <div><small>{step.error ? 'ERROR' : 'OUTPUT'}</small><pre>{step.error ?? JSON.stringify(step.output, null, 2)}</pre></div>
            </div>
          </details>
        </div>
      ))}
    </div>
  );
}
