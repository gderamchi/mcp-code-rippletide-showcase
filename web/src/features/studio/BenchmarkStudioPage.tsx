import { useEffect, useMemo, useRef, useState } from 'react';
import { Card } from '../../components/ui/Card';
import { InlineNotice } from '../../components/ui/InlineNotice';
import { Button } from '../../components/ui/Button';
import {
  buildStudioEventsUrl,
  buildStudioExportUrl,
  getAgentCatalog,
  getBenchmarkProfiles,
  getStudioRun,
  runStudioBenchmark,
  runStudioPrecheck,
} from '../../lib/studio/api';
import type {
  AgentBackendStatus,
  BenchmarkPrecheckResponse,
  BenchmarkRuleCoverageItem,
  CreateStudioRunInput,
  DemoProfileResponse,
  StudioEventEnvelope,
  StudioRunDetails,
} from '../../lib/studio/types';
import styles from './BenchmarkStudioPage.module.css';

type TargetMode = 'included' | 'custom';
type ExecutionPreset = 'demo' | 'codex' | 'claude' | 'custom';
type McpSourceType = 'inline' | 'file' | 'command';

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

function isAgentSelectable(agent: AgentBackendStatus): boolean {
  return agent.available && (agent.authenticated || agent.requires_custom_command);
}

function formatPercent(value: number | undefined): string {
  if (typeof value !== 'number') {
    return 'Pending';
  }
  return `${Math.round(value * 100)}%`;
}

function formatEventLabel(eventType: string): string {
  return eventType.replaceAll('_', ' ');
}

