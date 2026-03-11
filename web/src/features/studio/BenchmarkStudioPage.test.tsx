import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BenchmarkStudioPage } from './BenchmarkStudioPage';

class MockEventSource {
  static instances: MockEventSource[] = [];

  onmessage: ((event: MessageEvent<string>) => void) | null = null;
  onerror: (() => void) | null = null;
  url: string;

  constructor(url: string) {
    this.url = url;
    MockEventSource.instances.push(this);
  }

  close(): void {}

  emit(data: unknown): void {
    this.onmessage?.({ data: JSON.stringify(data) } as MessageEvent<string>);
  }
}

function buildAgentCatalog() {
  return {
    default_external_agent: 'codex',
    agents: [
      {
        key: 'codex',
        label: 'Codex',
        description: 'OpenAI Codex CLI benchmark adapter.',
        available: true,
        authenticated: true,
        default_for_external: true,
        command_preview: null,
        auth_message: 'Logged in using ChatGPT',
        requires_custom_command: false,
      },
      {
        key: 'claude',
        label: 'Claude Code',
        description: 'Anthropic Claude Code CLI benchmark adapter.',
        available: true,
        authenticated: true,
        default_for_external: false,
        command_preview: null,
        auth_message: 'Claude Code detected',
        requires_custom_command: false,
      },
      {
        key: 'custom',
        label: 'Custom command',
        description: 'Any adapter command that implements the benchmark NDJSON contract.',
        available: true,
        authenticated: false,
        default_for_external: false,
        command_preview: null,
        auth_message: 'Provide a full adapter command.',
        requires_custom_command: true,
      },
    ],
  };
}

function buildProfiles() {
  return {
    profiles: [
      {
        id: 'anthropic-demo',
        name: 'Anthropic demo',
        description: 'Included repo plus Claude Code and the shared rippletide MCP profile.',
        target_mode: 'included',
        execution_preset: 'claude',
        instruction_sources: [
          {
            type: 'repo_file',
            path: 'benchmark/profiles/prompts/studio-anthropic.md',
            label: 'Anthropic demo prompt',
          },
        ],
        mcp_source: {
          type: 'file',
          path: 'benchmark/profiles/mcp/rippletide.mcp.json',
        },
        max_workers: 2,
        proof_run: {
          run_id: '15ddae9ccd6e',
          md_summary: { adherence_rate: 0.71 },
          mcp_summary: { adherence_rate: 0.85 },
        },
      },
      {
        id: 'quick-demo',
        name: 'Quick demo',
        description: 'Fastest path for testing the included benchmark repo after cloning.',
        target_mode: 'included',
        execution_preset: 'demo',
        instruction_sources: [],
        mcp_source: {
          type: 'file',
          path: 'benchmark/profiles/mcp/rippletide.mcp.json',
        },
        max_workers: 2,
        proof_run: null,
      },
    ],
  };
}

function buildPrecheckResponse(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    profile_id: 'anthropic-demo',
    profile_name: 'Anthropic demo',
    source_root: '/tmp/repo',
    runner_kind: 'external',
    agent_backend: 'claude',
    instruction_sources: [
      {
        type: 'repo_file',
        origin: 'benchmark/profiles/prompts/studio-anthropic.md',
        label: 'Anthropic demo prompt',
      },
    ],
    mcp_source_type: 'file',
    mcp_source_origin: 'benchmark/profiles/mcp/rippletide.mcp.json',
    capabilities: {
      supported: true,
      support_reason: 'Detected a pytest-compatible repository.',
      test_runner: 'pytest',
      language: 'python',
    },
    precheck: {
      total_rules: 12,
      benchmarkable_rules: 9,
      excluded_rules: 3,
      covered_rules: 10,
      missing_rules: 1,
      ambiguous_rules: 1,
      requires_confirmation: false,
      thresholds: {
        missing_count: 5,
        missing_percent: 0.1,
      },
      rules: [
        {
          rule_id: 'benchmark-agents-1',
          source_rule_id: 'agents-1',
          category: 'validation',
          severity: 'hard',
          benchmarkable: true,
          benchmark_family: 'validate_before_conclude',
          normalized_claim: 'validate before conclude',
          raw_text: 'Validate before concluding.',
          source_file: 'AGENTS.md',
          non_benchmarkable_reason: '',
          coverage: {
            status: 'covered',
            evidence_source: 'manifest',
            explanation: 'Covered.',
          },
        },
      ],
    },
    ...overrides,
  };
}

