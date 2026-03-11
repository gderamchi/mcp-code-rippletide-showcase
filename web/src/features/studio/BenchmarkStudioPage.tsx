import { useEffect, useMemo, useRef, useState } from 'react';
import { Card } from '../../components/ui/Card';
import { InlineNotice } from '../../components/ui/InlineNotice';
import { Button } from '../../components/ui/Button';
import {
  buildStudioEventsUrl,
  buildStudioExportUrl,
  createStudioRun,
  getAgentCatalog,
  getStudioRun,
} from '../../lib/studio/api';
import type {
  AgentBackendStatus,
  CreateStudioRunInput,
  StudioEventEnvelope,
  StudioRunDetails,
} from '../../lib/studio/types';
import styles from './BenchmarkStudioPage.module.css';

type ExecutionPreset = 'demo' | 'codex' | 'claude' | 'custom';
type TargetMode = 'included' | 'custom';

const DEFAULT_MCP_JSON = `{
  "mcpServers": {
    "rippletide": {
      "type": "http",
      "url": "https://mcp.rippletide.com/mcp"
    }
  }
}`;

const FALLBACK_AGENTS: AgentBackendStatus[] = [
  {
    key: 'codex',
    label: 'Codex',
    description: 'OpenAI Codex CLI benchmark adapter.',
    available: true,
    authenticated: true,
    default_for_external: true,
    command_preview: null,
    auth_message: 'Default external agent.',
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
    auth_message: 'Detected from the backend at runtime.',
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
    auth_message: 'Provide an adapter command.',
    requires_custom_command: true,
  },
];

function formatPercent(value: number | undefined): string {
  if (typeof value !== 'number') {
    return 'Pending';
  }
  return `${Math.round(value * 100)}%`;
}

function formatEventLabel(eventType: string): string {
  return eventType.replaceAll('_', ' ');
}

function statusLabel(agent: AgentBackendStatus): string {
  if (agent.requires_custom_command) {
    return 'manual';
  }
  if (!agent.available) {
    return 'unavailable';
  }
  return agent.authenticated ? 'ready' : 'needs auth';
}

function toRunConfig(preset: ExecutionPreset): {
  runnerKind: 'demo' | 'external';
  agentBackend: 'codex' | 'claude' | 'custom';
} {
  if (preset === 'demo') {
    return { runnerKind: 'demo', agentBackend: 'codex' };
  }
  if (preset === 'claude') {
    return { runnerKind: 'external', agentBackend: 'claude' };
  }
  if (preset === 'custom') {
    return { runnerKind: 'external', agentBackend: 'custom' };
  }
  return { runnerKind: 'external', agentBackend: 'codex' };
}

