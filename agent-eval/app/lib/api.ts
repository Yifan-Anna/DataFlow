import type { AgentRun, EvaluationCase, EvaluationResult } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://127.0.0.1:8000';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options?.headers },
  });
  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);
    const detail = body && typeof body === 'object' && 'detail' in body
      ? String((body as { detail: unknown }).detail)
      : null;
    throw new Error(detail ?? `请求失败（${response.status}）`);
  }
  return response.json() as Promise<T>;
}

export function runAgent(query: string, agentVersion: string): Promise<AgentRun> {
  return request('/api/agent/run', {
    method: 'POST',
    body: JSON.stringify({ query, agent_version: agentVersion }),
  });
}

export function getCases(): Promise<EvaluationCase[]> {
  return request('/api/cases');
}

export function runEvaluation(caseId: string, agentVersion: string): Promise<EvaluationResult> {
  return request('/api/evaluations/run', {
    method: 'POST',
    body: JSON.stringify({ case_id: caseId, agent_version: agentVersion }),
  });
}

export function getRun(runId: string): Promise<AgentRun> {
  return request(`/api/runs/${runId}`);
}
