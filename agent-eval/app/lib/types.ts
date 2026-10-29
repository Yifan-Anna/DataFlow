export type TraceStep = {
  step: number;
  type: 'tool_call';
  tool: string;
  input: Record<string, unknown>;
  output: Record<string, unknown> | null;
  status: 'success' | 'failed';
  latency_ms: number;
  error: string | null;
};

export type AgentRun = {
  run_id: string;
  agent_name: string;
  agent_version: string;
  query: string;
  status: 'completed' | 'failed';
  trace: TraceStep[];
  final_answer: string;
  structured_result: Record<string, unknown> | null;
  total_latency_ms: number;
  error: string | null;
};

export type EvaluationCase = {
  case_id: string;
  name: string;
  category: string;
  query: string;
  expected: {
    result: Record<string, number>;
    tools: string[];
    tool_order: string[];
  };
  tags: string[];
};

export type DimensionResult = {
  pass: boolean;
  score: number;
  message: string | null;
  details: Record<string, unknown>;
};

export type EvaluationResult = {
  evaluation_id: string;
  run_id: string;
  case_id: string;
  overall_pass: boolean;
  score: number;
  dimensions: Record<string, DimensionResult>;
  failure_types: string[];
};