export function BenchmarkStudioPage(): JSX.Element {
  const [targetMode, setTargetMode] = useState<TargetMode>('included');
  const [repoPath, setRepoPath] = useState('');
  const [repoArchive, setRepoArchive] = useState<File | null>(null);
  const [instructionFiles, setInstructionFiles] = useState<File[]>([]);
  const [mcpJson, setMcpJson] = useState(DEFAULT_MCP_JSON);
  const [executionPreset, setExecutionPreset] = useState<ExecutionPreset>('demo');
  const [adapterCommand, setAdapterCommand] = useState('');
  const [maxWorkers, setMaxWorkers] = useState(4);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [runDetails, setRunDetails] = useState<StudioRunDetails | null>(null);
  const [events, setEvents] = useState<StudioEventEnvelope[]>([]);
  const [agents, setAgents] = useState<AgentBackendStatus[]>(FALLBACK_AGENTS);
  const eventSourceRef = useRef<EventSource | null>(null);

  const { runnerKind, agentBackend } = useMemo(
    () => toRunConfig(executionPreset),
    [executionPreset]
  );

  const selectedAgent = useMemo(
    () =>
      executionPreset === 'demo'
        ? null
        : agents.find((agent) => agent.key === agentBackend) ?? null,
    [agentBackend, agents, executionPreset]
  );

  const latestStats = useMemo(() => {
    const defaults = {
      ruleCount: 0,
      extractionMode: 'pending',
      supportedTasks: 0,
      alignmentIssues: 0,
      repoSupported: false,
    };
    return events.reduce((accumulator, event) => {
      if (event.event_type === 'instructions_compiled') {
        return {
          ...accumulator,
          ruleCount: Number(event.payload?.rule_count ?? 0),
          extractionMode: String(event.payload?.extraction_mode ?? 'deterministic'),
        };
      }
      if (event.event_type === 'bundle_ready') {
        return {
          ...accumulator,
          supportedTasks: Number(event.payload?.supported_tasks ?? 0),
          alignmentIssues: Number(event.payload?.alignment_issues ?? 0),
          repoSupported: Boolean(event.payload?.repo_supported),
        };
      }
      return accumulator;
    }, defaults);
  }, [events]);

  const presetCards = useMemo(
    () => [
      {
        key: 'demo' as const,
        label: 'Quick demo',
        description: 'Runs immediately against the included benchmark repo. No external coding agent required.',
        available: true,
        detail: 'Best first test after cloning the repo.',
      },
      {
        key: 'codex' as const,
        label: 'Real run with Codex',
        description: 'Uses the Codex adapter and runs the full matrix for real.',
        available: Boolean(
          agents.find((agent) => agent.key === 'codex')?.available &&
            agents.find((agent) => agent.key === 'codex')?.authenticated
        ),
        detail: agents.find((agent) => agent.key === 'codex')?.auth_message ?? 'Checking Codex…',
      },
      {
        key: 'claude' as const,
        label: 'Real run with Claude Code',
        description: 'Uses the Claude Code adapter and is ready for the Anthropic demo path.',
        available: Boolean(
          agents.find((agent) => agent.key === 'claude')?.available &&
            agents.find((agent) => agent.key === 'claude')?.authenticated
        ),
        detail:
          agents.find((agent) => agent.key === 'claude')?.auth_message ?? 'Checking Claude Code…',
      },
      {
        key: 'custom' as const,
        label: 'Custom adapter',
        description: 'Use any command that accepts `{request_file}` and streams benchmark NDJSON.',
        available: true,
        detail: 'For non-Codex, non-Claude integrations.',
      },
    ],
    [agents]
  );

  const launchBlocked =
    (executionPreset === 'custom' && !adapterCommand.trim()) ||
    (executionPreset !== 'demo' && selectedAgent != null && !selectedAgent.requires_custom_command
      ? !selectedAgent.available || !selectedAgent.authenticated
      : false) ||
    (targetMode === 'custom' && !repoPath.trim() && repoArchive == null);

  useEffect(() => {
    void getAgentCatalog()
      .then((payload) => {
        setAgents(payload.agents);
      })
      .catch((catalogLookupError) => {
        const message =
          catalogLookupError instanceof Error
            ? catalogLookupError.message
            : 'Failed to load the agent catalog.';
        setCatalogError(message);
      });
  }, []);

  useEffect(() => {
    return () => {
      eventSourceRef.current?.close();
    };
  }, []);

  async function refreshRun(runIdentifier: string): Promise<void> {
    const details = await getStudioRun(runIdentifier);
    setRunDetails(details);
  }

  function connectToEvents(runIdentifier: string): void {
    eventSourceRef.current?.close();
    const eventSource = new EventSource(buildStudioEventsUrl(runIdentifier));
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (message) => {
      try {
        const payload = JSON.parse(message.data) as StudioEventEnvelope;
        if (payload.event_type === 'stream_closed') {
          void refreshRun(runIdentifier);
          eventSource.close();
          return;
        }
        setEvents((current) => [payload, ...current].slice(0, 12));
        void refreshRun(runIdentifier);
      } catch {
        setEvents((current) => [
          {
            event_type: 'client_parse_warning',
            payload: { raw: message.data },
          },
          ...current,
        ]);
      }
    };
    eventSource.onerror = () => {
      eventSource.close();
    };
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setEvents([]);

    const payload: CreateStudioRunInput = {
      repoPath: targetMode === 'custom' ? repoPath : '',
      repoArchive: targetMode === 'custom' ? repoArchive : null,
      instructionFiles,
      mcpJson,
      runnerKind,
      agentBackend,
      adapterCommand,
      maxWorkers,
    };

    try {
      const response = await createStudioRun(payload);
      setRunId(response.run_id);
      await refreshRun(response.run_id);
      connectToEvents(response.run_id);
    } catch (submitError) {
      const message = submitError instanceof Error ? submitError.message : 'Unknown studio error.';
      setError(message);
    } finally {
      setSubmitting(false);
    }
  }

  const summary = runDetails?.summary;
  const exportHref = runId ? buildStudioExportUrl(runId) : null;

  return (
    <section className={styles.page}>
      <div className={styles.hero}>
        <div className={styles.heroCopy}>
          <span className={styles.eyebrow}>Dynamic Benchmark Studio</span>
          <h2 className={styles.title}>Launch a benchmark in three choices, not thirty fields.</h2>
          <p className={styles.copy}>
            After cloning the repo and running `make setup`, you can test the included benchmark
            repo immediately. For another repo, switch the target and paste its path.
          </p>
        </div>

        <Card className={styles.quickStartCard}>
          <span className={styles.metricLabel}>Quick start</span>
          <ol className={styles.quickStartList}>
            <li>Pick a target repo.</li>
            <li>Pick `Quick demo`, `Codex`, or `Claude Code`.</li>
            <li>Click `Launch benchmark`.</li>
          </ol>
          <p className={styles.metricMeta}>
            The included repo works out of the box. Other repos need a detectable `vitest`, `jest`,
            or `pytest` runner for full execution.
          </p>
        </Card>
      </div>

      <InlineNotice tone="info">
        Clone-and-run path: `make setup`, then `make studio`, then open `/studio` and click
        `Launch benchmark`.
      </InlineNotice>

      {catalogError ? <InlineNotice tone="info">{catalogError}</InlineNotice> : null}
      {error ? <InlineNotice tone="error">{error}</InlineNotice> : null}

      <div className={styles.layout}>
        <Card className={styles.primaryCard}>
          <form className={styles.form} onSubmit={handleSubmit}>
            <div className={styles.sectionBlock}>
              <div className={styles.sectionHeader}>
                <span className={styles.sectionEyebrow}>Step 1</span>
                <h3 className={styles.sectionTitle}>Choose the repo target</h3>
              </div>

              <div className={styles.choiceGrid}>
                <button
                  type="button"
                  className={[
                    styles.choiceCard,
                    targetMode === 'included' ? styles.choiceCardSelected : '',
                  ]
                    .filter(Boolean)
                    .join(' ')}
                  onClick={() => setTargetMode('included')}
                >
                  <strong>Included benchmark repo</strong>
                  <p className={styles.choiceDescription}>
                    Zero setup beyond `make setup`. Good for first-time testing after a clone.
                  </p>
                </button>
                <button
                  type="button"
                  className={[
                    styles.choiceCard,
                    targetMode === 'custom' ? styles.choiceCardSelected : '',
                  ]
                    .filter(Boolean)
                    .join(' ')}
                  onClick={() => setTargetMode('custom')}
                >
                  <strong>Another local repo</strong>
                  <p className={styles.choiceDescription}>
                    Use a local path or a zip archive when you want to benchmark another project.
                  </p>
                </button>
              </div>

              {targetMode === 'custom' ? (
                <div className={styles.stackFields}>
                  <label className={styles.field}>
                    <span className={styles.label}>Local repo path</span>
                    <input
                      className={styles.input}
                      placeholder="/Users/you/Documents/project"
                      value={repoPath}
                      onChange={(event) => setRepoPath(event.target.value)}
                    />
                  </label>
                  <label className={styles.field}>
                    <span className={styles.label}>Repository zip</span>
                    <input
                      className={styles.fileInput}
                      type="file"
                      accept=".zip"
                      onChange={(event) => setRepoArchive(event.target.files?.[0] ?? null)}
                    />
                    <span className={styles.helper}>
                      {repoArchive ? `Attached: ${repoArchive.name}` : 'Optional alternative to the local path.'}
                    </span>
                  </label>
                </div>
              ) : (
                <p className={styles.choiceHint}>
                  The Studio will use the repo you just cloned, so you can test the product
                  immediately.
                </p>
              )}
            </div>

            <div className={styles.sectionBlock}>
              <div className={styles.sectionHeader}>
                <span className={styles.sectionEyebrow}>Step 2</span>
                <h3 className={styles.sectionTitle}>Choose how to run it</h3>
              </div>

              <div className={styles.choiceGrid}>
                {presetCards.map((preset) => (
                  <button
                    key={preset.key}
                    type="button"
                    className={[
                      styles.choiceCard,
                      executionPreset === preset.key ? styles.choiceCardSelected : '',
                      !preset.available ? styles.choiceCardDisabled : '',
                    ]
                      .filter(Boolean)
                      .join(' ')}
                    onClick={() => {
                      if (preset.available) {
                        setExecutionPreset(preset.key);
                      }
                    }}
                    disabled={!preset.available}
                  >
                    <div className={styles.choiceHeader}>
                      <strong>{preset.label}</strong>
                      <span className={styles.choiceStatus}>
                        {preset.available ? 'ready' : 'not ready'}
                      </span>
                    </div>
                    <p className={styles.choiceDescription}>{preset.description}</p>
                    <p className={styles.choiceMeta}>{preset.detail}</p>
                  </button>
                ))}
              </div>

              {executionPreset === 'custom' ? (
                <label className={styles.field}>
                  <span className={styles.label}>Custom adapter command</span>
                  <input
                    className={styles.input}
                    value={adapterCommand}
                    onChange={(event) => setAdapterCommand(event.target.value)}
                    placeholder="python3 /abs/path/to/adapter.py {request_file}"
                  />
                </label>
              ) : null}
            </div>

            <details className={styles.advancedPanel}>
              <summary className={styles.advancedSummary}>Optional overrides</summary>

              <div className={styles.stackFields}>
                <label className={styles.field}>
                  <span className={styles.label}>Instruction files</span>
                  <input
                    className={styles.fileInput}
                    type="file"
                    accept=".md,.txt"
                    multiple
                    onChange={(event) => setInstructionFiles(Array.from(event.target.files ?? []))}
                  />
                  <span className={styles.helper}>
                    {instructionFiles.length > 0
                      ? `${instructionFiles.length} instruction file${instructionFiles.length > 1 ? 's' : ''} staged.`
                      : 'Leave empty to auto-detect AGENTS.md or CLAUDE.md in the target repo.'}
                  </span>
                </label>

                <label className={styles.field}>
                  <span className={styles.label}>MCP config JSON</span>
                  <textarea
                    className={styles.textarea}
                    rows={10}
                    value={mcpJson}
                    onChange={(event) => setMcpJson(event.target.value)}
                  />
                </label>

                <label className={styles.field}>
                  <span className={styles.label}>Parallel workers</span>
                  <input
                    className={styles.input}
                    type="number"
                    min={1}
                    max={16}
                    value={maxWorkers}
                    onChange={(event) => setMaxWorkers(Number(event.target.value) || 1)}
                  />
                </label>
              </div>
            </details>

            <div className={styles.actions}>
              <Button type="submit" disabled={submitting || launchBlocked}>
                {submitting ? 'Launching…' : 'Launch benchmark'}
              </Button>
              {exportHref ? (
                <a className={styles.exportLink} href={exportHref}>
                  Export run bundle
                </a>
              ) : null}
            </div>
          </form>
        </Card>

        <div className={styles.sideColumn}>
          <Card className={styles.statusCard}>
            <span className={styles.sectionEyebrow}>Current setup</span>
            <dl className={styles.definitionList}>
              <div>
                <dt>Target</dt>
                <dd>{targetMode === 'included' ? 'included repo' : 'custom repo'}</dd>
              </div>
              <div>
                <dt>Execution</dt>
                <dd>{executionPreset}</dd>
              </div>
              <div>
                <dt>Run status</dt>
                <dd>{runDetails?.status ?? 'idle'}</dd>
              </div>
              <div>
                <dt>Agent</dt>
                <dd>{selectedAgent ? `${selectedAgent.label} · ${statusLabel(selectedAgent)}` : 'not required'}</dd>
              </div>
              <div>
                <dt>Repo support</dt>
                <dd>
                  {summary?.capabilities?.supported
                    ? 'supported'
                    : latestStats.repoSupported
                      ? 'supported'
                      : 'pending'}
                </dd>
              </div>
            </dl>
          </Card>

          <Card className={styles.statusCard}>
            <span className={styles.sectionEyebrow}>Latest run</span>
            <div className={styles.metricStack}>
              <div>
                <span className={styles.metricLabel}>Rules extracted</span>
                <strong className={styles.metricValue}>{latestStats.ruleCount || '—'}</strong>
              </div>
              <div>
                <span className={styles.metricLabel}>Alignment issues</span>
                <strong className={styles.metricValue}>
                  {(summary?.alignment?.issue_count ?? latestStats.alignmentIssues) || '—'}
                </strong>
              </div>
              <div>
                <span className={styles.metricLabel}>Benchmark score</span>
                <strong className={styles.metricValue}>
                  {summary?.benchmark ? formatPercent(summary.benchmark.average_score) : 'Pending'}
                </strong>
              </div>
            </div>

            {summary?.capabilities?.support_reason ? (
              <InlineNotice tone={summary.capabilities.supported ? 'success' : 'info'}>
                {summary.capabilities.support_reason}
              </InlineNotice>
            ) : (
              <p className={styles.choiceHint}>
                Full execution needs `vitest`, `jest`, or `pytest`. Otherwise the Studio falls back
                to alignment-only reporting.
              </p>
            )}
          </Card>
        </div>
      </div>

      <Card className={styles.resultsCard}>
        <div className={styles.sectionHeader}>
          <span className={styles.sectionEyebrow}>Results</span>
          <h3 className={styles.sectionTitle}>Run matrix and live events</h3>
        </div>

        {summary?.runs?.length ? (
          <div className={styles.runGrid}>
            {summary.runs.map((run) => (
              <article key={run.run_id} className={styles.runTile}>
                <span className={styles.runTileHeader}>{run.condition}</span>
                <strong className={styles.runTileTitle}>{run.task_id}</strong>
                <span className={styles.runTileMeta}>Score {formatPercent(run.normalized_score)}</span>
                <span className={styles.runTileMeta}>
                  {run.task_success ? 'task success' : 'task incomplete'} · {run.hard_violation_count} hard violations
                </span>
              </article>
            ))}
          </div>
        ) : (
          <p className={styles.emptyState}>
            Launch a run and the MD/MCP matrix will appear here automatically.
          </p>
        )}

        {events.length ? (
          <ol className={styles.eventList}>
            {events.map((event, index) => (
              <li key={`${event.event_type}-${event.timestamp ?? index}`} className={styles.eventItem}>
                <div className={styles.eventMeta}>
                  <span>{formatEventLabel(event.event_type)}</span>
                  <span>{event.timestamp ?? 'live'}</span>
                </div>
                <pre className={styles.eventPayload}>{JSON.stringify(event.payload ?? {}, null, 2)}</pre>
              </li>
            ))}
          </ol>
        ) : (
          <p className={styles.emptyState}>
            No events yet. The feed will start once the run is created.
          </p>
        )}
      </Card>
    </section>
  );
}