function formatDisplayLabel(value: string): string {
  const normalized = value.replaceAll('_', ' ');
  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

function getCoverageStatusClass(
  status: BenchmarkRuleCoverageItem['coverage']['status']
): string {
  switch (status) {
    case 'covered':
      return styles.statusCovered;
    case 'missing':
      return styles.statusMissing;
    case 'ambiguous':
      return styles.statusAmbiguous;
    case 'not_applicable':
      return styles.statusNeutral;
    default:
      return '';
  }
}

function buildInputFromProfile(profile: DemoProfileResponse): CreateStudioRunInput {
  const mcpSourceType = profile.mcp_source.type;
  return {
    profileId: profile.id,
    repoPath: '',
    repoArchive: null,
    instructionFiles: [],
    instructionMarkdown: '',
    mcpJson:
      mcpSourceType === 'inline'
        ? JSON.stringify(profile.mcp_source.content ?? {}, null, 2)
        : DEFAULT_MCP_JSON,
    mcpSourceType,
    mcpSourcePath: profile.mcp_source.path ?? '',
    mcpSourceCommand: profile.mcp_source.command ?? '',
    runnerKind: profile.execution_preset === 'demo' ? 'demo' : 'external',
    agentBackend:
      profile.execution_preset === 'claude'
        ? 'claude'
        : profile.execution_preset === 'custom'
          ? 'custom'
          : 'codex',
    adapterCommand: '',
    maxWorkers: profile.max_workers,
  };
}

function buildInputFromCustom(
  targetMode: TargetMode,
  repoPath: string,
  repoArchive: File | null,
  instructionFiles: File[],
  instructionMarkdown: string,
  executionPreset: ExecutionPreset,
  mcpSourceType: McpSourceType,
  mcpJson: string,
  mcpFilePath: string,
  mcpCommand: string,
  adapterCommand: string,
  maxWorkers: number
): CreateStudioRunInput {
  return {
    profileId: null,
    repoPath: targetMode === 'custom' ? repoPath : '',
    repoArchive: targetMode === 'custom' ? repoArchive : null,
    instructionFiles,
    instructionMarkdown,
    mcpJson,
    mcpSourceType,
    mcpSourcePath: mcpFilePath,
    mcpSourceCommand: mcpCommand,
    runnerKind: executionPreset === 'demo' ? 'demo' : 'external',
    agentBackend:
      executionPreset === 'claude'
        ? 'claude'
        : executionPreset === 'custom'
          ? 'custom'
          : 'codex',
    adapterCommand,
    maxWorkers,
  };
}

export function BenchmarkStudioPage(): JSX.Element {
  const [profiles, setProfiles] = useState<DemoProfileResponse[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState<string | null>(null);
  const [agents, setAgents] = useState<AgentBackendStatus[]>(FALLBACK_AGENTS);
  const [targetMode, setTargetMode] = useState<TargetMode>('included');
  const [repoPath, setRepoPath] = useState('');
  const [repoArchive, setRepoArchive] = useState<File | null>(null);
  const [instructionFiles, setInstructionFiles] = useState<File[]>([]);
  const [instructionMarkdown, setInstructionMarkdown] = useState('');
  const [executionPreset, setExecutionPreset] = useState<ExecutionPreset>('demo');
  const [mcpSourceType, setMcpSourceType] = useState<McpSourceType>('inline');
  const [mcpJson, setMcpJson] = useState(DEFAULT_MCP_JSON);
  const [mcpFilePath, setMcpFilePath] = useState('');
  const [mcpCommand, setMcpCommand] = useState('');
  const [adapterCommand, setAdapterCommand] = useState('');
  const [maxWorkers, setMaxWorkers] = useState(8);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [precheckResult, setPrecheckResult] = useState<BenchmarkPrecheckResponse | null>(null);
  const [pendingInput, setPendingInput] = useState<CreateStudioRunInput | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [runDetails, setRunDetails] = useState<StudioRunDetails | null>(null);
  const [events, setEvents] = useState<StudioEventEnvelope[]>([]);
  const eventSourceRef = useRef<EventSource | null>(null);

  const selectedProfile = useMemo(
    () => profiles.find((profile) => profile.id === selectedProfileId) ?? null,
    [profiles, selectedProfileId]
  );
  const agentByKey = useMemo(
    () => new Map(agents.map((agent) => [agent.key, agent])),
    [agents]
  );
  const executionOptions = useMemo(
    () => [
      {
        key: 'demo' as const,
        label: 'Demo',
        description: 'Deterministic local runner for quick smoke tests.',
        disabled: false,
        helper: 'Recommended for the Quick demo profile.',
        status: 'local',
        requiresCustomCommand: false,
      },
      ...agents.map((agent) => ({
        key: agent.key as ExecutionPreset,
        label: agent.label,
        description: agent.description,
        disabled: !isAgentSelectable(agent),
        helper: agent.auth_message,
        status: agent.default_for_external ? 'default external' : agent.available ? 'external' : 'unavailable',
        requiresCustomCommand: agent.requires_custom_command,
      })),
    ],
    [agents]
  );
  const selectedExecutionOption =
    executionOptions.find((option) => option.key === executionPreset) ?? executionOptions[0];
  const selectedProfileAgent = useMemo(() => {
    if (selectedProfile == null || selectedProfile.execution_preset === 'demo') {
      return null;
    }
    return agentByKey.get(selectedProfile.execution_preset) ?? null;
  }, [agentByKey, selectedProfile]);

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

    void getBenchmarkProfiles()
      .then((payload) => {
        setProfiles(payload.profiles);
        setSelectedProfileId(
          payload.profiles.find((profile) => profile.id === 'quick-demo')?.id ??
            payload.profiles[0]?.id ??
            null
        );
      })
      .catch((profilesLookupError) => {
        const message =
          profilesLookupError instanceof Error
            ? profilesLookupError.message
            : 'Failed to load benchmark profiles.';
        setCatalogError(message);
      });
  }, []);

  useEffect(() => {
    return () => {
      eventSourceRef.current?.close();
    };
  }, []);

  useEffect(() => {
    if (selectedExecutionOption && selectedExecutionOption.disabled) {
      setExecutionPreset('demo');
    }
  }, [selectedExecutionOption]);

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
        setEvents((current) => [payload, ...current].slice(0, 20));
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

  async function launchPrecheck(input: CreateStudioRunInput): Promise<void> {
    setSubmitting(true);
    setError(null);
    setPrecheckResult(null);
    try {
      const payload = await runStudioPrecheck(input);
      setPendingInput(input);
      setPrecheckResult(payload);
    } catch (submitError) {
      const message = submitError instanceof Error ? submitError.message : 'Unknown precheck error.';
      setError(message);
    } finally {
      setSubmitting(false);
    }
  }

  async function launchBenchmark(confirmedToContinue = false): Promise<void> {
    if (pendingInput == null) {
      return;
    }
    setSubmitting(true);
    setError(null);
    setEvents([]);
    try {
      const response = await runStudioBenchmark(pendingInput, confirmedToContinue);
      setRunId(response.run_id);
      await refreshRun(response.run_id);
      connectToEvents(response.run_id);
    } catch (submitError) {
      const precheck = (submitError as Error & { precheck?: BenchmarkPrecheckResponse }).precheck;
      if (precheck) {
        setPrecheckResult(precheck);
        setError('The MCP is missing too many MD rules. Confirm before benchmarking.');
      } else {
        const message = submitError instanceof Error ? submitError.message : 'Unknown benchmark error.';
        setError(message);
      }
    } finally {
      setSubmitting(false);
    }
  }

  const selectedProfileProofRun = selectedProfile?.proof_run ?? null;
  const selectedProfileProofRunExportHref = selectedProfileProofRun
    ? buildStudioExportUrl(selectedProfileProofRun.run_id)
    : null;
  const selectedProfileProofMdRate =
    selectedProfileProofRun?.md_summary?.adherence_rate ??
    selectedProfileProofRun?.benchmark?.average_score;
  const selectedProfileProofMcpRate =
    selectedProfileProofRun?.mcp_summary?.adherence_rate ??
    selectedProfileProofRun?.benchmark?.average_score;
  const exportHref = runId ? buildStudioExportUrl(runId) : null;
  const runSummary = runDetails?.summary;
  const requiresConfirmation = precheckResult?.precheck.requires_confirmation ?? false;

  const profileCards = useMemo(
    () =>
      profiles.map((profile) => (
        <button
          key={profile.id}
          type="button"
          className={[
            styles.choiceCard,
            selectedProfile?.id === profile.id ? styles.choiceCardSelected : '',
          ]
            .filter(Boolean)
            .join(' ')}
          onClick={() => setSelectedProfileId(profile.id)}
        >
          <div className={styles.choiceHeader}>
            <strong>{profile.name}</strong>
            <span className={styles.choiceStatus}>{profile.execution_preset}</span>
          </div>
          <p className={styles.choiceDescription}>{profile.description}</p>
          <p className={styles.choiceMeta}>
            MCP: {profile.mcp_source.type} · target: {profile.target_mode}
          </p>
        </button>
      )),
    [profiles, selectedProfile]
  );

  const customInput = buildInputFromCustom(
    targetMode,
    repoPath,
    repoArchive,
    instructionFiles,
    instructionMarkdown,
    executionPreset,
    mcpSourceType,
    mcpJson,
    mcpFilePath,
    mcpCommand,
    adapterCommand,
    maxWorkers
  );

  return (
    <section className={styles.page}>
      <div className={styles.hero}>
        <div className={styles.heroCopy}>
          <span className={styles.eyebrow}>Dynamic Benchmark Studio</span>
          <h2 className={styles.title}>Measure rule adherence, not generic agent behavior.</h2>
          <p className={styles.copy}>
            The benchmark now has two stages: precheck the MCP against the MD, then run the full
            `MD vs MCP` rule-adherence matrix in parallel.
          </p>
          <p className={styles.helper}>
            Quick demo is the recommended local smoke test. Anthropic demo exercises a real external
            agent and the shared rippletide MCP.
          </p>
        </div>

        <Card className={styles.quickStartCard}>
          <span className={styles.metricLabel}>Flow</span>
          <ol className={styles.quickStartList}>
            <li>Select a profile or a custom config.</li>
            <li>Run precheck.</li>
            <li>Confirm only if the MCP is missing too many rules.</li>
            <li>Run the benchmark and compare MD vs MCP.</li>
          </ol>
        </Card>
      </div>

      {catalogError ? <InlineNotice tone="info">{catalogError}</InlineNotice> : null}
      {error ? <InlineNotice tone="error">{error}</InlineNotice> : null}

      <div className={styles.layout}>
        <Card className={styles.primaryCard}>
          <div className={styles.sectionHeader}>
            <span className={styles.sectionEyebrow}>Step 1</span>
            <h3 className={styles.sectionTitle}>Select a profile</h3>
          </div>

          <div className={styles.choiceGrid}>{profileCards}</div>

          {selectedProfile ? (
            <div className={styles.profileDetails}>
              <div className={styles.sectionHeader}>
                <span className={styles.sectionEyebrow}>Selected profile</span>
                <h4 className={styles.subTitle}>{selectedProfile.name}</h4>
              </div>

              <dl className={styles.definitionList}>
                <div>
                  <dt>Execution</dt>
                  <dd>
                    {selectedProfile.execution_preset === 'demo'
                      ? 'local smoke test'
                      : selectedProfile.execution_preset}
                  </dd>
                </div>
                <div>
                  <dt>Target</dt>
                  <dd>{selectedProfile.target_mode}</dd>
                </div>
                <div>
                  <dt>Runtime status</dt>
                  <dd>
                    {selectedProfile.execution_preset === 'demo'
                      ? 'Deterministic local runner.'
                      : selectedProfileAgent?.auth_message ?? 'Agent status unavailable.'}
                  </dd>
                </div>
                <div>
                  <dt>Instruction sources</dt>
                  <dd>{selectedProfile.instruction_sources.map((item) => item.label || item.path || item.type).join(' · ')}</dd>
                </div>
                <div>
                  <dt>MCP source</dt>
                  <dd>
                    {selectedProfile.mcp_source.type}
                    {selectedProfile.mcp_source.path ? ` · ${selectedProfile.mcp_source.path}` : ''}
                    {selectedProfile.mcp_source.command ? ` · ${selectedProfile.mcp_source.command}` : ''}
                  </dd>
                </div>
              </dl>

              <div className={styles.actions}>
                <Button
                  onClick={() => selectedProfile && void launchPrecheck(buildInputFromProfile(selectedProfile))}
                  disabled={submitting}
                >
                  {submitting ? 'Running…' : 'Run precheck'}
                </Button>
                {selectedProfileProofRunExportHref ? (
                  <a className={styles.exportLink} href={selectedProfileProofRunExportHref}>
                    Export proof run
                  </a>
                ) : null}
              </div>
            </div>
          ) : null}
        </Card>

        <div className={styles.sideColumn}>
          <Card className={styles.statusCard}>
            <span className={styles.sectionEyebrow}>Proof run</span>
            {selectedProfileProofRun ? (
              <div className={styles.metricStack}>
                <div className={styles.metricCard}>
                  <span className={styles.metricLabel}>Run id</span>
                  <strong className={styles.metricValue}>{selectedProfileProofRun.run_id}</strong>
                </div>
                <div className={styles.metricCard}>
                  <span className={styles.metricLabel}>MD score</span>
                  <strong className={styles.metricValue}>{formatPercent(selectedProfileProofMdRate)}</strong>
                </div>
                <div className={styles.metricCard}>
                  <span className={styles.metricLabel}>MCP score</span>
                  <strong className={styles.metricValue}>{formatPercent(selectedProfileProofMcpRate)}</strong>
                </div>
              </div>
            ) : (
              <p className={styles.choiceHint}>No proof run saved for this profile yet.</p>
            )}
          </Card>

          <Card className={styles.statusCard}>
            <span className={styles.sectionEyebrow}>Current run</span>
            <dl className={styles.definitionList}>
              <div>
                <dt>Status</dt>
                <dd>{runDetails?.status ?? 'idle'}</dd>
              </div>
              <div>
                <dt>Profile</dt>
                <dd>{runSummary?.inputs?.profile_name ?? precheckResult?.profile_name ?? 'none'}</dd>
              </div>
              <div>
                <dt>Agent</dt>
                <dd>{runSummary?.inputs?.agent_backend ?? precheckResult?.agent_backend ?? 'pending'}</dd>
              </div>
              <div>
                <dt>MCP source</dt>
                <dd>{runSummary?.inputs?.mcp_source_type ?? precheckResult?.mcp_source_type ?? 'pending'}</dd>
              </div>
            </dl>
            {exportHref ? (
              <a className={styles.exportLink} href={exportHref}>
                Export latest run
              </a>
            ) : null}
          </Card>
        </div>
      </div>

      <Card className={styles.primaryCard}>
        <div className={styles.sectionHeader}>
          <span className={styles.sectionEyebrow}>Custom one-off config</span>
          <h3 className={styles.sectionTitle}>Override the target, the instructions, or the MCP source</h3>
        </div>

        <form
          className={styles.form}
          onSubmit={(event) => {
            event.preventDefault();
            void launchPrecheck(customInput);
          }}
        >
          <div className={styles.sectionBlock}>
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
                <p className={styles.choiceDescription}>Use the current repo as the target.</p>
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
                <p className={styles.choiceDescription}>Use a local path or zip for a different target.</p>
              </button>
            </div>

            {targetMode === 'custom' ? (
              <div className={styles.stackFields}>
                <label className={styles.field}>
                  <span className={styles.label}>Local repo path</span>
                  <input
                    className={styles.input}
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
                </label>
              </div>
            ) : null}
          </div>

          <div className={styles.sectionBlock}>
            <div className={styles.choiceGrid}>
              {executionOptions.map((option) => (
                <button
                  key={option.key}
                  type="button"
                  className={[
                    styles.choiceCard,
                    executionPreset === option.key ? styles.choiceCardSelected : '',
                    option.disabled ? styles.choiceCardDisabled : '',
                  ]
                    .filter(Boolean)
                    .join(' ')}
                  disabled={option.disabled}
                  onClick={() => setExecutionPreset(option.key)}
                >
                  <div className={styles.choiceHeader}>
                    <strong>{option.label}</strong>
                    <span className={styles.choiceStatus}>{option.status}</span>
                  </div>
                  <p className={styles.choiceDescription}>{option.description}</p>
                  <p className={styles.choiceMeta}>{option.helper}</p>
                </button>
              ))}
            </div>

            {selectedExecutionOption?.requiresCustomCommand ? (
              <label className={styles.field}>
                <span className={styles.label}>Custom adapter command</span>
                <input
                  className={styles.input}
                  value={adapterCommand}
                  onChange={(event) => setAdapterCommand(event.target.value)}
                />
              </label>
            ) : null}
          </div>

          <details className={styles.advancedPanel}>
            <summary className={styles.advancedSummary}>Instruction and MCP overrides</summary>
            <div className={styles.stackFields}>
              <label className={styles.field}>
                <span className={styles.label}>Instruction markdown</span>
                <textarea
                  className={styles.textarea}
                  rows={8}
                  placeholder="Paste your .md instructions directly here. The Studio will send them as a temporary markdown source."
                  value={instructionMarkdown}
                  onChange={(event) => setInstructionMarkdown(event.target.value)}
                />
                <span className={styles.helper}>
                  Paste your `.md` directly here if you do not want to upload a local file.
                </span>
              </label>
              <label className={styles.field}>
                <span className={styles.label}>Instruction files</span>
                <input
                  className={styles.fileInput}
                  type="file"
                  accept=".md,.txt"
                  multiple
                  onChange={(event) => setInstructionFiles(Array.from(event.target.files ?? []))}
                />
              </label>
              <label className={styles.field}>
                <span className={styles.label}>MCP source type</span>
                <select
                  className={styles.input}
                  value={mcpSourceType}
                  onChange={(event) => setMcpSourceType(event.target.value as McpSourceType)}
                >
                  <option value="inline">inline</option>
                  <option value="file">file</option>
                  <option value="command">command</option>
                </select>
              </label>
              {mcpSourceType === 'inline' ? (
                <label className={styles.field}>
                  <span className={styles.label}>MCP JSON</span>
                  <textarea
                    className={styles.textarea}
                    rows={10}
                    value={mcpJson}
                    onChange={(event) => setMcpJson(event.target.value)}
                  />
                </label>
              ) : null}
              {mcpSourceType === 'file' ? (
                <label className={styles.field}>
                  <span className={styles.label}>MCP file path</span>
                  <input
                    className={styles.input}
                    value={mcpFilePath}
                    onChange={(event) => setMcpFilePath(event.target.value)}
                  />
                </label>
              ) : null}
              {mcpSourceType === 'command' ? (
                <label className={styles.field}>
                  <span className={styles.label}>MCP command</span>
                  <input
                    className={styles.input}
                    value={mcpCommand}
                    onChange={(event) => setMcpCommand(event.target.value)}
                  />
                </label>
              ) : null}
              <label className={styles.field}>
                <span className={styles.label}>Parallel workers</span>
                <input
                  className={styles.input}
                  type="number"
                  min={1}
                  max={64}
                  value={maxWorkers}
                  onChange={(event) => setMaxWorkers(Number(event.target.value) || 1)}
                />
              </label>
            </div>
          </details>

          <div className={styles.actions}>
            <Button type="submit" disabled={submitting}>
              {submitting ? 'Running…' : 'Run precheck'}
            </Button>
          </div>
        </form>
      </Card>

      {precheckResult ? (
        <Card className={styles.resultsCard}>
          <div className={styles.sectionHeader}>
            <span className={styles.sectionEyebrow}>Step 2</span>
            <h3 className={styles.sectionTitle}>Precheck result</h3>
          </div>
          <div className={styles.metricStack}>
            <div className={styles.metricCard}>
              <span className={styles.metricLabel}>Total rules</span>
              <strong className={styles.metricValue}>{precheckResult.precheck.total_rules}</strong>
            </div>
            <div className={styles.metricCard}>
              <span className={styles.metricLabel}>Covered by MCP</span>
              <strong className={styles.metricValue}>{precheckResult.precheck.covered_rules}</strong>
            </div>
            <div className={styles.metricCard}>
              <span className={styles.metricLabel}>Missing in MCP</span>
              <strong className={styles.metricValue}>{precheckResult.precheck.missing_rules}</strong>
            </div>
            <div className={styles.metricCard}>
              <span className={styles.metricLabel}>Ambiguous</span>
              <strong className={styles.metricValue}>{precheckResult.precheck.ambiguous_rules}</strong>
            </div>
          </div>

          <div className={styles.summaryRow}>
            <span className={styles.summaryPill}>
              Benchmarkable {precheckResult.precheck.benchmarkable_rules}
            </span>
            <span className={styles.summaryPill}>
              Excluded {precheckResult.precheck.excluded_rules}
            </span>
            <span className={styles.summaryPill}>
              Language {precheckResult.capabilities.language ?? 'Unknown'}
            </span>
            <span className={styles.summaryPill}>
              Runner {precheckResult.capabilities.test_runner ?? 'Undetected'}
            </span>
          </div>

          <p className={styles.metricMeta}>{precheckResult.capabilities.support_reason}</p>

          {requiresConfirmation ? (
            <InlineNotice tone="error">
              The MCP is missing more than {precheckResult.precheck.thresholds.missing_count} rules
              or more than {Math.round(precheckResult.precheck.thresholds.missing_percent * 100)}%
              of the MD rule set. If you continue, the MCP benchmark will likely be penalized for the
              missing rules.
            </InlineNotice>
          ) : (
            <InlineNotice tone="success">
              The MCP coverage is good enough to benchmark without confirmation.
            </InlineNotice>
          )}

          <div className={styles.actions}>
            {requiresConfirmation ? (
              <Button onClick={() => void launchBenchmark(true)} disabled={submitting}>
                {submitting ? 'Running…' : 'Run benchmark anyway'}
              </Button>
            ) : (
              <Button onClick={() => void launchBenchmark(false)} disabled={submitting}>
                {submitting ? 'Running…' : 'Launch benchmark'}
              </Button>
            )}
          </div>

          <div className={styles.sectionHeader}>
            <span className={styles.sectionEyebrow}>Rule coverage</span>
            <h4 className={styles.subTitle}>Each markdown rule mapped against the MCP manifest</h4>
          </div>

          <div className={styles.ruleList}>
            {precheckResult.precheck.rules.map((rule) => (
              <article key={rule.rule_id} className={styles.ruleItem}>
                <div className={styles.ruleHeader}>
                  <div className={styles.ruleIdentity}>
                    <span className={styles.ruleId}>{rule.rule_id}</span>
                    <div className={styles.ruleMetaRow}>
                      <span className={styles.ruleChip}>{formatDisplayLabel(rule.category)}</span>
                      <span className={styles.ruleChip}>{formatDisplayLabel(rule.severity)}</span>
                      <span className={styles.ruleChip}>
                        {formatDisplayLabel(rule.coverage.evidence_source)}
                      </span>
                    </div>
                  </div>
                  <span
                    className={[
                      styles.statusBadge,
                      getCoverageStatusClass(rule.coverage.status),
                    ]
                      .filter(Boolean)
                      .join(' ')}
                  >
                    {formatDisplayLabel(rule.coverage.status)}
                  </span>
                </div>
                <p className={styles.ruleStatement}>{rule.raw_text}</p>
                <div className={styles.ruleFooter}>
                  <span className={styles.ruleEvidence}>{rule.coverage.explanation}</span>
                  <span className={styles.ruleSource}>
                    Source {rule.source_file}
                    {rule.benchmark_family
                      ? ` · Family ${formatDisplayLabel(rule.benchmark_family)}`
                      : ''}
                  </span>
                </div>
              </article>
            ))}
          </div>
        </Card>
      ) : null}

      {runSummary?.md_summary && runSummary?.mcp_summary ? (
        <Card className={styles.resultsCard}>
          <div className={styles.sectionHeader}>
            <span className={styles.sectionEyebrow}>Step 3</span>
            <h3 className={styles.sectionTitle}>MD vs MCP benchmark</h3>
          </div>

          <div className={styles.metricStack}>
            <div className={styles.metricCard}>
              <span className={styles.metricLabel}>MD adherence</span>
              <strong className={styles.metricValue}>
                {formatPercent(runSummary.md_summary.adherence_rate)}
              </strong>
            </div>
            <div className={styles.metricCard}>
              <span className={styles.metricLabel}>MCP adherence</span>
              <strong className={styles.metricValue}>
                {formatPercent(runSummary.mcp_summary.adherence_rate)}
              </strong>
            </div>
            <div className={styles.metricCard}>
              <span className={styles.metricLabel}>Runtime</span>
              <strong className={styles.metricValue}>
                {Math.round((runSummary.benchmark_runtime_ms ?? 0) / 1000)}s
              </strong>
            </div>
          </div>

          <div className={styles.runGrid}>
            {(runSummary.category_comparisons ?? []).map((category) => (
              <article key={category.category} className={styles.runTile}>
                <span className={styles.runTileHeader}>{category.category}</span>
                <strong className={styles.runTileTitle}>MD {formatPercent(category.md_rate)}</strong>
                <strong className={styles.runTileTitle}>MCP {formatPercent(category.mcp_rate)}</strong>
                <span className={styles.runTileMeta}>Delta {Math.round(category.delta * 100)} pts</span>
              </article>
            ))}
          </div>

          <details className={styles.advancedPanel}>
            <summary className={styles.advancedSummary}>Rule-by-rule diff</summary>
            <div className={styles.eventList}>
              {(runSummary.rule_comparisons ?? []).map((item) => (
                <div key={item.rule_id} className={styles.eventItem}>
                  <div className={styles.eventMeta}>
                    <span>{item.rule_id}</span>
                    <span>{item.category}</span>
                  </div>
                  <div className={styles.choiceMeta}>
                    MD: {item.md_verdict} · MCP: {item.mcp_verdict} · Delta {Math.round(item.delta * 100)} pts
                  </div>
                </div>
              ))}
            </div>
          </details>

          <details className={styles.advancedPanel}>
            <summary className={styles.advancedSummary}>Live events</summary>
            <div className={styles.eventList}>
              {events.length ? (
                events.map((event, index) => (
                  <div key={`${event.event_type}-${event.timestamp ?? index}`} className={styles.eventItem}>
                    <div className={styles.eventMeta}>
                      <span>{formatEventLabel(event.event_type)}</span>
                      <span>{event.timestamp ?? 'live'}</span>
                    </div>
                    <pre className={styles.eventPayload}>{JSON.stringify(event.payload ?? {}, null, 2)}</pre>
                  </div>
                ))
              ) : (
                <p className={styles.choiceHint}>No live events recorded for this run.</p>
              )}
            </div>
          </details>
        </Card>
      ) : null}
    </section>
  );
}