function buildBenchmarkSummary() {
  return {
    run_id: 'run-123',
    status: 'completed',
    inputs: {
      profile_id: 'anthropic-demo',
      profile_name: 'Anthropic demo',
      agent_backend: 'claude',
      mcp_source_type: 'file',
    },
    md_summary: {
      rule_count: 9,
      adherence_rate: 0.66,
      pass_count: 5,
      partial_count: 2,
      fail_count: 2,
    },
    mcp_summary: {
      rule_count: 9,
      adherence_rate: 0.88,
      pass_count: 8,
      partial_count: 1,
      fail_count: 0,
    },
    category_comparisons: [
      {
        category: 'validation',
        md_rate: 0.5,
        mcp_rate: 1,
        delta: 0.5,
        rule_count: 1,
      },
    ],
    rule_comparisons: [
      {
        rule_id: 'benchmark-agents-1',
        category: 'validation',
        md_verdict: 'fail',
        mcp_verdict: 'pass',
        delta: 1,
        md_result: {
          verdict: 'fail',
          ratio: 0,
          evidence: ['MD failed to validate.'],
        },
        mcp_result: {
          verdict: 'pass',
          ratio: 1,
          evidence: ['MCP validated successfully.'],
        },
      },
    ],
    violations: {
      md_only: ['benchmark-agents-1'],
      mcp_only: [],
      shared: [],
    },
    benchmark_runtime_ms: 80000,
  };
}

describe('BenchmarkStudioPage', () => {
  beforeEach(() => {
    MockEventSource.instances.length = 0;
    vi.stubGlobal('EventSource', MockEventSource);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders profile-first quick start and proof run details', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => buildAgentCatalog() })
      .mockResolvedValueOnce({ ok: true, json: async () => buildProfiles() });
    vi.stubGlobal('fetch', fetchMock);

    render(<BenchmarkStudioPage />);

    expect(
      screen.getByRole('heading', {
        name: /measure rule adherence, not generic agent behavior/i,
      })
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith('/api/profiles');
    });

    expect(screen.getAllByRole('button', { name: /run precheck/i })[0]).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /export proof run/i })).toHaveAttribute(
      'href',
      '/api/runs/15ddae9ccd6e/export'
    );
  });

  it('runs precheck first and then launches the benchmark', async () => {
    const user = userEvent.setup();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => buildAgentCatalog() })
      .mockResolvedValueOnce({ ok: true, json: async () => buildProfiles() })
      .mockResolvedValueOnce({ ok: true, json: async () => buildPrecheckResponse() })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ run_id: 'run-123', status: 'queued' }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ run_id: 'run-123', status: 'running' }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ run_id: 'run-123', status: 'completed', summary: buildBenchmarkSummary() }) });
    vi.stubGlobal('fetch', fetchMock);

    render(<BenchmarkStudioPage />);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith('/api/profiles');
    });

    await user.click(screen.getAllByRole('button', { name: /^run precheck$/i })[0]);

    await waitFor(() => {
      expect(
        fetchMock.mock.calls.some(
          (call) =>
            call[0] === '/api/precheck' &&
            (call[1] as { method?: string } | undefined)?.method === 'POST'
        )
      ).toBe(true);
    });
    expect(screen.getByText(/the mcp coverage is good enough to benchmark without confirmation/i)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /launch benchmark/i }));

    await waitFor(() => {
      expect(
        fetchMock.mock.calls.some(
          (call) =>
            call[0] === '/api/benchmark' &&
            (call[1] as { method?: string } | undefined)?.method === 'POST'
        )
      ).toBe(true);
    });

    expect(MockEventSource.instances[0]?.url).toBe('/api/runs/run-123/events');

    await act(async () => {
      MockEventSource.instances[0].emit({
        event_type: 'stream_closed',
        payload: { status: 'completed' },
      });
    });

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(6);
    });

    await waitFor(() => {
      expect(screen.getByText(/MD adherence/i)).toBeInTheDocument();
      expect(screen.getAllByText(/88%/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/benchmark-agents-1/i).length).toBeGreaterThan(0);
    });
  });
});
