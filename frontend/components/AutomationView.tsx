"use client";

import { useEffect, useState } from "react";
import {
  AlertTriangle,
  Bot,
  Calendar,
  CheckCircle2,
  Clock,
  Code2,
  Copy,
  ExternalLink,
  Eye,
  FileCode,
  FolderGit2,
  GitBranch,
  GitCommit,
  GitPullRequest,
  Lock,
  Play,
  Plus,
  RefreshCw,
  Search,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Terminal,
  ThumbsUp,
  X,
  Zap,
} from "lucide-react";
import {
  api,
  type AutomationRun,
  type AutomationSetting,
  type AutomationSettingCreate,
  type Repository,
  type User,
} from "../lib/api";

type Props = {
  user: User | null;
  onOpenPatModal: () => void;
};

const FOCUS_AREA_OPTIONS = [
  { id: "bug_detection", label: "Bug Detection & Logic Fixes", icon: AlertTriangle },
  { id: "documentation", label: "Documentation & Type Annotations", icon: FileCode },
  { id: "test_generation", label: "Automated Sandbox Test Generation", icon: ShieldCheck },
  { id: "code_improvements", label: "Refactoring & Performance Enhancements", icon: Zap },
];

export function AutomationView({ user, onOpenPatModal }: Props) {
  const [settings, setSettings] = useState<AutomationSetting[]>([]);
  const [runs, setRuns] = useState<AutomationRun[]>([]);
  const [repos, setRepos] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Active sub-tab: "overview" | "pending" | "history" | "config"
  const [activeTab, setActiveTab] = useState<"overview" | "pending" | "history" | "config">("overview");

  // New automation modal
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [selectedRepoId, setSelectedRepoId] = useState<number | "">("");
  const [scheduleTime, setScheduleTime] = useState("20:00");
  const [selectedTimezone, setSelectedTimezone] = useState("Asia/Kolkata");
  const [autoPublish, setAutoPublish] = useState(false);
  const [targetPrefix, setTargetPrefix] = useState("gitauto/daily");
  const [selectedFocus, setSelectedFocus] = useState<string[]>([
    "bug_detection",
    "documentation",
    "test_generation",
    "code_improvements",
  ]);
  const [autoTest, setAutoTest] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Running manual trigger state
  const [triggeringId, setTriggeringId] = useState<number | null>(null);

  // Approving & publishing PR state
  const [approvingRunId, setApprovingRunId] = useState<number | null>(null);

  // Log viewer modal
  const [selectedRunLogs, setSelectedRunLogs] = useState<AutomationRun | null>(null);

  const loadData = async () => {
    if (!user) {
      setLoading(false);
      return;
    }
    setError(null);
    try {
      const [settingsData, runsData, reposData] = await Promise.all([
        api.automation.settings().catch(() => []),
        api.automation.runs().catch(() => []),
        api.repositories.connections().catch(() => []),
      ]);
      const uniqueSettings = Array.from(new Map(settingsData.map((s) => [s.id, s])).values());
      const uniqueRuns = Array.from(new Map(runsData.map((r) => [r.id, r])).values());
      setSettings(uniqueSettings);
      setRuns(uniqueRuns);
      setRepos(reposData);
      if (reposData.length > 0) {
        setSelectedRepoId((prev) => (prev !== "" ? prev : reposData[0].id));
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load automation data.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [user]);

  const handleToggleSetting = async (settingId: number) => {
    try {
      const updated = await api.automation.toggleSetting(settingId);
      setSettings((prev) => prev.map((s) => (s.id === settingId ? updated : s)));
      setSuccessMsg(`Automation schedule ${updated.is_enabled ? "enabled" : "disabled"}.`);
      setTimeout(() => setSuccessMsg(null), 3500);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to toggle setting.");
    }
  };

  const handleToggleAutoPublish = async (settingId: number, currentVal: boolean) => {
    try {
      const updated = await api.automation.updateSetting(settingId, { auto_publish: !currentVal });
      setSettings((prev) => prev.map((s) => (s.id === settingId ? updated : s)));
      setSuccessMsg(`Auto-publish ${updated.auto_publish ? "enabled (Sub-60s SLA PR workflow)" : "disabled (Manual approval required)"}.`);
      setTimeout(() => setSuccessMsg(null), 3500);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to toggle auto-publish.");
    }
  };

  const handleTriggerRun = async (settingId: number) => {
    setTriggeringId(settingId);
    setError(null);
    setSuccessMsg(null);
    try {
      const newRun = await api.automation.runNow(settingId);
      setRuns((prev) => {
        const map = new Map(prev.map((r) => [r.id, r]));
        map.set(newRun.id, newRun);
        return Array.from(map.values()).sort(
          (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
      });
      setSuccessMsg(
        `Automation started! New candidate created in pending approval state (Task #${newRun.development_task_id ?? "N/A"}).`
      );
      setTimeout(() => setSuccessMsg(null), 5000);
      setActiveTab("pending");
      await loadData();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to execute daily automation.");
    } finally {
      setTriggeringId(null);
    }
  };

  const handleApproveAndPublish = async (runId: number) => {
    setApprovingRunId(runId);
    setError(null);
    setSuccessMsg(null);
    try {
      const result = await api.automation.approveAndPublish(runId);
      setRuns((prev) => prev.map((r) => (r.id === runId ? result : r)));
      setSuccessMsg(
        `Approved! Pull request #${result.pull_request_number ?? ""} created with verified commit ${result.commit_sha?.slice(0, 7) ?? ""}.`
      );
      setTimeout(() => setSuccessMsg(null), 6000);
      await loadData();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to approve and publish PR.");
    } finally {
      setApprovingRunId(null);
    }
  };

  const handleCreateSetting = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRepoId) {
      setError("Please select a connected repository.");
      return;
    }
    setIsSubmitting(true);
    setError(null);
    try {
      const payload: AutomationSettingCreate = {
        repository_connection_id: Number(selectedRepoId),
        schedule_time: scheduleTime,
        timezone: selectedTimezone,
        auto_publish: autoPublish,
        focus_areas: selectedFocus,
        target_branch_prefix: targetPrefix.trim() || "gitauto/daily",
        auto_test: autoTest,
        is_enabled: true,
      };
      const created = await api.automation.createSetting(payload);
      setSettings((prev) => {
        const map = new Map(prev.map((s) => [s.id, s]));
        map.set(created.id, created);
        return Array.from(map.values());
      });
      setShowConfigModal(false);
      setSuccessMsg("Repository automation schedule saved successfully.");
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create automation schedule.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const toggleFocusItem = (id: string) => {
    if (selectedFocus.includes(id)) {
      if (selectedFocus.length === 1) return; // Keep at least one
      setSelectedFocus(selectedFocus.filter((item) => item !== id));
    } else {
      setSelectedFocus([...selectedFocus, id]);
    }
  };

  const pendingRuns = runs.filter((r) => r.status === "pending_approval");
  const completedRuns = runs.filter((r) => r.status !== "pending_approval");

  if (!user) {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-8 text-center">
        <Shield className="mx-auto h-10 w-10 text-[var(--accent)]" />
        <h3 className="mt-4 text-base font-semibold text-white">Authentication Required</h3>
        <p className="mt-2 text-xs text-[var(--muted)]">
          Please sign in with your GitHub Personal Access Token or OAuth to access System B Daily AI Automation.
        </p>
        <button
          onClick={onOpenPatModal}
          className="mt-5 rounded-lg bg-[var(--accent)] px-4 py-2 text-xs font-semibold text-black hover:opacity-90"
        >
          Sign In
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="rounded-2xl border border-[var(--border)] bg-gradient-to-br from-[var(--surface)] via-[#12161f] to-[#0d1017] p-6 shadow-xl">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="flex h-6 items-center rounded-full border border-sky-400/20 bg-sky-400/10 px-2.5 text-[11px] font-semibold text-sky-300">
                Phase 3: System B
              </span>
              <span className="flex h-6 items-center rounded-full border border-emerald-400/20 bg-emerald-400/10 px-2.5 text-[11px] font-semibold text-emerald-300">
                Active Release Pipeline
              </span>
            </div>
            <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <Bot className="h-6 w-6 text-sky-400" /> Daily GitAuto AI Automation
            </h2>
            <p className="text-xs leading-relaxed text-[var(--muted)] max-w-2xl">
              Automated daily code analysis, AI-driven refactoring & bug detection, isolated Docker sandbox test execution,
              secret scanning, and human-verified pull request publishing with remote commit SHA integrity.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={loadData}
              disabled={loading}
              className="flex items-center gap-1.5 rounded-lg border border-[var(--border)] bg-black/40 px-3 py-2 text-xs font-medium text-zinc-300 hover:border-zinc-500 hover:text-white transition disabled:opacity-50"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-sky-400" : ""}`} />
              Refresh
            </button>
            <button
              onClick={() => setShowConfigModal(true)}
              className="flex items-center gap-1.5 rounded-lg bg-sky-500 px-3.5 py-2 text-xs font-semibold text-black hover:bg-sky-400 transition shadow-lg shadow-sky-500/20"
            >
              <Plus className="h-4 w-4" />
              Configure Repository
            </button>
          </div>
        </div>

        {/* Operational Stat Counters */}
        <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-xl border border-[var(--border)] bg-black/20 p-3.5">
            <span className="text-[11px] font-medium text-[var(--muted)]">Active Schedules</span>
            <p className="mt-1 text-lg font-semibold text-white">
              {settings.filter((s) => s.is_enabled).length}{" "}
              <span className="text-xs font-normal text-zinc-500">/ {settings.length} repos</span>
            </p>
          </div>
          <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-3.5">
            <span className="text-[11px] font-medium text-amber-300">Pending Review & PR</span>
            <p className="mt-1 text-lg font-semibold text-amber-200">{pendingRuns.length}</p>
          </div>
          <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3.5">
            <span className="text-[11px] font-medium text-emerald-300">Published Pull Requests</span>
            <p className="mt-1 text-lg font-semibold text-emerald-200">
              {runs.filter((r) => r.pull_request_number !== null).length}
            </p>
          </div>
          <div className="rounded-xl border border-[var(--border)] bg-black/20 p-3.5">
            <span className="text-[11px] font-medium text-[var(--muted)]">Total Execution Runs</span>
            <p className="mt-1 text-lg font-semibold text-white">{runs.length}</p>
          </div>
        </div>
      </div>

      {/* Notifications */}
      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-xs text-red-300 space-y-3">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-start gap-2">
              <AlertTriangle className="h-4 w-4 shrink-0 text-red-400 mt-0.5" />
              <span>{error}</span>
            </div>
            <button onClick={() => setError(null)} className="text-red-400 hover:text-white">
              <X className="h-4 w-4" />
            </button>
          </div>
          {(error.includes("403") || error.includes("personal access token") || error.includes("Token") || error.includes("permission")) && (
            <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-red-500/20 text-[11px]">
              <span className="text-zinc-200 font-medium">Update GitHub token with write access:</span>
              {onOpenPatModal && (
                <button
                  type="button"
                  onClick={onOpenPatModal}
                  className="rounded bg-sky-500 px-3 py-1 text-black font-semibold hover:bg-sky-400 transition"
                >
                  Reconnect Token
                </button>
              )}
              <a
                href="https://github.com/settings/tokens/new?scopes=repo,read:user,user:email&description=GitAuto+AI"
                target="_blank"
                rel="noreferrer"
                className="rounded border border-red-400/40 bg-black/40 px-3 py-1 text-red-200 hover:text-white transition inline-flex items-center gap-1 font-mono"
              >
                Create Classic Token (pre-filled repo scope) <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          )}
        </div>
      )}

      {successMsg && (
        <div className="flex items-center justify-between rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-xs text-emerald-300">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
            <span>{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg(null)} className="text-emerald-400 hover:text-white">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Navigation Sub-Tabs */}
      <div className="flex border-b border-[var(--border)] gap-2">
        <button
          onClick={() => setActiveTab("overview")}
          className={`border-b-2 px-4 py-2.5 text-xs font-semibold transition ${
            activeTab === "overview"
              ? "border-sky-400 text-sky-400"
              : "border-transparent text-zinc-400 hover:text-zinc-200"
          }`}
        >
          Active Repositories ({settings.length})
        </button>
        <button
          onClick={() => setActiveTab("pending")}
          className={`relative border-b-2 px-4 py-2.5 text-xs font-semibold transition ${
            activeTab === "pending"
              ? "border-amber-400 text-amber-400"
              : "border-transparent text-zinc-400 hover:text-zinc-200"
          }`}
        >
          Pending Approvals ({pendingRuns.length})
          {pendingRuns.length > 0 && (
            <span className="ml-2 inline-flex h-2 w-2 rounded-full bg-amber-400 animate-pulse" />
          )}
        </button>
        <button
          onClick={() => setActiveTab("history")}
          className={`border-b-2 px-4 py-2.5 text-xs font-semibold transition ${
            activeTab === "history"
              ? "border-sky-400 text-sky-400"
              : "border-transparent text-zinc-400 hover:text-zinc-200"
          }`}
        >
          Run History & PRs ({runs.length})
        </button>
      </div>

      {/* TAB 1: Repositories & Schedules */}
      {activeTab === "overview" && (
        <div className="space-y-4">
          {settings.length === 0 ? (
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-8 text-center">
              <FolderGit2 className="mx-auto h-8 w-8 text-zinc-500" />
              <h4 className="mt-3 text-sm font-semibold text-white">No Automated Repositories Configured</h4>
              <p className="mt-1 text-xs text-[var(--muted)] max-w-md mx-auto">
                Connect a repository to allow GitAuto AI to run daily code quality checks, generate automated tests, and stage clean pull request candidates.
              </p>
              <button
                onClick={() => setShowConfigModal(true)}
                className="mt-4 rounded-lg bg-sky-500 px-4 py-2 text-xs font-semibold text-black hover:bg-sky-400 transition"
              >
                Configure First Repository
              </button>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {settings.map((setting, idx) => (
                <div
                  key={`setting-${setting.id}-${idx}`}
                  className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5 space-y-4 hover:border-zinc-600 transition"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <FolderGit2 className="h-4 w-4 text-sky-400" />
                        <span className="text-sm font-bold text-white">
                          {setting.repository_owner}/{setting.repository_name}
                        </span>
                      </div>
                      <p className="mt-1 text-[11px] text-zinc-400 flex items-center gap-1.5">
                        <GitBranch className="h-3 w-3 text-zinc-500" /> Base: {setting.default_branch || "main"} →
                        Candidate: {setting.target_branch_prefix}/*
                      </p>
                    </div>

                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={setting.is_enabled}
                        onChange={() => handleToggleSetting(setting.id)}
                        className="sr-only peer"
                      />
                      <div className="w-9 h-5 bg-zinc-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-zinc-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-sky-500"></div>
                    </label>
                  </div>

                  {/* Badges for Focus Areas */}
                  <div className="flex flex-wrap gap-1.5">
                    {setting.focus_areas.map((area, areaIdx) => (
                      <span
                        key={`${setting.id}-${area}-${areaIdx}`}
                        className="rounded-md border border-[var(--border)] bg-black/40 px-2 py-0.5 text-[10px] text-zinc-300 font-mono"
                      >
                        {area.replace("_", " ")}
                      </span>
                    ))}
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-[11px] border-t border-[var(--border)] pt-3 text-zinc-400">
                    <div>
                      <span className="text-zinc-500">Daily Schedule:</span>
                      <p className="font-semibold text-zinc-200">
                        {setting.schedule_time} {setting.timezone === "Asia/Kolkata" ? "IST (8:00 PM)" : setting.timezone || "Asia/Kolkata"}
                      </p>
                    </div>
                    <div>
                      <span className="text-zinc-500">Next Run:</span>
                      <p className="font-semibold text-sky-400">
                        {setting.next_run_at ? new Date(setting.next_run_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) + " (scheduled)" : "Due today"}
                      </p>
                    </div>
                    <div>
                      <span className="text-zinc-500">Last Execution:</span>
                      <p className="text-zinc-300">
                        {setting.last_run_at ? new Date(setting.last_run_at).toLocaleString() : "Never"}
                      </p>
                    </div>
                    <div>
                      <span className="text-zinc-500">Auto-Publish:</span>
                      <button
                        onClick={() => handleToggleAutoPublish(setting.id, setting.auto_publish ?? false)}
                        className={`mt-0.5 inline-flex items-center gap-1 rounded px-2 py-0.5 text-[10px] font-semibold border transition ${
                          setting.auto_publish
                            ? "bg-amber-500/10 text-amber-300 border-amber-500/30 hover:bg-amber-500/20"
                            : "bg-zinc-800 text-zinc-400 border-zinc-700 hover:text-white"
                        }`}
                        title="Click to toggle automatic sub-60s PR publishing"
                      >
                        <Zap className="h-3 w-3" />
                        {setting.auto_publish ? "Auto (<=60s)" : "Manual Review"}
                      </button>
                    </div>
                  </div>

                  <div className="flex items-center justify-end gap-2 border-t border-[var(--border)] pt-3">
                    <button
                      onClick={() => handleTriggerRun(setting.id)}
                      disabled={triggeringId === setting.id}
                      className="flex items-center gap-1.5 rounded-lg border border-sky-500/40 bg-sky-500/10 px-3 py-1.5 text-xs font-semibold text-sky-300 hover:bg-sky-500/20 transition disabled:opacity-50"
                    >
                      <Play className={`h-3.5 w-3.5 ${triggeringId === setting.id ? "animate-spin" : ""}`} />
                      {triggeringId === setting.id ? "Executing Automation..." : "Run Automation Now"}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Pending Approvals (Phase 5C Candidate Pipeline) */}
      {activeTab === "pending" && (
        <div className="space-y-4">
          {pendingRuns.length === 0 ? (
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-8 text-center">
              <CheckCircle2 className="mx-auto h-8 w-8 text-emerald-400" />
              <h4 className="mt-3 text-sm font-semibold text-white">No Pending Approvals</h4>
              <p className="mt-1 text-xs text-[var(--muted)]">
                All daily automation runs have either been reviewed or published to GitHub Pull Requests.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {pendingRuns.map((run, idx) => (
                <div
                  key={`pending-run-${run.id}-${idx}`}
                  className="rounded-xl border border-amber-500/30 bg-gradient-to-r from-[var(--surface)] via-[#161a24] to-[#14181f] p-5 space-y-4 shadow-lg"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="rounded-full border border-amber-400/30 bg-amber-400/10 px-2.5 py-0.5 text-[10px] font-semibold text-amber-300">
                          Awaiting Explicit Approval
                        </span>
                        <span className="text-xs text-zinc-500">Run #{run.id}</span>
                      </div>
                      <h4 className="text-sm font-semibold text-white flex items-center gap-2">
                        <FolderGit2 className="h-4 w-4 text-sky-400" />
                        {run.repository_name}
                      </h4>
                      <p className="text-xs text-zinc-300">{run.summary}</p>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={() => setSelectedRunLogs(run)}
                        className="flex items-center gap-1.5 rounded-lg border border-[var(--border)] bg-black/40 px-3 py-1.5 text-xs font-medium text-zinc-300 hover:text-white"
                      >
                        <Eye className="h-3.5 w-3.5" />
                        Inspect Logs
                      </button>

                      <button
                        onClick={() => handleApproveAndPublish(run.id)}
                        disabled={approvingRunId === run.id}
                        className="flex items-center gap-1.5 rounded-lg bg-emerald-500 px-3.5 py-1.5 text-xs font-semibold text-black hover:bg-emerald-400 transition shadow-lg shadow-emerald-500/20 disabled:opacity-50"
                      >
                        <ThumbsUp className={`h-3.5 w-3.5 ${approvingRunId === run.id ? "animate-spin" : ""}`} />
                        {approvingRunId === run.id ? "Publishing PR..." : "Approve & Publish PR"}
                      </button>
                    </div>
                  </div>

                  {/* Readiness Verification Card */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 border-t border-[var(--border)] pt-3 text-[11px]">
                    <div className="rounded-lg border border-[var(--border)] bg-black/30 p-2.5">
                      <span className="text-zinc-500">Target Candidate Branch</span>
                      <p className="font-mono text-zinc-200 truncate">{run.target_branch || "N/A"}</p>
                    </div>
                    <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-2.5">
                      <span className="text-emerald-400">Sandbox Test Status</span>
                      <p className="font-semibold text-emerald-300">
                        {run.tests_passed ? "PASSED (Deterministic)" : "FAILED"}
                      </p>
                    </div>
                    <div className="rounded-lg border border-[var(--border)] bg-black/30 p-2.5">
                      <span className="text-zinc-500">Findings & Changes</span>
                      <p className="font-semibold text-zinc-200">
                        {run.findings_count} findings, {run.changes_count} proposed change(s)
                      </p>
                    </div>
                    <div className="rounded-lg border border-[var(--border)] bg-black/30 p-2.5">
                      <span className="text-zinc-500">Release Candidate ID</span>
                      <p className="font-semibold text-zinc-200">Candidate #{run.release_candidate_id || "N/A"}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: Run History & Published Pull Requests */}
      {activeTab === "history" && (
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-[var(--border)] bg-black/30 text-[11px] font-medium text-zinc-400">
                <tr>
                  <th className="px-4 py-3">Run ID</th>
                  <th className="px-4 py-3">Repository</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Diff Changes</th>
                  <th className="px-4 py-3">SLA Speed</th>
                  <th className="px-4 py-3">Target Branch</th>
                  <th className="px-4 py-3">Verified SHA</th>
                  <th className="px-4 py-3">Pull Request</th>
                  <th className="px-4 py-3">Executed At</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border)] text-zinc-300">
                {runs.length === 0 ? (
                  <tr>
                    <td colSpan={10} className="px-4 py-8 text-center text-zinc-500">
                      No automation runs recorded yet.
                    </td>
                  </tr>
                ) : (
                  runs.map((run, idx) => (
                    <tr key={`run-${run.id}-${idx}`} className="hover:bg-white/[0.02]">
                      <td className="px-4 py-3 font-mono text-zinc-400">#{run.id}</td>
                      <td className="px-4 py-3 font-medium text-white">{run.repository_name}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                            run.status === "approved" || run.status === "completed"
                              ? "bg-emerald-500/10 text-emerald-300 border border-emerald-500/20"
                              : run.status === "pending_approval"
                              ? "bg-amber-500/10 text-amber-300 border border-amber-500/20"
                              : "bg-red-500/10 text-red-300 border border-red-500/20"
                          }`}
                        >
                          {run.status.replace("_", " ")}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-mono text-[11px] whitespace-nowrap">
                        <span className="text-emerald-400">+{run.lines_added ?? 0}</span>{" "}
                        <span className="text-rose-400">-{run.lines_deleted ?? 0}</span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        {run.publishing_duration_ms ? (
                          <span
                            className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${
                              run.speed_target_met ? "bg-emerald-500/10 text-emerald-300" : "bg-amber-500/10 text-amber-300"
                            }`}
                          >
                            ⚡ {run.publishing_duration_ms}ms
                          </span>
                        ) : (
                          <span className="text-zinc-500 text-[10px]">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 font-mono text-[11px] text-zinc-400">{run.target_branch || "N/A"}</td>
                      <td className="px-4 py-3 font-mono text-[11px]">
                        {run.commit_sha ? (
                          <span className="text-sky-400">{run.commit_sha.slice(0, 7)}</span>
                        ) : (
                          <span className="text-zinc-500">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {run.pull_request_url ? (
                          <a
                            href={run.pull_request_url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 text-sky-400 hover:underline font-semibold"
                          >
                            <GitPullRequest className="h-3 w-3" /> PR #{run.pull_request_number}
                            <ExternalLink className="h-2.5 w-2.5" />
                          </a>
                        ) : run.status === "pending_approval" ? (
                          <span className="text-amber-400/80">Pending Approval</span>
                        ) : (
                          <span className="text-zinc-500">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-zinc-400">{new Date(run.created_at).toLocaleString()}</td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => setSelectedRunLogs(run)}
                          className="rounded border border-[var(--border)] px-2 py-1 text-[11px] font-medium text-zinc-300 hover:text-white"
                        >
                          Logs
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Configure Automation Modal */}
      {showConfigModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-[var(--border)] bg-[#14181f] p-6 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold text-white flex items-center gap-2">
                <Bot className="h-5 w-5 text-sky-400" /> Configure Daily AI Automation
              </h3>
              <button onClick={() => setShowConfigModal(false)} className="text-zinc-400 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleCreateSetting} className="mt-5 space-y-4">
              <div>
                <div className="flex items-center justify-between">
                  <label className="block text-xs font-medium text-zinc-300">Target Repository</label>
                  {repos.length === 0 && (
                    <span className="text-[11px] text-amber-400 font-medium">No connected repositories</span>
                  )}
                </div>
                {repos.length === 0 ? (
                  <div className="mt-1.5 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-200">
                    <p className="font-semibold text-white">How to add a Target Repository:</p>
                    <ol className="mt-1.5 list-decimal pl-4 space-y-1 text-zinc-300">
                      <li>Go to the <span className="font-semibold text-white">"My Repositories"</span> tab in the left sidebar.</li>
                      <li>Find your GitHub repository (e.g. <span className="text-sky-300 font-mono">kvdayananda/my-git</span>).</li>
                      <li>Click the green <span className="text-emerald-400 font-semibold">"Connect"</span> button next to it.</li>
                      <li>Return here, and your repository will automatically appear in this dropdown.</li>
                    </ol>
                  </div>
                ) : (
                  <select
                    value={selectedRepoId}
                    onChange={(e) => setSelectedRepoId(e.target.value ? Number(e.target.value) : "")}
                    className="mt-1.5 w-full rounded-lg border border-[var(--border)] bg-black/40 px-3 py-2 text-xs text-white focus:border-sky-500 focus:outline-none"
                    required
                  >
                    <option value="">Select a connected repository...</option>
                    {repos.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.owner}/{r.name} ({r.default_branch})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-zinc-300">Daily Schedule Time</label>
                  <input
                    type="time"
                    value={scheduleTime}
                    onChange={(e) => setScheduleTime(e.target.value)}
                    className="mt-1.5 w-full rounded-lg border border-[var(--border)] bg-black/40 px-3 py-2 text-xs text-white focus:border-sky-500 focus:outline-none"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-300">Timezone</label>
                  <select
                    value={selectedTimezone}
                    onChange={(e) => setSelectedTimezone(e.target.value)}
                    className="mt-1.5 w-full rounded-lg border border-[var(--border)] bg-black/40 px-3 py-2 text-xs text-white focus:border-sky-500 focus:outline-none"
                  >
                    <option value="Asia/Kolkata">Asia/Kolkata (IST - 8:00 PM)</option>
                    <option value="UTC">UTC (Universal)</option>
                    <option value="America/New_York">America/New_York (EST)</option>
                    <option value="Europe/London">Europe/London (GMT)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-300">Target Dedicated Branch Prefix</label>
                <input
                  type="text"
                  value={targetPrefix}
                  onChange={(e) => setTargetPrefix(e.target.value)}
                  className="mt-1.5 w-full rounded-lg border border-[var(--border)] bg-black/40 px-3 py-2 text-xs text-white focus:border-sky-500 focus:outline-none font-mono"
                  placeholder="gitauto/daily"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-300 mb-2">Enabled Focus Areas</label>
                <div className="space-y-2">
                  {FOCUS_AREA_OPTIONS.map((opt) => {
                    const active = selectedFocus.includes(opt.id);
                    const Icon = opt.icon;
                    return (
                      <button
                        type="button"
                        key={opt.id}
                        onClick={() => toggleFocusItem(opt.id)}
                        className={`w-full flex items-center justify-between rounded-lg border p-2.5 text-left text-xs transition ${
                          active
                            ? "border-sky-500/50 bg-sky-500/10 text-white"
                            : "border-[var(--border)] bg-black/20 text-zinc-400 hover:text-zinc-200"
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <Icon className={`h-4 w-4 ${active ? "text-sky-400" : "text-zinc-500"}`} />
                          <span>{opt.label}</span>
                        </div>
                        <input type="checkbox" checked={active} readOnly className="pointer-events-none" />
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="rounded-lg border border-[var(--border)] bg-black/30 p-3 space-y-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={autoTest}
                    onChange={(e) => setAutoTest(e.target.checked)}
                    className="rounded border-[var(--border)] text-sky-500 focus:ring-0"
                  />
                  <span className="text-xs text-zinc-200 font-medium">
                    Run Automated Tests in Docker Sandbox
                  </span>
                </label>
                <p className="text-[11px] text-zinc-400 pl-5">
                  Proposed changes will be executed and verified inside an isolated container sandbox before staging.
                </p>
              </div>

              <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3 space-y-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={autoPublish}
                    onChange={(e) => setAutoPublish(e.target.checked)}
                    className="rounded border-amber-400 text-amber-500 focus:ring-0"
                  />
                  <span className="text-xs text-amber-200 font-semibold flex items-center gap-1.5">
                    <Zap className="h-3.5 w-3.5 text-amber-400" />
                    Automatic Branch Publishing (Target &lt;= 60s SLA)
                  </span>
                </label>
                <p className="text-[11px] text-amber-300/70 pl-5">
                  When enabled, verified code changes will automatically be published to a dedicated branch and an active Pull Request opened immediately without waiting for manual human approval.
                </p>
              </div>

              <div className="mt-6 flex items-center justify-end gap-3 pt-3 border-t border-[var(--border)]">
                <button
                  type="button"
                  onClick={() => setShowConfigModal(false)}
                  className="rounded-lg border border-[var(--border)] px-4 py-2 text-xs font-medium text-zinc-300 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="rounded-lg bg-sky-500 px-4 py-2 text-xs font-semibold text-black hover:bg-sky-400 transition disabled:opacity-50"
                >
                  {isSubmitting ? "Saving..." : "Save Schedule"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Execution Log Viewer Modal */}
      {selectedRunLogs && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm">
          <div className="w-full max-w-3xl rounded-2xl border border-[var(--border)] bg-[#14181f] p-6 shadow-2xl flex flex-col max-h-[85vh]">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
              <div className="flex items-center gap-2">
                <Terminal className="h-5 w-5 text-sky-400" />
                <h3 className="text-base font-semibold text-white">
                  Execution Log – Run #{selectedRunLogs.id} ({selectedRunLogs.repository_name})
                </h3>
              </div>
              <button onClick={() => setSelectedRunLogs(null)} className="text-zinc-400 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="mt-4 flex-1 overflow-y-auto rounded-lg border border-[var(--border)] bg-black/60 p-4 font-mono text-[11px] text-zinc-300 whitespace-pre-wrap leading-relaxed">
              {selectedRunLogs.log_output || "No log output recorded."}
            </div>

            <div className="mt-4 flex items-center justify-between border-t border-[var(--border)] pt-3 text-xs">
              <span className="text-zinc-400">
                Status: <strong className="text-white uppercase">{selectedRunLogs.status}</strong>
              </span>
              <button
                onClick={() => setSelectedRunLogs(null)}
                className="rounded-lg border border-[var(--border)] px-4 py-1.5 text-xs font-medium text-zinc-300 hover:text-white"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
