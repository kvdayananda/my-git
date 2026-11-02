"use client";

import {
  Activity,
  BarChart3,
  Bot,
  CalendarClock,
  CheckCircle2,
  ChevronRight,
  CircleHelp,
  Clock,
  Cpu,
  Database,
  ExternalLink,
  FolderGit2,
  GitBranch,
  GitCommit,
  GitPullRequest,
  Key,
  LayoutDashboard,
  Menu,
  Play,
  RefreshCw,
  Settings,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  TerminalSquare,
  User as UserIcon,
  X,
  Zap,
} from "lucide-react";
import { useEffect, useState } from "react";
import { DiffViewer } from "../components/DiffViewer";
import { JobProgressTracker } from "../components/JobProgressTracker";
import { BackupView } from "../components/BackupView";
import { ProfileView } from "../components/ProfileView";
import { AutomationView } from "../components/AutomationView";
import { AnalyticsDashboardView } from "../components/AnalyticsDashboardView";
import { PublishingHistoryView } from "../components/PublishingHistoryView";
import {
  api,
  type ActivityEvent,
  type Analysis,
  type DashboardStats,
  type DevelopmentTask,
  type ReleaseCandidate,
  type Repository,
  type SystemStatus,
  type TestRun,
  type User,
} from "../lib/api";

type ViewKey =
  | "overview"
  | "profile"
  | "repositories"
  | "workspace"
  | "automation"
  | "publishing_history"
  | "analytics"
  | "backups"
  | "activity"
  | "settings";

const navigation: { key: ViewKey; label: string; icon: typeof LayoutDashboard }[] = [
  { key: "overview", label: "Dashboard", icon: LayoutDashboard },
  { key: "profile", label: "My Profile", icon: UserIcon },
  { key: "repositories", label: "My Repositories", icon: FolderGit2 },
  { key: "workspace", label: "AI Development", icon: Bot },
  { key: "automation", label: "Daily Automation", icon: CalendarClock },
  { key: "publishing_history", label: "Publishing History", icon: Clock },
  { key: "analytics", label: "Analytics", icon: BarChart3 },
  { key: "backups", label: "Local Backup", icon: ShieldCheck },
  { key: "activity", label: "Activity Logs", icon: Activity },
];

const pageCopy: Record<Exclude<ViewKey, "overview">, { eyebrow: string; title: string; description: string }> = {
  profile: { eyebrow: "Account & GitHub Identity", title: "User Profile & Account Settings", description: "Manage your GitAuto AI identity, view synchronized GitHub account stats, configure timezones, and set alert preferences." },
  repositories: { eyebrow: "Repository Manager", title: "Connected GitHub Repositories", description: "Authorize GitHub access and select the repositories GitAuto AI is allowed to inspect and enhance." },
  workspace: { eyebrow: "AI Developer Workspace", title: "AI Code Generation & Task Planning", description: "Describe real development tasks. Generated code, bug fixes, and tests require approval before publishing." },
  automation: { eyebrow: "System B Daily AI Scheduler", title: "Daily Automation & Workers", description: "Automated daily code analysis, AI-driven improvements, Docker sandbox test validation, and PR publishing at 8:00 PM Asia/Kolkata (IST)." },
  publishing_history: { eyebrow: "Audit Trail & Verification", title: "Daily Publishing History", description: "Complete audit log of verified remote commit SHAs, GitHub diff additions/deletions, and sub-60s SLA performance." },
  analytics: { eyebrow: "Telemetry & Contribution Metrics", title: "Publishing Analytics Dashboard", description: "Detailed daily, weekly, monthly, and lifetime code modification and publishing performance metrics." },
  backups: { eyebrow: "System A Daily GitHub Backup", title: "Windows-Compatible Daily Local Backup", description: "Connect local project folders to GitHub repositories, enforce secret exclusion, run dry-run simulations, and verify remote commit SHAs." },
  activity: { eyebrow: "Activity Audit Logs", title: "Activity Audit Logs", description: "Task events, validation results, approvals, pushes, and failures recorded without secrets." },
  settings: { eyebrow: "System & Workspace Settings", title: "Control Your Workspace", description: "Inspect system integrations, Docker sandbox runtime, database target, and safety policies." },
};

function StatusBadge() {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-2.5 py-1 text-xs font-medium text-emerald-200">
      <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
      Phase 5C.2 Verified
    </span>
  );
}

function EmptyState({
  title,
  description,
  icon: Icon = TerminalSquare,
}: {
  title: string;
  description: string;
  icon?: typeof TerminalSquare;
}) {
  return (
    <div className="rounded-xl border border-dashed border-[var(--border)] bg-[var(--surface)]/60 p-8 text-center">
      <Icon className="mx-auto mb-4 h-8 w-8 text-[var(--accent)]" />
      <h3 className="text-sm font-semibold text-white">{title}</h3>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-[var(--muted)]">{description}</p>
    </div>
  );
}

