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
        command_preview: 'python3 scripts/adapter_codex.py {request_file}',
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
        command_preview: 'python3 scripts/adapter_claude.py {request_file}',
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

describe('BenchmarkStudioPage', () => {
  beforeEach(() => {
    MockEventSource.instances.length = 0;
    vi.stubGlobal('EventSource', MockEventSource);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders the quick-start flow for the included repo', async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => buildAgentCatalog(),
    });
    vi.stubGlobal('fetch', fetchMock);

    render(<BenchmarkStudioPage />);

    expect(
      screen.getByRole('heading', {
        name: /launch a benchmark in three choices/i,
      })
    ).toBeInTheDocument();
    expect(screen.getByText(/clone-and-run path/i)).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: /included benchmark repo/i })[0]).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /quick demo/i })).toBeInTheDocument();

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith('/api/agents');
    });
  });

  it('submits a claude run for a custom repo and updates the live summary', async () => {
    const user = userEvent.setup();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => buildAgentCatalog(),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: 'run-123', status: 'queued' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: 'run-123', status: 'running' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          run_id: 'run-123',
          status: 'completed',
          summary: {
            inputs: {
              runner_kind: 'external',
              agent_backend: 'claude',
            },
            generated_task_count: 6,
            runnable_task_count: 3,
            alignment: {
              issue_count: 4,
              by_status: { matched: 2, missing_in_mcp: 2 },
            },
            capabilities: {
              supported: true,
              support_reason: 'Detected a pytest-compatible repository.',
              test_runner: 'pytest',
            },
            benchmark: {
              average_score: 0.84,
              task_success_rate: 0.66,
            },
            runs: [
              {
                run_id: 'mutation_validation_before_conclude-condition_md',
                task_id: 'mutation_validation_before_conclude',
                condition: 'condition_md',
                normalized_score: 0.81,
                task_success: true,
                hard_violation_count: 0,
              },
            ],
          },
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          run_id: 'run-123',
          status: 'completed',
          summary: {
            inputs: {
              runner_kind: 'external',
              agent_backend: 'claude',
            },
            generated_task_count: 6,
            runnable_task_count: 3,
            alignment: {
              issue_count: 4,
              by_status: { matched: 2, missing_in_mcp: 2 },
            },
            capabilities: {
              supported: true,
              support_reason: 'Detected a pytest-compatible repository.',
              test_runner: 'pytest',
            },
            benchmark: {
              average_score: 0.84,
              task_success_rate: 0.66,
            },
            runs: [
              {
                run_id: 'mutation_validation_before_conclude-condition_md',
                task_id: 'mutation_validation_before_conclude',
                condition: 'condition_md',
                normalized_score: 0.81,
                task_success: true,
                hard_violation_count: 0,
              },
            ],
          },
        }),
      });
    vi.stubGlobal('fetch', fetchMock);

    render(<BenchmarkStudioPage />);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith('/api/agents');
    });

    await user.click(screen.getByRole('button', { name: /another local repo/i }));
    await user.type(screen.getByLabelText(/local repo path/i), '/tmp/rippletide-platform');
    await user.click(screen.getByRole('button', { name: /real run with claude code/i }));
    await user.click(screen.getByRole('button', { name: /launch benchmark/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenNthCalledWith(
        2,
        '/api/runs',
        expect.objectContaining({ method: 'POST' })
      );
    });
    expect(MockEventSource.instances[0]?.url).toBe('/api/runs/run-123/events');

    await act(async () => {
      MockEventSource.instances[0].emit({
        event_type: 'instructions_compiled',
        timestamp: '2026-03-11T10:00:00Z',
        payload: { rule_count: 7, extraction_mode: 'codex' },
      });
    });

    await waitFor(() => {
      expect(screen.getByText('7')).toBeInTheDocument();
    });

    await act(async () => {
      MockEventSource.instances[0].emit({
        event_type: 'stream_closed',
        payload: { status: 'completed' },
      });
    });

    await waitFor(() => {
      expect(screen.getByText(/detected a pytest-compatible repository/i)).toBeInTheDocument();
      expect(screen.getByText(/84%/i)).toBeInTheDocument();
      expect(screen.getByText(/claude code · ready/i)).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /export run bundle/i })).toHaveAttribute(
        'href',
        '/api/runs/run-123/export'
      );
    });
  });
});
