"use client";

import { useEffect, useState } from "react";
import {
  AlertTriangle,
  Calendar,
  CheckCircle2,
  Clock,
  Copy,
  ExternalLink,
  Eye,
  FileCode,
  FolderGit2,
  GitBranch,
  GitCommit,
  HardDrive,
  Lock,
  Play,
  Plus,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  Terminal,
  Trash2,
  X,
} from "lucide-react";
import {
  api,
  type BackupRecord,
  type BackupScanPreview,
  type LocalProject,
  type Repository,
  type User,
} from "../lib/api";

type Props = {
  user: User | null;
  onOpenPatModal: () => void;
};

export function BackupView({ user, onOpenPatModal }: Props) {
  const [projects, setProjects] = useState<LocalProject[]>([]);
  const [repos, setRepos] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Add project modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [addName, setAddName] = useState("");
  const [addPath, setAddPath] = useState("");
  const [addRepoId, setAddRepoId] = useState<number | "">("");
  const [addBranch, setAddBranch] = useState("backup/daily");
  const [addSchedule, setAddSchedule] = useState("02:00");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Preview modal
  const [previewData, setPreviewData] = useState<BackupScanPreview | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewProject, setPreviewProject] = useState<LocalProject | null>(null);

  // History / log modal
  const [historyProject, setHistoryProject] = useState<LocalProject | null>(null);
  const [records, setRecords] = useState<BackupRecord[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [activeLogRecord, setActiveLogRecord] = useState<BackupRecord | null>(null);

  // Active running
  const [runningId, setRunningId] = useState<number | null>(null);
  const [copiedCmd, setCopiedCmd] = useState(false);

  const loadData = async () => {
    if (!user) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [projList, repoList] = await Promise.all([
        api.backups.projects().catch(() => []),
        api.repositories.connections().catch(() => []),
      ]);
      setProjects(projList);
      setRepos(repoList);
      if (repoList.length > 0 && addRepoId === "") {
        setAddRepoId(repoList[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load backup data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadData();
  }, [user]);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!addRepoId) {
      setError("Please select a connected GitHub repository.");
      return;
    }
    setIsSubmitting(true);
    setError(null);
    try {
      await api.backups.createProject({
        name: addName.trim(),
        local_path: addPath.trim(),
        repository_connection_id: Number(addRepoId),
        target_branch: addBranch.trim(),
        backup_schedule: addSchedule.trim(),
      });
      setShowAddModal(false);
      setAddName("");
      setAddPath("");
      setSuccessMsg("Local project connected successfully!");
      void loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to connect project.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteProject = async (project: LocalProject) => {
    if (!confirm(`Are you sure you want to remove project "${project.name}" from backups?`)) {
      return;
    }
    try {
      await api.backups.deleteProject(project.id);
      setProjects((prev) => prev.filter((p) => p.id !== project.id));
      setSuccessMsg(`Project "${project.name}" removed.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete project.");
    }
  };

  const handleOpenPreview = async (project: LocalProject) => {
    setPreviewProject(project);
    setPreviewLoading(true);
    setPreviewData(null);
    try {
      const data = await api.backups.preview(project.id);
      setPreviewData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to scan project preview.");
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleRunBackup = async (project: LocalProject, dryRun: boolean) => {
    setRunningId(project.id);
    setError(null);
    setSuccessMsg(null);
    try {
      const record = await api.backups.run(project.id, { dry_run: dryRun });
      if (record.status === "success") {
        setSuccessMsg(
          `Backup successful! Pushed commit ${record.commit_sha?.substring(0, 7) ?? ""} to ${record.target_branch}. Remote SHA verified.`
        );
      } else if (record.status === "dry_run") {
        setSuccessMsg(
          `Dry-run simulation complete! ${record.files_backed_up.length} safe file(s) would be backed up. ${record.files_excluded.length} secret(s) protected.`
        );
      } else if (record.status === "skipped") {
        setSuccessMsg("No changes detected since last backup. Clean working tree.");
      } else {
        setError(`Backup failed: ${record.error_message ?? "Check logs for details."}`);
      }
      setActiveLogRecord(record);
      void loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Execution failed.");
    } finally {
      setRunningId(null);
    }
  };

  const handleOpenHistory = async (project: LocalProject) => {
    setHistoryProject(project);
    setHistoryLoading(true);
    setRecords([]);
    try {
      const data = await api.backups.records(project.id);
      setRecords(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch backup records.");
    } finally {
      setHistoryLoading(false);
    }
  };

  const copyTaskSchedulerCmd = () => {
    const cmd = "powershell -ExecutionPolicy Bypass -File scripts\\register-task-scheduler.ps1";
    navigator.clipboard.writeText(cmd);
    setCopiedCmd(true);
    setTimeout(() => setCopiedCmd(false), 2500);
  };

  if (!user) {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-12 text-center">
        <ShieldCheck className="mx-auto h-12 w-12 text-[var(--accent)]" />
        <h3 className="mt-4 text-lg font-semibold text-white">Sign In Required</h3>
        <p className="mt-2 text-sm text-[var(--muted)] max-w-md mx-auto">
          Connect your GitHub account or use Instant Demo to configure daily local project backups.
        </p>
        <button
          onClick={onOpenPatModal}
          className="mt-6 rounded-lg bg-[var(--accent-strong)] px-5 py-2.5 text-sm font-semibold text-[#06130b] hover:bg-[var(--accent)] transition"
        >
          Connect GitHub
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Notifications */}
      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-200 flex items-start justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0 text-red-400" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-white">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {successMsg && (
        <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-4 text-sm text-emerald-200 flex items-start justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
            <span>{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg(null)} className="text-emerald-400 hover:text-white">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Header & Actions */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <HardDrive className="h-5 w-5 text-[var(--accent)]" />
            Local Project Backups
          </h2>
          <p className="text-xs text-[var(--muted)] mt-1">
            Safely mirror Windows directories to dedicated GitHub branches with automatic secret exclusion.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => void loadData()}
            className="flex items-center gap-1.5 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-xs text-[var(--muted)] hover:text-white transition"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-1.5 rounded-lg bg-[var(--accent-strong)] px-4 py-2 text-xs font-semibold text-[#06130b] hover:bg-[var(--accent)] transition"
          >
            <Plus className="h-4 w-4" />
            Add Local Project
          </button>
        </div>
      </div>

      {/* Windows Task Scheduler Automation Banner */}
      <div className="rounded-xl border border-[var(--border)] bg-gradient-to-r from-[#0e1613] to-[var(--surface)] p-5">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="flex h-6 w-6 items-center justify-center rounded bg-emerald-400/10 text-emerald-300">
                <Terminal className="h-3.5 w-3.5" />
              </span>
              <h3 className="text-sm font-semibold text-white">Windows Automation & Task Scheduler</h3>
              <span className="rounded bg-emerald-400/20 px-2 py-0.5 text-[10px] font-bold text-emerald-300 uppercase">
                Active System A
              </span>
            </div>
            <p className="text-xs text-[var(--muted)] max-w-2xl leading-5">
              Run backups automatically every night on Windows. The setup script configures Windows Task Scheduler with retry logic, comprehensive logging, and secret redaction.
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <code className="hidden sm:inline-block rounded border border-[var(--border)] bg-black/40 px-3 py-1.5 font-mono text-[11px] text-emerald-300">
              powershell -ExecutionPolicy Bypass -File scripts\register-task-scheduler.ps1
            </code>
            <button
              onClick={copyTaskSchedulerCmd}
              className="flex items-center gap-1.5 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-xs font-medium text-white hover:bg-[var(--surface-hover)] transition"
            >
              <Copy className="h-3.5 w-3.5" />
              {copiedCmd ? "Copied Command!" : "Copy Setup Command"}
            </button>
          </div>
        </div>
      </div>

      {/* Projects List */}
      {loading ? (
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-12 text-center text-sm text-[var(--muted)]">
          <RefreshCw className="mx-auto h-6 w-6 animate-spin text-[var(--accent)] mb-2" />
          Loading local projects...
        </div>
      ) : projects.length === 0 ? (
        <div className="rounded-xl border border-dashed border-[var(--border)] bg-[var(--surface)] p-12 text-center">
          <FolderGit2 className="mx-auto h-12 w-12 text-[var(--muted)]" />
          <h3 className="mt-4 text-base font-semibold text-white">No Local Projects Configured</h3>
          <p className="mt-1 text-xs text-[var(--muted)] max-w-sm mx-auto">
            Connect your local directory to a GitHub repository to begin automated daily backups.
          </p>
          <button
            onClick={() => setShowAddModal(true)}
            className="mt-5 inline-flex items-center gap-2 rounded-lg bg-[var(--accent-strong)] px-4 py-2 text-xs font-semibold text-[#06130b] hover:bg-[var(--accent)] transition"
          >
            <Plus className="h-4 w-4" />
            Connect Your First Project
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {projects.map((proj) => {
            const isRunning = runningId === proj.id;
            return (
              <div
                key={proj.id}
                className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5 transition hover:border-[var(--border-hover)]"
              >
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div className="space-y-2">
                    <div className="flex items-center gap-3">
                      <h3 className="font-semibold text-white text-base">{proj.name}</h3>
                      {proj.last_backup_status === "success" && (
                        <span className="inline-flex items-center gap-1 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-2.5 py-0.5 text-[11px] font-medium text-emerald-300">
                          <CheckCircle2 className="h-3 w-3" />
                          Success
                        </span>
                      )}
                      {proj.last_backup_status === "dry_run" && (
                        <span className="inline-flex items-center gap-1 rounded-full border border-sky-400/30 bg-sky-400/10 px-2.5 py-0.5 text-[11px] font-medium text-sky-300">
                          <ShieldCheck className="h-3 w-3" />
                          Dry Run
                        </span>
                      )}
                      {proj.last_backup_status === "skipped" && (
                        <span className="inline-flex items-center gap-1 rounded-full border border-amber-400/30 bg-amber-400/10 px-2.5 py-0.5 text-[11px] font-medium text-amber-300">
                          <Clock className="h-3 w-3" />
                          Clean (No changes)
                        </span>
                      )}
                      {proj.last_backup_status === "failed" && (
                        <span className="inline-flex items-center gap-1 rounded-full border border-red-400/30 bg-red-400/10 px-2.5 py-0.5 text-[11px] font-medium text-red-300">
                          <ShieldAlert className="h-3 w-3" />
                          Failed
                        </span>
                      )}
                      {!proj.last_backup_status && (
                        <span className="inline-flex items-center gap-1 rounded-full border border-zinc-700 bg-zinc-800 px-2.5 py-0.5 text-[11px] font-medium text-zinc-400">
                          Not run yet
                        </span>
                      )}
                    </div>

                    <div className="flex flex-wrap items-center gap-4 text-xs text-[var(--muted)]">
                      <div className="flex items-center gap-1.5 font-mono">
                        <HardDrive className="h-3.5 w-3.5 text-zinc-400" />
                        <span className="text-zinc-300">{proj.local_path}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <FolderGit2 className="h-3.5 w-3.5 text-zinc-400" />
                        <span className="text-zinc-300">
                          {proj.repository_owner ? `${proj.repository_owner}/${proj.repository_name}` : "Repository"}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <GitBranch className="h-3.5 w-3.5 text-emerald-400" />
                        <span className="font-mono text-emerald-300">{proj.target_branch}</span>
                        <span className="text-[10px] text-zinc-500">(protected default branch isolated)</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Calendar className="h-3.5 w-3.5 text-zinc-400" />
                        <span>Daily at {proj.backup_schedule}</span>
                      </div>
                      {proj.last_backup_at && (
                        <div className="flex items-center gap-1.5 text-[11px] text-zinc-400">
                          <span>Last: {new Date(proj.last_backup_at).toLocaleString()}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Card Actions */}
                  <div className="flex flex-wrap items-center gap-2 shrink-0">
                    <button
                      onClick={() => void handleOpenPreview(proj)}
                      className="flex items-center gap-1.5 rounded-lg border border-[var(--border)] bg-black/30 px-3 py-1.5 text-xs text-zinc-300 hover:text-white hover:bg-black/50 transition"
                      title="Inspect modified files & secret exclusion preview"
                    >
                      <Eye className="h-3.5 w-3.5 text-[var(--accent)]" />
                      Preview Scan
                    </button>
                    <button
                      disabled={isRunning}
                      onClick={() => void handleRunBackup(proj, true)}
                      className="flex items-center gap-1.5 rounded-lg border border-sky-500/30 bg-sky-500/10 px-3 py-1.5 text-xs font-medium text-sky-200 hover:bg-sky-500/20 transition disabled:opacity-50"
                      title="Run a non-modifying dry-run simulation"
                    >
                      <ShieldCheck className="h-3.5 w-3.5" />
                      {isRunning ? "Simulating..." : "Dry Run"}
                    </button>
                    <button
                      disabled={isRunning}
                      onClick={() => void handleRunBackup(proj, false)}
                      className="flex items-center gap-1.5 rounded-lg bg-[var(--accent-strong)] px-3 py-1.5 text-xs font-semibold text-[#06130b] hover:bg-[var(--accent)] transition disabled:opacity-50"
                      title="Execute live backup, push to GitHub, and verify remote SHA"
                    >
                      <Play className="h-3.5 w-3.5 fill-current" />
                      {isRunning ? "Backing up..." : "Backup Now"}
                    </button>
                    <button
                      onClick={() => void handleOpenHistory(proj)}
                      className="flex items-center gap-1.5 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-2.5 py-1.5 text-xs text-[var(--muted)] hover:text-white transition"
                      title="View execution logs and history"
                    >
                      <Clock className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => void handleDeleteProject(proj)}
                      className="rounded-lg border border-[var(--border)] p-1.5 text-zinc-500 hover:text-red-400 hover:border-red-400/40 transition"
                      title="Remove local project"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Add Project Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-[var(--border)] bg-[#11161d] p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
              <h3 className="text-base font-semibold text-white flex items-center gap-2">
                <Plus className="h-4 w-4 text-[var(--accent)]" />
                Connect Local Project Directory
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-zinc-400 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleCreateProject} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-medium text-zinc-300">Project Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. GitAuto Production Workspace"
                  value={addName}
                  onChange={(e) => setAddName(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-[var(--border)] bg-black/40 px-3 py-2 text-sm text-white placeholder-zinc-500 focus:border-[var(--accent)] focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-300">
                  Local Windows Directory Path
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. D:\GitAuto-AI - Copy or C:\Projects\MyRepo"
                  value={addPath}
                  onChange={(e) => setAddPath(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-[var(--border)] bg-black/40 px-3 py-2 font-mono text-sm text-white placeholder-zinc-500 focus:border-[var(--accent)] focus:outline-none"
                />
                <p className="mt-1 text-[11px] text-zinc-400">
                  Must be a valid directory path on the local Windows machine.
                </p>
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-300">
                  Target GitHub Repository
                </label>
                {repos.length === 0 ? (
                  <div className="mt-1 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-200">
                    No repositories connected. Please connect a repository in the Repositories tab first.
                  </div>
                ) : (
                  <select
                    value={addRepoId}
                    onChange={(e) => setAddRepoId(Number(e.target.value))}
                    className="mt-1 w-full rounded-lg border border-[var(--border)] bg-[#171f28] px-3 py-2 text-sm text-white focus:border-[var(--accent)] focus:outline-none"
                  >
                    {repos.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.owner}/{r.name} ({r.default_branch})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-medium text-zinc-300">
                    Target Branch
                  </label>
                  <input
                    type="text"
                    required
                    value={addBranch}
                    onChange={(e) => setAddBranch(e.target.value)}
                    className="mt-1 w-full rounded-lg border border-[var(--border)] bg-black/40 px-3 py-2 font-mono text-sm text-white focus:border-[var(--accent)] focus:outline-none"
                  />
                  <p className="mt-1 text-[10px] text-emerald-400 flex items-center gap-1">
                    <ShieldCheck className="h-3 w-3 shrink-0" />
                    Dedicated backup branch (default branch protected)
                  </p>
                </div>

                <div>
                  <label className="block text-xs font-medium text-zinc-300">
                    Daily Schedule (24h)
                  </label>
                  <input
                    type="text"
                    required
                    value={addSchedule}
                    onChange={(e) => setAddSchedule(e.target.value)}
                    className="mt-1 w-full rounded-lg border border-[var(--border)] bg-black/40 px-3 py-2 text-sm text-white focus:border-[var(--accent)] focus:outline-none"
                    placeholder="02:00"
                  />
                  <p className="mt-1 text-[10px] text-zinc-400">Daily execution time (e.g. 02:00)</p>
                </div>
              </div>

              <div className="rounded-lg border border-[var(--border)] bg-black/30 p-3 text-[11px] text-zinc-400 space-y-1">
                <span className="font-semibold text-zinc-300 flex items-center gap-1">
                  <Lock className="h-3 w-3 text-[var(--accent)]" /> Secret Protection Policy Active:
                </span>
                <p>
                  Files matching <code className="text-zinc-200">.env*</code>, <code className="text-zinc-200">*.pem</code>, <code className="text-zinc-200">*.key</code>, <code className="text-zinc-200">id_rsa</code>, and credential files are permanently excluded and never pushed.
                </p>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-[var(--border)]">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="rounded-lg border border-[var(--border)] px-4 py-2 text-xs font-medium text-zinc-300 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || repos.length === 0}
                  className="rounded-lg bg-[var(--accent-strong)] px-5 py-2 text-xs font-semibold text-[#06130b] hover:bg-[var(--accent)] transition disabled:opacity-50"
                >
                  {isSubmitting ? "Connecting..." : "Connect Project"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Preview Scan Modal */}
      {previewProject && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className="w-full max-w-2xl rounded-2xl border border-[var(--border)] bg-[#11161d] p-6 shadow-2xl max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
              <div>
                <h3 className="text-base font-semibold text-white flex items-center gap-2">
                  <Eye className="h-4 w-4 text-[var(--accent)]" />
                  Pre-Backup Scan: {previewProject.name}
                </h3>
                <p className="text-xs text-[var(--muted)] font-mono mt-0.5">{previewProject.local_path}</p>
              </div>
              <button
                onClick={() => setPreviewProject(null)}
                className="text-zinc-400 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto py-4 space-y-4">
              {previewLoading ? (
                <div className="py-12 text-center text-sm text-[var(--muted)]">
                  <RefreshCw className="mx-auto h-6 w-6 animate-spin text-[var(--accent)] mb-2" />
                  Scanning local filesystem and verifying .gitignore...
                </div>
              ) : previewData ? (
                <>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3">
                      <span className="text-xs text-emerald-400 font-medium">Safe Files to Stage</span>
                      <p className="mt-1 text-2xl font-bold text-white">{previewData.total_safe_count}</p>
                      <p className="text-[11px] text-zinc-400">Validated against sensitivity heuristics</p>
                    </div>
                    <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-3">
                      <span className="text-xs text-red-400 font-medium">Excluded Sensitive Files</span>
                      <p className="mt-1 text-2xl font-bold text-white">{previewData.total_excluded_count}</p>
                      <p className="text-[11px] text-zinc-400">Protected secrets and credential tokens</p>
                    </div>
                  </div>

                  {/* Excluded Secrets Section */}
                  {previewData.excluded_secrets.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-xs font-semibold text-red-300 uppercase tracking-wider flex items-center gap-1.5">
                        <Lock className="h-3.5 w-3.5" />
                        Safely Excluded Secrets ({previewData.excluded_secrets.length})
                      </h4>
                      <div className="rounded-lg border border-red-500/30 bg-red-950/20 p-2 max-h-40 overflow-y-auto space-y-1.5">
                        {previewData.excluded_secrets.map((sec) => (
                          <div
                            key={sec.path}
                            className="flex items-center justify-between text-xs px-2 py-1 rounded bg-black/40 font-mono"
                          >
                            <span className="text-red-300">{sec.path}</span>
                            <span className="text-[10px] text-zinc-400">{sec.exclusion_reason}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Safe Files Section */}
                  <div className="space-y-2">
                    <h4 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider flex items-center gap-1.5">
                      <FileCode className="h-3.5 w-3.5 text-emerald-400" />
                      Safe Files ({previewData.safe_files.length})
                    </h4>
                    {previewData.safe_files.length === 0 ? (
                      <p className="text-xs text-zinc-500 italic p-3 text-center border border-dashed border-[var(--border)] rounded-lg">
                        Working directory is clean. No untracked or modified files detected.
                      </p>
                    ) : (
                      <div className="rounded-lg border border-[var(--border)] bg-black/30 p-2 max-h-48 overflow-y-auto space-y-1">
                        {previewData.safe_files.map((file) => (
                          <div
                            key={file.path}
                            className="flex items-center justify-between text-xs px-2 py-1 rounded hover:bg-white/5 font-mono"
                          >
                            <span className="text-zinc-200">{file.path}</span>
                            <div className="flex items-center gap-2 text-[10px]">
                              <span className="text-zinc-400">{(file.size / 1024).toFixed(1)} KB</span>
                              <span
                                className={`rounded px-1.5 py-0.5 text-[9px] uppercase font-bold ${
                                  file.status === "modified"
                                    ? "bg-amber-400/20 text-amber-300"
                                    : file.status === "added"
                                    ? "bg-emerald-400/20 text-emerald-300"
                                    : "bg-zinc-700 text-zinc-300"
                                }`}
                              >
                                {file.status}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </>
              ) : null}
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-[var(--border)]">
              <span className="text-xs text-[var(--muted)]">Target branch: {previewProject.target_branch}</span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPreviewProject(null)}
                  className="rounded-lg border border-[var(--border)] px-4 py-2 text-xs text-zinc-300 hover:text-white"
                >
                  Close
                </button>
                <button
                  onClick={() => {
                    const p = previewProject;
                    setPreviewProject(null);
                    void handleRunBackup(p, true);
                  }}
                  className="rounded-lg border border-sky-500/40 bg-sky-500/10 px-4 py-2 text-xs font-medium text-sky-200 hover:bg-sky-500/20"
                >
                  Run Dry-Run
                </button>
                <button
                  onClick={() => {
                    const p = previewProject;
                    setPreviewProject(null);
                    void handleRunBackup(p, false);
                  }}
                  className="rounded-lg bg-[var(--accent-strong)] px-4 py-2 text-xs font-semibold text-[#06130b] hover:bg-[var(--accent)]"
                >
                  Backup Now
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* History & Records Modal */}
      {historyProject && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className="w-full max-w-3xl rounded-2xl border border-[var(--border)] bg-[#11161d] p-6 shadow-2xl max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
              <div>
                <h3 className="text-base font-semibold text-white flex items-center gap-2">
                  <Clock className="h-4 w-4 text-[var(--accent)]" />
                  Backup History: {historyProject.name}
                </h3>
                <p className="text-xs text-[var(--muted)] mt-0.5">Audit log of all live pushes and dry-run simulations</p>
              </div>
              <button
                onClick={() => setHistoryProject(null)}
                className="text-zinc-400 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto py-4">
              {historyLoading ? (
                <div className="py-12 text-center text-sm text-[var(--muted)]">
                  <RefreshCw className="mx-auto h-6 w-6 animate-spin text-[var(--accent)] mb-2" />
                  Loading records...
                </div>
              ) : records.length === 0 ? (
                <div className="py-12 text-center text-xs text-[var(--muted)] italic">
                  No backup records found for this project.
                </div>
              ) : (
                <div className="divide-y divide-[var(--border)]">
                  {records.map((rec) => (
                    <div key={rec.id} className="py-3 flex flex-col gap-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {rec.status === "success" && (
                            <span className="rounded bg-emerald-400/20 text-emerald-300 px-2 py-0.5 text-[10px] font-bold uppercase">
                              Success
                            </span>
                          )}
                          {rec.status === "dry_run" && (
                            <span className="rounded bg-sky-400/20 text-sky-300 px-2 py-0.5 text-[10px] font-bold uppercase">
                              Dry Run
                            </span>
                          )}
                          {rec.status === "skipped" && (
                            <span className="rounded bg-amber-400/20 text-amber-300 px-2 py-0.5 text-[10px] font-bold uppercase">
                              Skipped
                            </span>
                          )}
                          {rec.status === "failed" && (
                            <span className="rounded bg-red-400/20 text-red-300 px-2 py-0.5 text-[10px] font-bold uppercase">
                              Failed
                            </span>
                          )}
                          <span className="text-xs text-white font-medium">{rec.commit_message}</span>
                        </div>
                        <span className="text-[11px] text-zinc-400">
                          {new Date(rec.created_at).toLocaleString()}
                        </span>
                      </div>

                      <div className="flex flex-wrap items-center gap-4 text-xs text-[var(--muted)]">
                        {rec.commit_sha && (
                          <div className="flex items-center gap-1 font-mono text-emerald-400">
                            <GitCommit className="h-3.5 w-3.5" />
                            <span>{rec.commit_sha.substring(0, 7)}</span>
                            {rec.commit_url && (
                              <a
                                href={rec.commit_url}
                                target="_blank"
                                rel="noreferrer"
                                className="text-zinc-400 hover:text-white"
                              >
                                <ExternalLink className="h-3 w-3" />
                              </a>
                            )}
                          </div>
                        )}
                        <span>{rec.files_backed_up.length} backed up</span>
                        <span className="text-red-400">{rec.files_excluded.length} secrets protected</span>
                        <button
                          onClick={() => setActiveLogRecord(rec)}
                          className="ml-auto text-[11px] text-[var(--accent)] hover:underline flex items-center gap-1"
                        >
                          <Terminal className="h-3 w-3" />
                          View Full Log
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="pt-4 border-t border-[var(--border)] flex justify-end">
              <button
                onClick={() => setHistoryProject(null)}
                className="rounded-lg border border-[var(--border)] px-4 py-2 text-xs text-zinc-300 hover:text-white"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Log Output Viewer Modal */}
      {activeLogRecord && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm">
          <div className="w-full max-w-2xl rounded-2xl border border-[var(--border)] bg-[#0d1117] p-6 shadow-2xl max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
              <div className="flex items-center gap-2">
                <Terminal className="h-4 w-4 text-[var(--accent)]" />
                <h3 className="text-sm font-semibold text-white">Execution Console Log</h3>
                <span className="rounded bg-black/40 px-2 py-0.5 font-mono text-[10px] text-zinc-400">
                  Record #{activeLogRecord.id}
                </span>
              </div>
              <button
                onClick={() => setActiveLogRecord(null)}
                className="text-zinc-400 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto py-4">
              <pre className="rounded-lg border border-[var(--border)] bg-black/60 p-4 font-mono text-xs text-emerald-300 leading-relaxed whitespace-pre-wrap overflow-x-auto">
                {activeLogRecord.log_output || "No log output recorded."}
              </pre>
            </div>

            <div className="pt-3 border-t border-[var(--border)] flex justify-end">
              <button
                onClick={() => setActiveLogRecord(null)}
                className="rounded-lg bg-[var(--accent-strong)] px-4 py-2 text-xs font-semibold text-[#06130b] hover:bg-[var(--accent)]"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

