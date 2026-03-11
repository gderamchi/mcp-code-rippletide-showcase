export interface CreateStudioRunInput {
  repoPath: string;
  repoArchive: File | null;
  instructionFiles: File[];
  mcpJson: string;
  runnerKind: 'demo' | 'external';
  agentBackend: 'codex' | 'claude' | 'custom';
  adapterCommand: string;
  maxWorkers: number;
}

export interface CreateStudioRunResponse {
  run_id: string;
  status: string;
}

export interface StudioRunSummary {
  run_id: string;
  status: string;
  source_root?: string;
  inputs?: {
    runner_kind?: string;
    agent_backend?: string;
    adapter_command?: string | null;
  };
  alignment?: {
    issue_count: number;
    by_status: Record<string, number>;
  };
  capabilities?: {
    language: string | null;
    test_runner: string | null;
    supported: boolean;
    support_reason: string;
  };
  generated_task_count?: number;
  runnable_task_count?: number;
  benchmark?: {
    average_score: number;
    task_success_rate: number;
  };
  runs?: Array<{
    run_id: string;
    task_id: string;
    condition: string;
    normalized_score: number;
    task_success: boolean;
    hard_violation_count: number;
  }>;
}

export interface StudioRunDetails {
  run_id: string;
  status: string;
  error?: string | null;
  summary?: StudioRunSummary;
}

export interface AgentBackendStatus {
  key: 'codex' | 'claude' | 'custom';
  label: string;
  description: string;
  available: boolean;
  authenticated: boolean;
  default_for_external: boolean;
  command_preview: string | null;
  auth_message: string;
  requires_custom_command: boolean;
}

export interface AgentCatalogResponse {
  default_external_agent: 'codex' | 'claude' | 'custom';
  agents: AgentBackendStatus[];
}

export interface StudioEventEnvelope {
  timestamp?: string;
  run_id?: string;
  event_type: string;
  payload?: Record<string, unknown>;
}