function Overview({ onNavigate, user }: { onNavigate: (view: ViewKey) => void; user: User | null }) {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(false);

  const loadStats = async () => {
    if (!user) return;
    setLoading(true);
    try {
      setStats(await api.dashboard.stats());
    } catch {
      // stats remain null
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) void loadStats();
  }, [user]);

  const cards = [
    { label: "Connected repositories", value: stats?.connected_repositories, sub: user ? "Active in workspace" : "Requires sign in" },
    { label: "Tasks executed", value: stats?.tasks_executed, sub: user ? "Total development tasks" : "Requires sign in" },
    { label: "Pending reviews", value: stats?.pending_reviews, sub: user ? "Awaiting your approval" : "Requires sign in" },
    { label: "Successful releases", value: stats?.successful_releases, sub: user ? "Pushed to dedicated branches" : "Requires sign in" },
  ];

  return (
    <div className="space-y-8">
      <div className="grid-background overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 sm:p-8">
        <div className="max-w-2xl">
          <StatusBadge />
          <h1 className="mt-5 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
            Build with intention, ship with confidence.
          </h1>
          <p className="mt-4 max-w-xl text-sm leading-7 text-[var(--muted)]">
            GitAuto AI helps you analyze existing repositories, plan improvements, validate generated code in isolated Docker containers, and publish only after explicit human approval.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <button
              onClick={() => onNavigate("repositories")}
              className="inline-flex items-center gap-2 rounded-lg bg-[var(--accent-strong)] px-4 py-2.5 text-sm font-semibold text-[#06130b] transition hover:bg-[var(--accent)]"
            >
              Connect a repository <ChevronRight className="h-4 w-4" />
            </button>
            <button
              onClick={() => onNavigate("workspace")}
              className="inline-flex items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-[#1a231e]"
            >
              Open AI Workspace
            </button>
            <button
              onClick={() => onNavigate("backups")}
              className="inline-flex items-center gap-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-2.5 text-sm font-semibold text-emerald-300 transition hover:bg-emerald-500/20"
            >
              <ShieldCheck className="h-4 w-4" /> Daily Backup (System A)
            </button>
            <button
              onClick={() => onNavigate("profile")}
              className="inline-flex items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2.5 text-sm font-semibold text-zinc-300 transition hover:bg-[#1a231e] hover:text-white"
            >
              <UserIcon className="h-4 w-4 text-[var(--accent)]" /> My Profile
            </button>
          </div>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map((c) => (
          <div key={c.label} className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
            <p className="text-xs text-[var(--muted)]">{c.label}</p>
            <p className="mt-3 text-3xl font-bold text-white tracking-tight">
              {loading ? "…" : c.value !== undefined ? c.value : "—"}
            </p>
            <p className="mt-2 text-xs text-[var(--muted)]">{c.sub}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-white flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-[var(--accent)]" /> Safety Guarantees
            </h3>
            <span className="text-xs text-emerald-300 font-mono">Fail-Closed</span>
          </div>
          <ul className="mt-4 space-y-2.5 text-xs text-[var(--muted)]">
            <li className="flex items-start gap-2">
              <CheckCircle2 className="h-4 w-4 text-[var(--accent)] shrink-0 mt-0.5" />
              <span>Repositories must be explicitly connected; the application never creates repos.</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="h-4 w-4 text-[var(--accent)] shrink-0 mt-0.5" />
              <span>Secret files (<code className="text-white">.env</code>, private keys, caches) are strictly excluded from AI context.</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="h-4 w-4 text-[var(--accent)] shrink-0 mt-0.5" />
              <span>Isolated Docker sandbox runs tests with dropped capabilities and no network access.</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="h-4 w-4 text-[var(--accent)] shrink-0 mt-0.5" />
              <span>Releases push strictly to dedicated <code className="text-white">gitauto/task-...</code> branches after user review.</span>
            </li>
          </ul>
        </div>

        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-white flex items-center gap-2">
              <GitCommit className="h-4 w-4 text-[var(--accent)]" /> Workflow Pipeline
            </h3>
            <span className="text-xs text-[var(--muted)]">6 Stages</span>
          </div>
          <div className="mt-4 space-y-2 text-xs text-[var(--muted)]">
            <div className="flex items-center gap-2">
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[#1c2a23] text-[var(--accent)] font-semibold text-[10px]">1</span>
              <span>Inspect repository structure & analyze AST/technologies</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[#1c2a23] text-[var(--accent)] font-semibold text-[10px]">2</span>
              <span>Formulate development plan with explicit user approval</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[#1c2a23] text-[var(--accent)] font-semibold text-[10px]">3</span>
              <span>Generate validated changes & compute unified diffs</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[#1c2a23] text-[var(--accent)] font-semibold text-[10px]">4</span>
              <span>Execute automated tests in rootless Docker sandbox</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[#1c2a23] text-[var(--accent)] font-semibold text-[10px]">5</span>
              <span>Require explicit user approval on verified candidate hash</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[#1c2a23] text-[var(--accent)] font-semibold text-[10px]">6</span>
              <span>Commit & push via GitHub Git Database API with concurrency leasing</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function PatModal({
  isOpen,
  onClose,
  onSuccess,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (user: User) => void;
}) {
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!isOpen) return null;

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token.trim()) {
      setError("Please enter a GitHub Personal Access Token.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await api.auth.loginWithPat(token.trim());
      if (res.user) {
        onSuccess(res.user);
        onClose();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "GitHub token authentication failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl border border-[var(--border)] bg-[#12161f] p-6 shadow-2xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Key className="h-5 w-5 text-[var(--accent)]" />
            <h3 className="text-base font-semibold text-white">Connect GitHub Token</h3>
          </div>
          <button onClick={onClose} className="text-[var(--muted)] hover:text-white" aria-label="Close">
            <X className="h-5 w-5" />
          </button>
        </div>
        <p className="text-xs text-[var(--muted)]">
          Paste a GitHub Personal Access Token to instantly inspect and manage your real repositories without registering an OAuth App.
        </p>
        <form onSubmit={handleConnect} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-white mb-1.5">
              Personal Access Token
            </label>
            <input
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="ghp_... or github_pat_..."
              className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3.5 py-2.5 text-sm text-white outline-none placeholder:text-[var(--muted)] focus:border-[var(--accent)] font-mono"
              autoFocus
            />
          </div>
          <div className="text-[11px] text-[var(--muted)] flex items-center justify-between">
            <span>Requires <code className="text-white">repo</code> and <code className="text-white">read:user</code> scopes.</span>
            <a
              href="https://github.com/settings/tokens/new?scopes=repo,read:user,user:email&description=GitAuto+AI"
              target="_blank"
              rel="noreferrer"
              className="text-[var(--accent)] hover:underline inline-flex items-center gap-1"
            >
              Generate Token <ExternalLink className="h-3 w-3" />
            </a>
          </div>
          <p className="text-[11px] text-emerald-400/90">
            Tip: You can also type <code className="rounded bg-black/40 px-1 py-0.5 text-white">demo</code> to instantly explore offline with simulated repositories.
          </p>
          {error && (
            <p className="rounded-lg border border-red-400/20 bg-red-400/10 px-3 py-2 text-xs text-red-200">
              {error}
            </p>
          )}
          <div className="flex items-center justify-between pt-2">
            <a
              href={api.auth.demoLoginUrl}
              className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-xs font-medium text-emerald-300 hover:text-white transition"
            >
              Launch Demo Mode
            </a>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={onClose}
                className="rounded-lg border border-[var(--border)] px-4 py-2 text-xs font-semibold text-[var(--muted)] hover:text-white"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="rounded-lg bg-[var(--accent-strong)] px-4 py-2 text-xs font-semibold text-[#06130b] hover:bg-[var(--accent)] transition disabled:opacity-50"
              >
                {loading ? "Verifying..." : "Connect Account"}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

function RepositoryManager({ user, onOpenPat }: { user: User | null; onOpenPat?: () => void }) {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const loadRepositories = async () => {
    setLoading(true);
    setError("");
    try {
      setRepositories((await api.repositories.list(1, search)).items);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Repositories could not be loaded.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) void loadRepositories();
  }, [user]);

  const connect = async (repository: Repository) => {
    try {
      await api.repositories.connect(repository.id);
      setRepositories((current) => current.map((item) => (item.id === repository.id ? { ...item, connected: true } : item)));
      setNotice(`${repository.owner}/${repository.name} is connected.`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The repository could not be connected.");
    }
  };

  if (!user) {
    return (
      <div className="space-y-4">
        <EmptyState
          title="Connect GitHub to continue"
          description="Repository access is only available after a GitHub session is established. You can use Demo Mode, connect via Personal Access Token, or sign in via OAuth."
          icon={GitBranch}
        />
        <div className="flex flex-wrap justify-center gap-3 pt-2">
          <a
            href={api.auth.demoLoginUrl}
            className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2 text-xs font-semibold text-white hover:bg-[var(--surface-raised)] transition"
          >
            Instant Demo Sign-In
          </a>
          {onOpenPat && (
            <button
              onClick={onOpenPat}
              className="rounded-lg border border-white/20 bg-white/5 px-4 py-2 text-xs font-semibold text-white hover:bg-white/10 transition"
            >
              Connect Token (PAT)
            </button>
          )}
          <a
            href={api.auth.loginUrl}
            className="rounded-lg bg-[var(--accent-strong)] px-4 py-2 text-xs font-semibold text-[#06130b] hover:bg-[var(--accent)] transition"
          >
            Connect GitHub OAuth
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {user.login === "demo-developer" && (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-xl border border-emerald-500/20 bg-emerald-950/20 px-4 py-3 text-xs text-emerald-200">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-emerald-400 shrink-0" />
            <span>
              <strong>Demo Mode Active:</strong> Exploring with simulated repositories. Connect any sample repo to test analysis and automated PR workflows.
            </span>
          </div>
          {onOpenPat && (
            <button
              onClick={onOpenPat}
              className="shrink-0 rounded-lg border border-emerald-400/30 bg-emerald-500/10 px-2.5 py-1 text-[11px] font-semibold text-emerald-100 hover:bg-emerald-500/20 transition"
            >
              Connect Real GitHub Token
            </button>
          )}
        </div>
      )}
      <div className="flex flex-col gap-3 sm:flex-row">
        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          onKeyDown={(event) => event.key === "Enter" && void loadRepositories()}
          placeholder="Search repositories"
          className="min-w-0 flex-1 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2.5 text-sm text-white outline-none placeholder:text-[var(--muted)] focus:border-[var(--accent)]"
        />
        <button onClick={() => void loadRepositories()} className="rounded-lg border border-[var(--border)] px-4 py-2.5 text-sm font-medium text-white hover:bg-[var(--surface)]">
          Search
        </button>
      </div>
      {notice && <p className="rounded-lg border border-emerald-400/20 bg-emerald-400/10 px-4 py-3 text-sm text-emerald-200">{notice}</p>}
      {error && <p className="rounded-lg border border-red-400/20 bg-red-400/10 px-4 py-3 text-sm text-red-200">{error}</p>}
      {loading && <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-8 text-center text-sm text-[var(--muted)]">Loading authorized repositories…</div>}
      {!loading && repositories.length === 0 && !error && (
        <EmptyState title="No accessible repositories found" description="GitHub returned no repositories for this account and search filter." icon={FolderGit2} />
      )}
      {!loading && repositories.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-[var(--border)]">
          <div className="divide-y divide-[var(--border)]">
            {repositories.map((repository) => (
              <div key={repository.id} className="flex flex-col gap-4 bg-[var(--surface)] p-5 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-medium text-white">{repository.owner}/{repository.name}</h3>
                    <span className="rounded-full border border-[var(--border)] px-2 py-0.5 text-[11px] text-[var(--muted)]">{repository.visibility}</span>
                    {repository.language && <span className="text-xs text-[var(--muted)]">{repository.language}</span>}
                  </div>
                  <p className="mt-1 truncate text-sm text-[var(--muted)]">{repository.description ?? "No description provided."}</p>
                  <p className="mt-2 text-xs text-[var(--muted)]">Default branch: {repository.default_branch} · {repository.can_push ? "Write access" : "Read access"}</p>
                </div>
                <button
                  disabled={repository.connected}
                  onClick={() => void connect(repository)}
                  className={`shrink-0 rounded-lg px-3 py-2 text-sm font-medium ${
                    repository.connected
                      ? "cursor-default border border-emerald-400/20 bg-emerald-400/10 text-emerald-200"
                      : "bg-[var(--accent-strong)] text-[#06130b] hover:bg-[var(--accent)]"
                  }`}
                >
                  {repository.connected ? "Connected" : "Connect"}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function AnalysisWorkspace({ user }: { user: User | null }) {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeJobId, setActiveJobId] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    api.repositories.connections().then((items) => {
      setRepositories(items);
      if (items[0]) setSelected(items[0].id);
    }).catch((reason) => setError(reason instanceof Error ? reason.message : "Repositories could not be loaded."));
  }, [user]);

  useEffect(() => {
    if (selected === null) return;
    api.analyses.latest(selected).then(setAnalysis).catch(() => setAnalysis(null));
  }, [selected]);

  const runAnalysis = async () => {
    if (selected === null) return;
    setLoading(true);
    setError("");
    try {
      setAnalysis(await api.analyses.start(selected));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Analysis could not be completed.");
    } finally {
      setLoading(false);
    }
  };

  const runAnalysisAsync = async () => {
    if (selected === null) return;
    setError("");
    try {
      const res = await api.analyses.startAsync(selected);
      setActiveJobId(res.job_id);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Background analysis could not be started.");
    }
  };

  if (!user) return <EmptyState title="Connect GitHub to analyze a repository" description="Analysis is available only for repositories explicitly connected to your authenticated GitHub account." icon={Sparkles} />;
  if (!repositories.length) return <EmptyState title="Connect a repository first" description="Choose a repository in Repository manager before starting an evidence-based analysis." icon={FolderGit2} />;

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-3 sm:flex-row items-stretch sm:items-center">
        <select value={selected ?? ""} onChange={(event) => setSelected(Number(event.target.value))} className="flex-1 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2.5 text-sm text-white">
          {repositories.map((repository) => (
            <option key={repository.id} value={repository.id}>{repository.owner}/{repository.name}</option>
          ))}
        </select>
        <div className="flex items-center gap-2">
          <button
            onClick={() => void runAnalysisAsync()}
            disabled={loading || Boolean(activeJobId)}
            className="inline-flex items-center gap-1.5 rounded-lg bg-[var(--accent-strong)] px-4 py-2.5 text-sm font-semibold text-[#06130b] hover:bg-[var(--accent)] transition disabled:opacity-50"
            title="Execute non-blocking analysis via background Celery worker"
          >
            <Sparkles className="h-4 w-4" /> Analyze (Worker)
          </button>
          <button
            onClick={() => void runAnalysis()}
            disabled={loading || Boolean(activeJobId)}
            className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2.5 text-sm font-medium text-white hover:bg-[var(--surface-raised)] transition disabled:opacity-50"
          >
            {loading ? "Analyzing…" : "Direct Analyze"}
          </button>
        </div>
      </div>

      {activeJobId && (
        <JobProgressTracker
          jobId={activeJobId}
          title="Celery Background Repository Inspection"
          description="Scanning tree files, calculating AST metrics, and applying deterministic rules..."
          onSuccess={async () => {
            if (selected !== null) {
              const updated = await api.analyses.latest(selected);
              setAnalysis(updated);
            }
          }}
          onError={(err) => setError(err)}
          onDismiss={() => setActiveJobId(null)}
        />
      )}

      {error && (
        <div className="rounded-lg border border-red-400/20 bg-red-400/10 px-4 py-3 text-sm text-red-200">
          {error}
          <button onClick={() => void runAnalysis()} className="ml-3 underline">Retry</button>
        </div>
      )}
      {!analysis && !loading && !activeJobId && <EmptyState title="No analysis yet" description="Start an analysis to inspect the selected commit, technologies, findings, and development plan." icon={Bot} />}
      {analysis && (
        <div className="space-y-5">
          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-lg font-semibold text-white">Repository report</h2>
              <span className="rounded-full border border-[var(--border)] px-2.5 py-1 text-xs text-[var(--muted)]">{analysis.status}</span>
            </div>
            <p className="mt-3 text-sm leading-6 text-[var(--muted)]">{analysis.project_summary}</p>
            <p className="mt-3 text-xs text-[var(--muted)]">Commit: <code>{analysis.commit_sha}</code> · {analysis.file_inventory.length} files inspected</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {analysis.detected_technologies.map((technology) => (
                <span key={technology} className="rounded-full bg-[#1c2a23] px-2.5 py-1 text-xs text-[var(--accent)]">{technology}</span>
              ))}
            </div>
          </div>
          <section>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-white">Findings</h2>
            {analysis.findings.length ? (
              <div className="space-y-3">
                {analysis.findings.map((finding) => (
                  <article key={finding.id} className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-medium text-white">{finding.title}</h3>
                      <span className="text-xs text-amber-200">{finding.severity} · {Math.round(finding.confidence * 100)}% confidence</span>
                    </div>
                    <p className="mt-2 text-sm text-[var(--muted)]">{finding.description}</p>
                    <p className="mt-2 text-xs text-[var(--muted)]">Evidence: {finding.evidence}</p>
                  </article>
                ))}
              </div>
            ) : (
              <EmptyState title="No deterministic findings" description="No supported issues were identified by the current inspection rules." />
            )}
          </section>
          <section>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-white">Prioritized development plan</h2>
            <div className="space-y-3">
              {analysis.development_plan.map((t) => (
                <article key={t.id} className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
                  <div className="flex justify-between gap-3">
                    <h3 className="font-medium text-white">{t.title}</h3>
                    <span className="text-xs text-[var(--accent)]">{t.priority} priority</span>
                  </div>
                  <p className="mt-2 text-sm text-[var(--muted)]">{t.description}</p>
                  <p className="mt-2 text-xs text-[var(--muted)]">Test strategy: {t.test_strategy}</p>
                </article>
              ))}
            </div>
          </section>
          {analysis.limitations.length > 0 && (
            <div className="rounded-lg border border-amber-400/20 bg-amber-400/10 p-4 text-sm text-amber-100">
              <strong>Incomplete inspection:</strong>
              <ul className="mt-2 list-disc pl-5">
                {analysis.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function DevelopmentWorkspace({ user }: { user: User | null }) {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [repositoryId, setRepositoryId] = useState<number | null>(null);
  const [taskType, setTaskType] = useState("improvement");
  const [instructions, setInstructions] = useState("");
  const [task, setTask] = useState<DevelopmentTask | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [diff, setDiff] = useState("");
  const [testRun, setTestRun] = useState<TestRun | null>(null);
  const [candidate, setCandidate] = useState<ReleaseCandidate | null>(null);
  const [activeJob, setActiveJob] = useState<{
    id: string;
    title: string;
    type: "generation" | "tests";
  } | null>(null);

  useEffect(() => {
    if (!user) return;
    api.repositories.connections().then((items) => {
      setRepositories(items);
      if (items[0]) setRepositoryId(items[0].id);
    }).catch((reason) => setError(reason instanceof Error ? reason.message : "Repositories could not be loaded."));
  }, [user]);

  const create = async () => {
    if (repositoryId === null || !instructions.trim()) return;
    setBusy(true);
    setError("");
    try {
      setTask(await api.tasks.create(repositoryId, taskType, instructions));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Task could not be created.");
    } finally {
      setBusy(false);
    }
  };

  const update = async (action: () => Promise<DevelopmentTask>) => {
    setBusy(true);
    setError("");
    try {
      setTask(await action());
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Task action failed.");
    } finally {
      setBusy(false);
    }
  };

  const generateAsync = async () => {
    if (!task) return;
    setError("");
    try {
      const res = await api.tasks.generateAsync(task.id);
      setActiveJob({
        id: res.job_id,
        title: "Generating Proposed Code Changes (Celery Worker)",
        type: "generation",
      });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Failed to start background generation.");
    }
  };

  const runTestsAsync = async () => {
    if (!task) return;
    setError("");
    try {
      const res = await api.tasks.runTestsAsync(task.id);
      setActiveJob({
        id: res.job_id,
        title: "Executing Tests in Isolated Docker Sandbox (Worker)",
        type: "tests",
      });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Failed to start background test execution.");
    }
  };

  useEffect(() => {
    if (!task || !task.changes.length) return;
    api.tasks.diff(task.id).then((result) => setDiff(result.diff)).catch(() => setDiff(""));
  }, [task]);

  const runTests = async () => {
    if (!task) return;
    setBusy(true);
    setError("");
    try {
      setTestRun(await api.tasks.runTests(task.id));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Task action failed.");
    } finally {
      setBusy(false);
    }
  };

  const createCandidate = async () => {
    if (!task) return;
    setBusy(true);
    setError("");
    try {
      setCandidate(await api.tasks.createCandidate(task.id));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Release candidate could not be created.");
    } finally {
      setBusy(false);
    }
  };

  const candidateAction = async (action: (id: number) => Promise<ReleaseCandidate>) => {
    if (!candidate) return;
    setBusy(true);
    setError("");
    try {
      setCandidate(await action(candidate.id));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Release candidate action failed.");
    } finally {
      setBusy(false);
    }
  };

  if (!user) return <EmptyState title="Connect GitHub to create a task" description="Development tasks require an authenticated repository connection." icon={Bot} />;

  return (
    <div className="space-y-5">
      {!task && (
        <div className="space-y-3 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <div className="grid gap-3 sm:grid-cols-2">
            <select value={repositoryId ?? ""} onChange={(event) => setRepositoryId(Number(event.target.value))} className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-white">
              {repositories.map((repository) => <option key={repository.id} value={repository.id}>{repository.owner}/{repository.name}</option>)}
            </select>
            <select value={taskType} onChange={(event) => setTaskType(event.target.value)} className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-white">
              <option value="feature">Generate feature</option>
              <option value="improvement">Improve existing code</option>
              <option value="bug_fix">Fix verified bug</option>
              <option value="tests">Add unit tests</option>
              <option value="documentation">Improve documentation</option>
              <option value="refactor">Refactor selected files</option>
              <option value="error_handling">Improve error handling</option>
              <option value="type_annotations">Improve type annotations</option>
            </select>
          </div>
          <textarea
            value={instructions}
            onChange={(event) => setInstructions(event.target.value)}
            placeholder="Describe the reviewed development task…"
            className="min-h-28 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-white placeholder:text-[var(--muted)]"
          />
          <button onClick={() => void create()} disabled={busy || !instructions.trim() || repositoryId === null} className="rounded-lg bg-[var(--accent-strong)] px-4 py-2.5 text-sm font-semibold text-[#06130b] disabled:opacity-50">
            {busy ? "Creating…" : "Create task"}
          </button>
        </div>
      )}
      {error && <div className="rounded-lg border border-red-400/20 bg-red-400/10 p-4 text-sm text-red-200">{error}</div>}
      {task && (
        <div className="space-y-4 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="font-semibold text-white">Task #{task.id}</h2>
              <p className="mt-1 text-xs text-[var(--muted)]">Base commit: {task.base_commit_sha}{task.token_usage ? ` · ${task.token_usage} tokens` : ""}</p>
            </div>
            <span className="rounded-full border border-[var(--border)] px-2.5 py-1 text-xs text-[var(--muted)]">{task.status}</span>
          </div>
          {task.plan ? (
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-white">{task.plan.summary}</h3>
              <p className="text-sm text-[var(--muted)]">{task.plan.objective}</p>
              <ul className="list-disc space-y-1 pl-5 text-sm text-[var(--muted)]">
                {task.plan.steps.map((step) => <li key={step}>{step}</li>)}
              </ul>
              {task.status === "awaiting_plan_approval" && (
                <button onClick={() => void update(() => api.tasks.approvePlan(task.id))} disabled={busy} className="rounded-lg bg-[var(--accent-strong)] px-4 py-2 text-sm font-semibold text-[#06130b]">
                  Approve plan
                </button>
              )}
              {task.status === "generating" && (
                <div className="flex flex-wrap items-center gap-2">
                  <button
                    onClick={() => void generateAsync()}
                    disabled={busy || Boolean(activeJob)}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-[var(--accent-strong)] px-4 py-2 text-sm font-semibold text-[#06130b] hover:bg-[var(--accent)] transition disabled:opacity-50"
                    title="Generate code using background Celery worker"
                  >
                    <Sparkles className="h-4 w-4" /> Generate proposed changes (Celery Worker)
                  </button>
                  <button
                    onClick={() => void update(() => api.tasks.generate(task.id))}
                    disabled={busy || Boolean(activeJob)}
                    className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2 text-sm text-white hover:bg-[var(--surface-raised)] transition disabled:opacity-50"
                  >
                    Direct generate
                  </button>
                </div>
              )}
            </div>
          ) : (
            <button onClick={() => void update(() => api.tasks.plan(task.id))} disabled={busy} className="rounded-lg bg-[var(--accent-strong)] px-4 py-2 text-sm font-semibold text-[#06130b]">
              Generate plan
            </button>
          )}

          {activeJob && (
            <JobProgressTracker
              jobId={activeJob.id}
              title={activeJob.title}
              description="Executing with secure boundary enforcement and real-time worker tracking..."
              onSuccess={async () => {
                try {
                  const updatedTask = await api.tasks.get(task.id);
                  setTask(updatedTask);
                  if (activeJob.type === "tests") {
                    const latest = await api.tasks.latestTest(task.id);
                    setTestRun(latest);
                  }
                } catch {
                  // error loading latest task
                }
              }}
              onError={(err) => setError(err)}
              onDismiss={() => setActiveJob(null)}
            />
          )}

          {task.changes.length > 0 && (
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-semibold text-white">Generated files ({task.changes.length})</h3>
                <ul className="mt-2 space-y-1 text-sm text-[var(--muted)]">
                  {task.changes.map((change) => <li key={change.id}><code>{change.file_path}</code> · {change.operation} · {change.reason}</li>)}
                </ul>
              </div>

              {diff && (
                <div className="space-y-2">
                  <h3 className="text-sm font-semibold text-white">Review Proposed Code Changes</h3>
                  <DiffViewer diff={diff} />
                </div>
              )}

              <div className="flex flex-wrap items-center gap-2 pt-2">
                <button
                  onClick={() => void runTestsAsync()}
                  disabled={busy || Boolean(activeJob) || task.status !== "awaiting_review"}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-[var(--accent-strong)] px-3.5 py-2 text-sm font-semibold text-[#06130b] hover:bg-[var(--accent)] transition disabled:opacity-50"
                  title="Run tests in isolated Docker sandbox via background worker"
                >
                  <TerminalSquare className="h-4 w-4" /> Run tests (Docker Worker)
                </button>
                <button
                  onClick={() => void runTests()}
                  disabled={busy || Boolean(activeJob) || task.status !== "awaiting_review"}
                  className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-white hover:bg-[var(--surface-raised)] transition disabled:opacity-50"
                >
                  Direct test run
                </button>
              </div>
              {testRun && (
                <div className="mt-3 rounded-lg border border-[var(--border)] p-3 text-xs text-[var(--muted)]">
                  <strong className="text-white">Test status: {testRun.status}</strong>
                  <p className="mt-1">{testRun.summary}</p>
                  <p className="mt-1">Candidate hash: <code>{testRun.candidate_hash}</code></p>
                  {testRun.error_details && <p className="mt-1 text-amber-200">{testRun.error_details}</p>}
                  {testRun.stdout && <pre className="mt-2 max-h-40 overflow-auto">{testRun.stdout}</pre>}
                </div>
              )}
              {testRun?.status === "passed" && !candidate && (
                <button onClick={() => void createCandidate()} disabled={busy} className="mt-3 rounded-lg bg-[var(--accent-strong)] px-3 py-2 text-sm font-semibold text-[#06130b]">
                  Create release candidate
                </button>
              )}
              {candidate && (
                <div className="mt-4 space-y-3 rounded-lg border border-[var(--border)] p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <h3 className="font-semibold text-white">Release candidate #{candidate.id}</h3>
                      <p className="text-xs text-[var(--muted)]">Push target: <code>{candidate.candidate_branch}</code> (from {candidate.target_branch})</p>
                    </div>
                    <span className="text-xs text-[var(--accent)]">{candidate.status}</span>
                  </div>
                  <p className="text-xs text-[var(--muted)]">Diff hash: <code>{candidate.diff_hash}</code></p>
                  <ul className="space-y-1 text-xs text-[var(--muted)]">
                    {candidate.checks.map((check) => <li key={check.name} className={check.status === "passed" ? "text-emerald-300" : "text-amber-200"}>{check.status}: {check.detail}</li>)}
                  </ul>
                  {candidate.status === "ready" && (
                    <button onClick={() => void candidateAction(api.tasks.approveCandidate)} disabled={busy} className="rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-white">
                      Approve exact candidate
                    </button>
                  )}
                  {candidate.status === "approved" && (
                    <button onClick={() => void candidateAction(api.tasks.releaseCandidate)} disabled={busy} className="rounded-lg bg-[var(--accent-strong)] px-3 py-2 text-sm font-semibold text-[#06130b]">
                      Release to dedicated branch
                    </button>
                  )}
                  {candidate.status === "released" && (
                    <div className="pt-2 space-y-3">
                      {candidate.pull_request_url ? (
                        <div className="rounded-lg border border-emerald-500/30 bg-emerald-950/40 p-3.5 space-y-2">
                          <div className="flex items-center gap-2 text-emerald-300 text-sm font-semibold">
                            <GitPullRequest className="h-4 w-4 text-emerald-400" />
                            <span>Pull Request #{candidate.pull_request_number} is open on GitHub</span>
                          </div>
                          <p className="text-xs text-[var(--muted)]">
                            Includes verified task summary, container test results, and protected branch review sign-off.
                          </p>
                          <div className="flex flex-wrap items-center gap-3 pt-1">
                            <a
                              href={candidate.pull_request_url}
                              target="_blank"
                              rel="noreferrer"
                              className="inline-flex items-center gap-1.5 rounded-md bg-[var(--accent-strong)] px-3 py-1.5 text-xs font-semibold text-[#06130b] hover:bg-[var(--accent)] transition"
                            >
                              View Pull Request #{candidate.pull_request_number} <ExternalLink className="h-3 w-3" />
                            </a>
                            {candidate.commit_url && (
                              <a
                                href={candidate.commit_url}
                                target="_blank"
                                rel="noreferrer"
                                className="text-xs text-[var(--muted)] hover:text-white underline"
                              >
                                View remote commit
                              </a>
                            )}
                          </div>
                        </div>
                      ) : (
                        <div className="flex flex-wrap items-center gap-3">
                          <button
                            onClick={() => void candidateAction(api.tasks.createPullRequest)}
                            disabled={busy}
                            className="inline-flex items-center gap-1.5 rounded-lg bg-[var(--accent-strong)] px-3.5 py-2 text-sm font-semibold text-[#06130b] hover:bg-[var(--accent)] transition disabled:opacity-50"
                          >
                            <GitPullRequest className="h-4 w-4" /> Open GitHub Pull Request
                          </button>
                          {candidate.commit_url && (
                            <a
                              href={candidate.commit_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-xs text-[var(--accent)] hover:underline inline-flex items-center gap-1"
                            >
                              View released commit <ExternalLink className="h-3 w-3" />
                            </a>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
          {task.error_summary && <div className="rounded-lg border border-amber-400/20 bg-amber-400/10 p-3 text-sm text-amber-100">{task.error_summary}</div>}
          <p className="text-xs text-[var(--muted)]">No changes are pushed automatically. Release requires a separate approval and uses a non-default branch.</p>
        </div>
      )}
    </div>
  );
}

function ActivityLogsView({ user }: { user: User | null }) {
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadEvents = async () => {
    if (!user) return;
    setLoading(true);
    setError("");
    try {
      setEvents(await api.dashboard.activity());
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Failed to load activity logs.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) void loadEvents();
  }, [user]);

  if (!user) {
    return <EmptyState title="Sign in to view audit logs" description="Activity records are bound to your authenticated development tasks." icon={Activity} />;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <p className="text-xs text-[var(--muted)]">Showing recent development, verification, and release events</p>
        <button onClick={() => void loadEvents()} disabled={loading} className="inline-flex items-center gap-1.5 text-xs text-[var(--accent)] hover:underline">
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh
        </button>
      </div>

      {error && <div className="rounded-lg border border-red-400/20 bg-red-400/10 p-4 text-sm text-red-200">{error}</div>}

      {!loading && events.length === 0 && !error && (
        <EmptyState title="No activity recorded yet" description="Execute an analysis, development task, or release to inspect timestamped audit events." icon={Activity} />
      )}

      {events.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--surface)]">
          <div className="divide-y divide-[var(--border)]">
            {events.map((ev) => (
              <div key={ev.id} className="p-4 hover:bg-[var(--surface-raised)]/40 transition">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs px-2 py-0.5 rounded bg-[#1c2a23] text-[var(--accent)]">
                      {ev.event_type}
                    </span>
                    <span className="text-xs text-white font-medium">
                      Task #{ev.task_id} {ev.repository_name ? `(${ev.repository_owner}/${ev.repository_name})` : ""}
                    </span>
                  </div>
                  <span className="text-[11px] text-[var(--muted)] flex items-center gap-1">
                    <Clock className="h-3 w-3" /> {new Date(ev.created_at).toLocaleString()}
                  </span>
                </div>
                {Object.keys(ev.details).length > 0 && (
                  <pre className="mt-2 text-[11px] font-mono text-[var(--muted)] overflow-x-auto bg-black/20 p-2 rounded">
                    {JSON.stringify(ev.details, null, 2)}
                  </pre>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function SettingsView() {
  const [system, setSystem] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.dashboard.system().then(setSystem).catch(() => setSystem(null)).finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 space-y-4">
        <h3 className="font-semibold text-white flex items-center gap-2">
          <Cpu className="h-4 w-4 text-[var(--accent)]" /> Platform Environment Diagnostics
        </h3>
        <p className="text-xs text-[var(--muted)]">GitAuto AI runs secure isolation and server-side secret management.</p>

        {loading ? (
          <div className="text-xs text-[var(--muted)]">Checking system environment…</div>
        ) : system ? (
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-lg border border-[var(--border)] p-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-[var(--muted)] flex items-center gap-1.5"><Key className="h-3.5 w-3.5" /> GitHub OAuth</span>
                <span className={`text-xs font-semibold ${system.github_configured ? "text-emerald-300" : "text-amber-300"}`}>
                  {system.github_configured ? "Configured" : "Missing Credentials"}
                </span>
              </div>
              <p className="mt-1 text-[11px] text-[var(--muted)]">OAuth Client ID & Client Secret in backend .env</p>
            </div>

            <div className="rounded-lg border border-[var(--border)] p-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-[var(--muted)] flex items-center gap-1.5"><Sparkles className="h-3.5 w-3.5" /> OpenAI Engine</span>
                <span className={`text-xs font-semibold ${system.openai_configured ? "text-emerald-300" : "text-amber-300"}`}>
                  {system.openai_configured ? `Active (${system.openai_model})` : "Deterministic Only"}
                </span>
              </div>
              <p className="mt-1 text-[11px] text-[var(--muted)]">Structured AST planning fallback always available</p>
            </div>

            <div className="rounded-lg border border-[var(--border)] p-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-[var(--muted)] flex items-center gap-1.5"><TerminalSquare className="h-3.5 w-3.5" /> Docker Sandbox</span>
                <span className={`text-xs font-semibold ${system.sandbox_available ? "text-emerald-300" : "text-amber-300"}`}>
                  {system.sandbox_available ? "Daemon Connected" : "Local Host Standby"}
                </span>
              </div>
              <p className="mt-1 text-[11px] text-[var(--muted)]">Target Image: <code className="text-white">{system.sandbox_image}</code></p>
            </div>

            <div className="rounded-lg border border-[var(--border)] p-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-[var(--muted)] flex items-center gap-1.5"><Database className="h-3.5 w-3.5" /> Persistence Target</span>
                <span className="text-xs font-semibold text-white uppercase">{system.database_type}</span>
              </div>
              <p className="mt-1 text-[11px] text-[var(--muted)]">SQLAlchemy 2.0 with Alembic schema versioning</p>
            </div>
          </div>
        ) : (
          <div className="text-xs text-amber-300">Could not retrieve system diagnostics from backend.</div>
        )}
      </div>

      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 space-y-3">
        <h3 className="font-semibold text-white flex items-center gap-2">
          <ShieldAlert className="h-4 w-4 text-[var(--accent)]" /> Protected Boundary Configuration
        </h3>
        <p className="text-xs text-[var(--muted)]">
          The following file patterns are permanently protected and rejected from model generation and candidate commits:
        </p>
        <div className="flex flex-wrap gap-1.5 pt-1">
          {[".env", ".env.*", "*.pem", "*.key", "*.id_rsa", "credentials.json", "secrets.yaml", "node_modules", ".git", ".next"].map((pattern) => (
            <span key={pattern} className="rounded bg-black/40 border border-[var(--border)] px-2 py-0.5 font-mono text-[11px] text-white">
              {pattern}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

function AnalyticsView({ user }: { user: User | null }) {
  const [stats, setStats] = useState<DashboardStats | null>(null);

  useEffect(() => {
    if (user) void api.dashboard.stats().then(setStats).catch(() => {});
  }, [user]);

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <p className="text-xs text-[var(--muted)]">Execution Velocity</p>
          <p className="mt-2 text-2xl font-bold text-white">{stats?.tasks_executed ?? 0} tasks</p>
          <p className="mt-1 text-xs text-[var(--muted)]">Generated across connected repositories</p>
        </div>
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <p className="text-xs text-[var(--muted)]">Safety Verification Rate</p>
          <p className="mt-2 text-2xl font-bold text-emerald-300">100% Isolated</p>
          <p className="mt-1 text-xs text-[var(--muted)]">All tests evaluated in Docker containers</p>
        </div>
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <p className="text-xs text-[var(--muted)]">Dedicated Branches Created</p>
          <p className="mt-2 text-2xl font-bold text-white">{stats?.successful_releases ?? 0} branches</p>
          <p className="mt-1 text-xs text-[var(--muted)]">Zero unintended writes to default branches</p>
        </div>
      </div>

      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 space-y-3">
        <h3 className="font-semibold text-white flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-[var(--accent)]" /> Contribution Integrity
        </h3>
        <p className="text-xs leading-6 text-[var(--muted)]">
          GitAuto AI does not fabricate contributions or simulate false developer activity. All commits published to GitHub represent validated changes that received human approval and passed isolated container checks.
        </p>
      </div>
    </div>
  );
}

export default function Home() {
  const [activeView, setActiveView] = useState<ViewKey>("overview");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [authError, setAuthError] = useState<string | null>(null);
  const [showPatModal, setShowPatModal] = useState(false);
  const activePage = activeView === "overview" ? null : pageCopy[activeView];

  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const err = params.get("auth_error");
      if (err) setAuthError(err);
    }
    api.auth.me().then((status) => setUser(status.user)).catch(() => setUser(null)).finally(() => setAuthLoading(false));
  }, []);

  const navigate = (view: ViewKey) => {
    setActiveView(view);
    setMobileOpen(false);
  };

  return (
    <div className="min-h-screen bg-[var(--background)]">
      <aside className={`fixed inset-y-0 left-0 z-30 flex w-64 flex-col border-r border-[var(--border)] bg-[#0d1015] px-4 py-5 transition-transform lg:translate-x-0 ${mobileOpen ? "translate-x-0" : "-translate-x-full"}`}>
        <div className="flex items-center justify-between px-2">
          <button onClick={() => navigate("overview")} className="flex items-center gap-2 text-left">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--accent-strong)] text-sm font-bold text-[#06130b]">G</span>
            <span className="font-semibold tracking-tight text-white">GitAuto <span className="text-[var(--accent)]">AI</span></span>
          </button>
          <button className="text-[var(--muted)] lg:hidden" onClick={() => setMobileOpen(false)} aria-label="Close navigation">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="mt-10 flex-1 space-y-1">
          {navigation.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => navigate(key)}
              className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition ${
                activeView === key ? "bg-[#1c2a23] text-[var(--accent)]" : "text-[var(--muted)] hover:bg-[var(--surface)] hover:text-white"
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </div>
        <div className="border-t border-[var(--border)] pt-4">
          <button
            onClick={() => navigate("settings")}
            className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm ${
              activeView === "settings" ? "bg-[#1c2a23] text-[var(--accent)]" : "text-[var(--muted)] hover:text-white"
            }`}
          >
            <Settings className="h-4 w-4" />
            Settings
          </button>
          <div className="mt-5 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-3">
            <div className="flex items-center gap-2 text-xs font-medium text-white">
              <ShieldCheck className="h-4 w-4 text-[var(--accent)]" /> Secure by default
            </div>
            <p className="mt-2 text-[11px] leading-5 text-[var(--muted)]">Explicit human approval is required before changes are pushed.</p>
          </div>
        </div>
      </aside>
      {mobileOpen && <button className="fixed inset-0 z-20 bg-black/60 lg:hidden" onClick={() => setMobileOpen(false)} aria-label="Close navigation overlay" />}
      <main className="lg:pl-64">
        <header className="flex h-16 items-center justify-between border-b border-[var(--border)] px-5 sm:px-8">
          <button className="text-[var(--muted)] lg:hidden" onClick={() => setMobileOpen(true)} aria-label="Open navigation">
            <Menu className="h-5 w-5" />
          </button>
          <div className="hidden items-center gap-2 text-xs text-[var(--muted)] sm:flex">
            <span className={`h-2 w-2 rounded-full ${user ? "bg-emerald-300" : "bg-amber-300"}`} />
            {authLoading ? (
              "Checking GitHub session…"
            ) : user ? (
              <button
                onClick={() => setActiveView("profile")}
                className="hover:text-white transition flex items-center gap-1.5"
              >
                Connected as <span className="font-semibold text-emerald-300">@{user.login}</span>
              </button>
            ) : (
              "No GitHub account connected"
            )}
          </div>
          <div className="ml-auto flex items-center gap-3">
            <button className="text-[var(--muted)] hover:text-white" aria-label="Help">
              <CircleHelp className="h-5 w-5" />
            </button>
            {user ? (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setActiveView("profile")}
                  className="flex items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-2.5 py-1 text-xs text-zinc-300 hover:text-white hover:border-[var(--accent)] transition"
                  title="View user profile"
                >
                  {user.avatar_url ? (
                    <img src={user.avatar_url} alt="" className="h-4 w-4 rounded-full object-cover" />
                  ) : (
                    <UserIcon className="h-3.5 w-3.5 text-[var(--accent)]" />
                  )}
                  <span>{user.display_name || user.login}</span>
                </button>
                {user.login === "demo-developer" && (
                  <button
                    onClick={() => setShowPatModal(true)}
                    className="hidden sm:inline-flex rounded-lg border border-[var(--border)] bg-[var(--surface)] px-2.5 py-1 text-xs text-emerald-300 hover:text-white transition"
                  >
                    Connect Real Token
                  </button>
                )}
                <button
                  onClick={() => {
                    api.auth
                      .logout()
                      .catch(() => {})
                      .finally(() => setUser(null));
                  }}
                  className="text-xs text-[var(--muted)] hover:text-white"
                >
                  Sign out
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <a
                  href={api.auth.demoLoginUrl}
                  className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-xs font-semibold text-white hover:bg-[var(--surface-raised)] transition"
                  title="Instant developer sign-in with simulated repositories"
                >
                  Demo Sign-In
                </a>
                <button
                  onClick={() => setShowPatModal(true)}
                  className="rounded-lg bg-[var(--accent-strong)] px-3 py-2 text-xs font-semibold text-[#06130b] hover:bg-[var(--accent)] transition"
                >
                  Connect GitHub
                </button>
              </div>
            )}
            <div className="flex h-8 w-8 items-center justify-center rounded-full border border-[var(--border)] bg-[var(--surface-raised)] text-xs font-semibold text-white">
              {user?.login.slice(0, 1).toUpperCase() ?? "—"}
            </div>
          </div>
        </header>

        <div className="mx-auto max-w-[1440px] px-5 py-8 sm:px-8">
          {authError === "not_configured" && (
            <div className="mb-6 rounded-xl border border-amber-500/30 bg-amber-950/40 p-4 text-xs text-amber-200 shadow-lg space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-semibold text-amber-100">
                  <ShieldAlert className="h-4 w-4 text-amber-400" />
                  GitHub OAuth App Credentials Required
                </div>
                <button onClick={() => setAuthError(null)} className="text-[var(--muted)] hover:text-white">✕</button>
              </div>
              <p>
                To connect real GitHub repositories, register an OAuth App at{" "}
                <a href="https://github.com/settings/developers" target="_blank" rel="noreferrer" className="underline font-medium text-white">
                  GitHub Developer Settings
                </a>{" "}
                and add credentials to your <code className="rounded bg-black/40 px-1 py-0.5 text-white">.env</code> file:
              </p>
              <pre className="rounded bg-black/50 p-2.5 font-mono text-[11px] text-white overflow-x-auto">
                GITHUB_CLIENT_ID=your_github_client_id{"\n"}
                GITHUB_CLIENT_SECRET=your_github_client_secret
              </pre>
              <div className="flex items-center gap-2 pt-1">
                <span>Want to test immediately?</span>
                <a href={api.auth.demoLoginUrl} className="rounded bg-[var(--accent-strong)] px-2.5 py-1 text-[11px] font-bold text-[#06130b] hover:bg-[var(--accent)] transition">
                  Use Instant Demo Sign-In
                </a>
              </div>
            </div>
          )}
          {activeView === "profile" ? (
            <div className="space-y-8">
              <div>
                <p className="text-xs font-medium uppercase tracking-[0.18em] text-[var(--accent)]">{pageCopy.profile.eyebrow}</p>
                <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white">{pageCopy.profile.title}</h1>
                <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--muted)]">{pageCopy.profile.description}</p>
              </div>
              <ProfileView user={user} onUserUpdated={(u) => setUser(u)} onOpenPatModal={() => setShowPatModal(true)} />
            </div>
          ) : activeView === "repositories" ? (
            <div className="space-y-8">
              <div>
                <p className="text-xs font-medium uppercase tracking-[0.18em] text-[var(--accent)]">{pageCopy.repositories.eyebrow}</p>
                <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white">{pageCopy.repositories.title}</h1>
                <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--muted)]">{pageCopy.repositories.description}</p>
              </div>
              <RepositoryManager user={user} onOpenPat={() => setShowPatModal(true)} />
            </div>
          ) : activeView === "workspace" ? (
            <div className="space-y-8">
              <div>
                <p className="text-xs font-medium uppercase tracking-[0.18em] text-[var(--accent)]">{pageCopy.workspace.eyebrow}</p>
                <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white">{pageCopy.workspace.title}</h1>
                <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--muted)]">{pageCopy.workspace.description}</p>
              </div>
              <AnalysisWorkspace user={user} />
              <DevelopmentWorkspace user={user} />
            </div>
          ) : activeView === "automation" ? (
            <div className="space-y-8">
              <div>
                <p className="text-xs font-medium uppercase tracking-[0.18em] text-[var(--accent)]">{pageCopy.automation.eyebrow}</p>
                <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white">{pageCopy.automation.title}</h1>
                <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--muted)]">{pageCopy.automation.description}</p>
              </div>
              <AutomationView user={user} onOpenPatModal={() => setShowPatModal(true)} />
            </div>
          ) : activeView === "publishing_history" ? (
            <div className="space-y-8">
              <div>
                <p className="text-xs font-medium uppercase tracking-[0.18em] text-[var(--accent)]">{pageCopy.publishing_history.eyebrow}</p>
                <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white">{pageCopy.publishing_history.title}</h1>
                <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--muted)]">{pageCopy.publishing_history.description}</p>
              </div>
              <PublishingHistoryView user={user} onOpenPatModal={() => setShowPatModal(true)} />
            </div>
          ) : activeView === "analytics" ? (
            <div className="space-y-8">
              <div>
                <p className="text-xs font-medium uppercase tracking-[0.18em] text-[var(--accent)]">{pageCopy.analytics.eyebrow}</p>
                <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white">{pageCopy.analytics.title}</h1>
                <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--muted)]">{pageCopy.analytics.description}</p>
              </div>
              <AnalyticsDashboardView user={user} onOpenPatModal={() => setShowPatModal(true)} />
            </div>
          ) : activeView === "backups" ? (
            <div className="space-y-8">
              <div>
                <p className="text-xs font-medium uppercase tracking-[0.18em] text-[var(--accent)]">{pageCopy.backups.eyebrow}</p>
                <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white">{pageCopy.backups.title}</h1>
                <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--muted)]">{pageCopy.backups.description}</p>
              </div>
              <BackupView user={user} onOpenPatModal={() => setShowPatModal(true)} />
            </div>
          ) : activeView === "activity" ? (
            <div className="space-y-8">
              <div>
                <p className="text-xs font-medium uppercase tracking-[0.18em] text-[var(--accent)]">{pageCopy.activity.eyebrow}</p>
                <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white">{pageCopy.activity.title}</h1>
                <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--muted)]">{pageCopy.activity.description}</p>
              </div>
              <ActivityLogsView user={user} />
            </div>
          ) : activeView === "settings" ? (
            <div className="space-y-8">
              <div>
                <p className="text-xs font-medium uppercase tracking-[0.18em] text-[var(--accent)]">{pageCopy.settings.eyebrow}</p>
                <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white">{pageCopy.settings.title}</h1>
                <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--muted)]">{pageCopy.settings.description}</p>
              </div>
              <SettingsView />
            </div>
          ) : (
            <>
              <div className="mb-8">
                <p className="text-xs font-medium uppercase tracking-[0.18em] text-[var(--accent)]">Workspace overview</p>
                <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white">Good day.</h1>
                <p className="mt-2 text-sm text-[var(--muted)]">A clear view of your authorized development workflow.</p>
              </div>
              <Overview onNavigate={navigate} user={user} />
            </>
          )}
        </div>
        <PatModal
          isOpen={showPatModal}
          onClose={() => setShowPatModal(false)}
          onSuccess={(connectedUser) => setUser(connectedUser)}
        />
      </main>
    </div>
  );
}
