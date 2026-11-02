"use client";

import { useEffect, useState } from "react";
import {
  BarChart3,
  Calendar,
  CheckCircle2,
  Clock,
  ExternalLink,
  FileCode,
  FolderGit2,
  GitCommit,
  GitPullRequest,
  RefreshCw,
  ShieldCheck,
  TrendingUp,
  Zap,
} from "lucide-react";
import {
  api,
  type DailyAnalytics,
  type LifetimeAnalytics,
  type MonthlyAnalytics,
  type User,
  type WeeklyAnalytics,
} from "../lib/api";

type Props = {
  user: User | null;
  onOpenPatModal: () => void;
};

export function AnalyticsDashboardView({ user, onOpenPatModal }: Props) {
  const [scope, setScope] = useState<"daily" | "weekly" | "monthly" | "lifetime">("daily");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter parameters
  const [selectedDate, setSelectedDate] = useState<string>(() => {
    const today = new Date();
    return today.toISOString().split("T")[0];
  });
  const [selectedYear, setSelectedYear] = useState<number>(() => new Date().getFullYear());
  const [selectedMonth, setSelectedMonth] = useState<number>(() => new Date().getMonth() + 1);

  // Data states
  const [dailyData, setDailyData] = useState<DailyAnalytics | null>(null);
  const [weeklyData, setWeeklyData] = useState<WeeklyAnalytics | null>(null);
  const [monthlyData, setMonthlyData] = useState<MonthlyAnalytics | null>(null);
  const [lifetimeData, setLifetimeData] = useState<LifetimeAnalytics | null>(null);

  const loadAnalytics = async () => {
    if (!user) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      if (scope === "daily") {
        const res = await api.analytics.daily(selectedDate);
        setDailyData(res);
      } else if (scope === "weekly") {
        const res = await api.analytics.weekly(selectedDate);
        setWeeklyData(res);
      } else if (scope === "monthly") {
        const res = await api.analytics.monthly(selectedYear, selectedMonth);
        setMonthlyData(res);
      } else if (scope === "lifetime") {
        const res = await api.analytics.lifetime();
        setLifetimeData(res);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load publishing analytics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
  }, [user, scope, selectedDate, selectedYear, selectedMonth]);

  if (!user) {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-8 text-center">
        <BarChart3 className="mx-auto h-10 w-10 text-[var(--accent)]" />
        <h3 className="mt-4 text-base font-semibold text-white">Authentication Required</h3>
        <p className="mt-2 text-xs text-[var(--muted)]">
          Sign in to view daily, weekly, monthly, and lifetime publishing statistics.
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
      {/* Top Banner */}
      <div className="rounded-2xl border border-[var(--border)] bg-gradient-to-br from-[var(--surface)] via-[#12161f] to-[#0d1017] p-6 shadow-xl">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="flex h-6 items-center rounded-full border border-sky-400/20 bg-sky-400/10 px-2.5 text-[11px] font-semibold text-sky-300">
                System B Telemetry
              </span>
              <span className="flex h-6 items-center rounded-full border border-emerald-400/20 bg-emerald-400/10 px-2.5 text-[11px] font-semibold text-emerald-300">
                Live GitHub Diff Ingestion
              </span>
            </div>
            <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <BarChart3 className="h-6 w-6 text-sky-400" /> Publishing Analytics & Performance
            </h2>
            <p className="text-xs text-[var(--muted)] max-w-2xl">
              Real-time audit metrics for lines added, lines deleted, verified commits, pull requests, and sub-60s SLA compliance
              across daily, weekly, monthly, and lifetime scopes.
            </p>
          </div>

          <button
            onClick={loadAnalytics}
            disabled={loading}
            className="flex items-center gap-1.5 rounded-lg border border-[var(--border)] bg-black/40 px-3 py-2 text-xs font-medium text-zinc-300 hover:border-zinc-500 hover:text-white transition disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-sky-400" : ""}`} />
            Refresh Metrics
          </button>
        </div>

        {/* Scope Selector Sub-Tabs */}
        <div className="mt-6 flex flex-wrap items-center justify-between gap-4 border-t border-[var(--border)] pt-4">
          <div className="flex items-center gap-2">
            {(["daily", "weekly", "monthly", "lifetime"] as const).map((s) => (
              <button
                key={s}
                onClick={() => setScope(s)}
                className={`rounded-lg px-3.5 py-1.5 text-xs font-semibold capitalize transition ${
                  scope === s
                    ? "bg-sky-500 text-black shadow-lg shadow-sky-500/20"
                    : "border border-[var(--border)] bg-black/30 text-zinc-400 hover:text-white"
                }`}
              >
                {s === "daily" ? "Daily (Calendar Day)" : s === "weekly" ? "Weekly (7 Days)" : s === "monthly" ? "Monthly" : "Lifetime (All Time)"}
              </button>
            ))}
          </div>

          {/* Scope Filters */}
          <div className="flex items-center gap-2">
            {scope === "daily" && (
              <div className="flex items-center gap-2">
                <input
                  type="date"
                  value={selectedDate}
                  onChange={(e) => setSelectedDate(e.target.value)}
                  className="rounded-lg border border-[var(--border)] bg-black/40 px-3 py-1.5 text-xs text-white focus:border-sky-500 focus:outline-none"
                />
                <button
                  onClick={() => setSelectedDate(new Date().toISOString().split("T")[0])}
                  className="rounded-lg border border-[var(--border)] px-2.5 py-1.5 text-[11px] text-zinc-300 hover:text-white"
                >
                  Today
                </button>
              </div>
            )}

            {scope === "weekly" && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-[var(--muted)]">Ending on:</span>
                <input
                  type="date"
                  value={selectedDate}
                  onChange={(e) => setSelectedDate(e.target.value)}
                  className="rounded-lg border border-[var(--border)] bg-black/40 px-3 py-1.5 text-xs text-white focus:border-sky-500 focus:outline-none"
                />
              </div>
            )}

            {scope === "monthly" && (
              <div className="flex items-center gap-2">
                <select
                  value={selectedMonth}
                  onChange={(e) => setSelectedMonth(Number(e.target.value))}
                  className="rounded-lg border border-[var(--border)] bg-black/40 px-3 py-1.5 text-xs text-white focus:border-sky-500 focus:outline-none"
                >
                  {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                    <option key={m} value={m}>
                      {new Date(2000, m - 1, 1).toLocaleString("default", { month: "long" })}
                    </option>
                  ))}
                </select>
                <select
                  value={selectedYear}
                  onChange={(e) => setSelectedYear(Number(e.target.value))}
                  className="rounded-lg border border-[var(--border)] bg-black/40 px-3 py-1.5 text-xs text-white focus:border-sky-500 focus:outline-none"
                >
                  {[2024, 2025, 2026, 2027].map((y) => (
                    <option key={y} value={y}>
                      {y}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-xs text-red-300">
          {error}
        </div>
      )}

      {/* Scope 1: DAILY STATS */}
      {scope === "daily" && dailyData && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-6">
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
              <span className="text-[11px] font-medium text-[var(--muted)]">Verified Commits</span>
              <p className="mt-1 text-2xl font-bold text-white">{dailyData.commits_count}</p>
              <span className="text-[10px] text-zinc-500">{dailyData.runs_count} automation runs</span>
            </div>
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
              <span className="text-[11px] font-medium text-sky-400">Pull Requests</span>
              <p className="mt-1 text-2xl font-bold text-sky-300">{dailyData.prs_count}</p>
              <span className="text-[10px] text-zinc-500">{dailyData.successful_runs} successful</span>
            </div>
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
              <span className="text-[11px] font-medium text-emerald-400">Lines Added</span>
              <p className="mt-1 text-2xl font-bold text-emerald-400">+{dailyData.lines_added}</p>
              <span className="text-[10px] text-emerald-500/70">From GitHub API diff</span>
            </div>
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
              <span className="text-[11px] font-medium text-rose-400">Lines Deleted</span>
              <p className="mt-1 text-2xl font-bold text-rose-400">-{dailyData.lines_deleted}</p>
              <span className="text-[10px] text-rose-500/70">From GitHub API diff</span>
            </div>
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
              <span className="text-[11px] font-medium text-[var(--muted)]">Files Touched</span>
              <p className="mt-1 text-2xl font-bold text-zinc-200">
                {dailyData.files_created_count + dailyData.files_modified_count + dailyData.files_deleted_count}
              </p>
              <span className="text-[10px] text-zinc-500">
                +{dailyData.files_created_count} / ~{dailyData.files_modified_count} / -{dailyData.files_deleted_count}
              </span>
            </div>
            <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4">
              <span className="text-[11px] font-medium text-amber-300">Sub-60s SLA Met</span>
              <p className="mt-1 text-2xl font-bold text-amber-200">
                {dailyData.speed_target_met_count}{" "}
                <span className="text-xs font-normal text-amber-400/70">
                  {dailyData.avg_publishing_duration_ms ? `(avg ${dailyData.avg_publishing_duration_ms}ms)` : ""}
                </span>
              </p>
              <span className="text-[10px] text-amber-300/60">Target: publish &lt;= 60s</span>
            </div>
          </div>

          {/* Daily Runs Detail Table */}
          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
            <h3 className="text-sm font-semibold text-white mb-3">
              Publications for {dailyData.date} ({dailyData.runs.length})
            </h3>
            {dailyData.runs.length === 0 ? (
              <p className="text-xs text-zinc-500 py-6 text-center">
                No automation runs executed on this calendar day.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-[var(--border)] text-zinc-400 text-[11px]">
                    <tr>
                      <th className="py-2.5 px-3">Repository</th>
                      <th className="py-2.5 px-3">Task Message</th>
                      <th className="py-2.5 px-3">Diff Changes</th>
                      <th className="py-2.5 px-3">Verified Commit</th>
                      <th className="py-2.5 px-3">Pull Request</th>
                      <th className="py-2.5 px-3">Speed SLA</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border)] text-zinc-300">
                    {dailyData.runs.map((r) => (
                      <tr key={r.id}>
                        <td className="py-2.5 px-3 font-semibold text-white">{r.repository_name}</td>
                        <td className="py-2.5 px-3 max-w-xs truncate text-zinc-400">
                          {r.commit_message || "Daily automated improvement"}
                        </td>
                        <td className="py-2.5 px-3 font-mono">
                          <span className="text-emerald-400">+{r.lines_added}</span>{" "}
                          <span className="text-rose-400">-{r.lines_deleted}</span>
                        </td>
                        <td className="py-2.5 px-3 font-mono text-[11px]">
                          {r.commit_sha ? (
                            <a
                              href={r.commit_url ?? `https://github.com/search?q=${r.commit_sha}`}
                              target="_blank"
                              rel="noreferrer"
                              className="text-emerald-400 hover:underline"
                            >
                              {r.commit_sha.slice(0, 7)}
                            </a>
                          ) : (
                            <span className="text-zinc-500">--</span>
                          )}
                        </td>
                        <td className="py-2.5 px-3">
                          {r.pull_request_number ? (
                            <a
                              href={r.pull_request_url ?? "#"}
                              target="_blank"
                              rel="noreferrer"
                              className="text-sky-400 hover:underline inline-flex items-center gap-1"
                            >
                              PR #{r.pull_request_number}
                              <ExternalLink className="h-2.5 w-2.5" />
                            </a>
                          ) : (
                            <span className="text-zinc-500">--</span>
                          )}
                        </td>
                        <td className="py-2.5 px-3">
                          {r.publishing_duration_ms ? (
                            <span
                              className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${
                                r.speed_target_met ? "bg-emerald-500/10 text-emerald-300" : "bg-amber-500/10 text-amber-300"
                              }`}
                            >
                              ⚡ {r.publishing_duration_ms}ms
                            </span>
                          ) : (
                            <span className="text-zinc-500">--</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Scope 2: WEEKLY STATS */}
      {scope === "weekly" && weeklyData && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
              <span className="text-[11px] font-medium text-[var(--muted)]">7-Day Total Commits</span>
              <p className="mt-1 text-2xl font-bold text-white">{weeklyData.total_commits}</p>
              <span className="text-[10px] text-zinc-500">{weeklyData.total_runs} runs</span>
            </div>
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
              <span className="text-[11px] font-medium text-sky-400">7-Day Pull Requests</span>
              <p className="mt-1 text-2xl font-bold text-sky-300">{weeklyData.total_prs}</p>
              <span className="text-[10px] text-sky-500/70">Published &amp; verified</span>
            </div>
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
              <span className="text-[11px] font-medium text-emerald-400">7-Day Lines Added</span>
              <p className="mt-1 text-2xl font-bold text-emerald-400">+{weeklyData.total_lines_added}</p>
              <span className="text-[10px] text-emerald-500/70">Across all repos</span>
            </div>
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
              <span className="text-[11px] font-medium text-rose-400">7-Day Lines Deleted</span>
              <p className="mt-1 text-2xl font-bold text-rose-400">-{weeklyData.total_lines_deleted}</p>
              <span className="text-[10px] text-rose-500/70">Refactored code</span>
            </div>
          </div>

          {/* 7-Day Day-by-Day Activity Chart / Breakdown */}
          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
            <h3 className="text-sm font-semibold text-white mb-4">
              Daily Velocity ({weeklyData.start_date} to {weeklyData.end_date})
            </h3>

            <div className="grid grid-cols-7 gap-2">
              {weeklyData.daily_breakdown.map((d) => {
                const maxVal = Math.max(...weeklyData.daily_breakdown.map((x) => x.lines_added + x.lines_deleted), 50);
                const barHeight = Math.min(100, Math.round(((d.lines_added + d.lines_deleted) / maxVal) * 100));

                return (
                  <div key={d.date} className="flex flex-col items-center gap-2 rounded-lg border border-[var(--border)] bg-black/30 p-3">
                    <span className="text-xs font-semibold text-white">{d.day_name}</span>
                    <span className="text-[10px] text-zinc-500">{d.date.slice(5)}</span>

                    <div className="h-28 w-full flex flex-col justify-end items-center py-1">
                      <div
                        style={{ height: `${Math.max(barHeight, 8)}%` }}
                        className="w-4 rounded-t bg-gradient-to-t from-emerald-500 to-sky-400"
                        title={`+${d.lines_added} / -${d.lines_deleted} lines`}
                      />
                    </div>

                    <div className="text-[11px] font-mono text-center">
                      <div className="text-emerald-400">+{d.lines_added}</div>
                      <div className="text-rose-400">-{d.lines_deleted}</div>
                    </div>
                    <span className="text-[10px] text-sky-300 font-semibold">{d.prs} PRs</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Scope 3: MONTHLY STATS */}
      {scope === "monthly" && monthlyData && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
              <span className="text-[11px] font-medium text-[var(--muted)]">Monthly Total Commits</span>
              <p className="mt-1 text-2xl font-bold text-white">{monthlyData.total_commits}</p>
              <span className="text-[10px] text-zinc-500">{monthlyData.total_runs} runs</span>
            </div>
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
              <span className="text-[11px] font-medium text-sky-400">Monthly Pull Requests</span>
              <p className="mt-1 text-2xl font-bold text-sky-300">{monthlyData.total_prs}</p>
              <span className="text-[10px] text-sky-500/70">{monthlyData.active_repositories_count} active repos</span>
            </div>
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
              <span className="text-[11px] font-medium text-emerald-400">Monthly Lines Added</span>
              <p className="mt-1 text-2xl font-bold text-emerald-400">+{monthlyData.total_lines_added}</p>
            </div>
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
              <span className="text-[11px] font-medium text-rose-400">Monthly Lines Deleted</span>
              <p className="mt-1 text-2xl font-bold text-rose-400">-{monthlyData.total_lines_deleted}</p>
            </div>
          </div>

          {/* Repository Breakdown */}
          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
            <h3 className="text-sm font-semibold text-white mb-3">
              Per-Repository Breakdown ({monthlyData.year}-{String(monthlyData.month).padStart(2, "0")})
            </h3>
            {monthlyData.repository_breakdown.length === 0 ? (
              <p className="text-xs text-zinc-500 py-4 text-center">No publications recorded for this month.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-[var(--border)] text-zinc-400 text-[11px]">
                    <tr>
                      <th className="py-2.5 px-3">Repository</th>
                      <th className="py-2.5 px-3">Runs</th>
                      <th className="py-2.5 px-3">Commits</th>
                      <th className="py-2.5 px-3">Pull Requests</th>
                      <th className="py-2.5 px-3">Lines Added</th>
                      <th className="py-2.5 px-3">Lines Deleted</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border)] text-zinc-300">
                    {monthlyData.repository_breakdown.map((r) => (
                      <tr key={r.repository_id}>
                        <td className="py-2.5 px-3 font-semibold text-white">{r.repository_name}</td>
                        <td className="py-2.5 px-3">{r.runs}</td>
                        <td className="py-2.5 px-3 font-semibold text-emerald-400">{r.commits}</td>
                        <td className="py-2.5 px-3 font-semibold text-sky-400">{r.prs}</td>
                        <td className="py-2.5 px-3 font-mono text-emerald-400">+{r.lines_added}</td>
                        <td className="py-2.5 px-3 font-mono text-rose-400">-{r.lines_deleted}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Scope 4: LIFETIME STATS */}
      {scope === "lifetime" && lifetimeData && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-6">
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
              <span className="text-[11px] font-medium text-[var(--muted)]">Automated Repos</span>
              <p className="mt-1 text-2xl font-bold text-white">{lifetimeData.total_automated_repositories}</p>
              <span className="text-[10px] text-zinc-500">Connected repositories</span>
            </div>
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
              <span className="text-[11px] font-medium text-[var(--muted)]">All-Time Commits</span>
              <p className="mt-1 text-2xl font-bold text-white">{lifetimeData.total_commits}</p>
              <span className="text-[10px] text-zinc-500">{lifetimeData.total_runs} total runs</span>
            </div>
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
              <span className="text-[11px] font-medium text-sky-400">Pull Requests</span>
              <p className="mt-1 text-2xl font-bold text-sky-300">{lifetimeData.total_prs}</p>
              <span className="text-[10px] text-sky-500/70">{lifetimeData.success_rate_percent}% success rate</span>
            </div>
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
              <span className="text-[11px] font-medium text-emerald-400">Lines Added</span>
              <p className="mt-1 text-2xl font-bold text-emerald-400">+{lifetimeData.total_lines_added}</p>
            </div>
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
              <span className="text-[11px] font-medium text-rose-400">Lines Deleted</span>
              <p className="mt-1 text-2xl font-bold text-rose-400">-{lifetimeData.total_lines_deleted}</p>
            </div>
            <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4">
              <span className="text-[11px] font-medium text-amber-300">Sub-60s SLA</span>
              <p className="mt-1 text-2xl font-bold text-amber-200">{lifetimeData.speed_compliance_percent}%</p>
              <span className="text-[10px] text-amber-300/70">
                {lifetimeData.avg_publishing_duration_ms ? `avg ${lifetimeData.avg_publishing_duration_ms}ms` : "Compliant"}
              </span>
            </div>
          </div>

          {/* Lifetime Repositories Breakdown */}
          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
            <h3 className="text-sm font-semibold text-white mb-3">
              Lifetime Contribution by Repository ({lifetimeData.repository_breakdown.length})
            </h3>
            {lifetimeData.repository_breakdown.length === 0 ? (
              <p className="text-xs text-zinc-500 py-4 text-center">No lifetime publishing records found.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-[var(--border)] text-zinc-400 text-[11px]">
                    <tr>
                      <th className="py-2.5 px-3">Repository</th>
                      <th className="py-2.5 px-3">Total Runs</th>
                      <th className="py-2.5 px-3">Verified Commits</th>
                      <th className="py-2.5 px-3">Pull Requests</th>
                      <th className="py-2.5 px-3">Lines Added</th>
                      <th className="py-2.5 px-3">Lines Deleted</th>
                      <th className="py-2.5 px-3">Net Diff</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border)] text-zinc-300">
                    {lifetimeData.repository_breakdown.map((r) => (
                      <tr key={r.repository_id}>
                        <td className="py-2.5 px-3 font-semibold text-white">{r.repository_name}</td>
                        <td className="py-2.5 px-3">{r.runs}</td>
                        <td className="py-2.5 px-3 font-semibold text-emerald-400">{r.commits}</td>
                        <td className="py-2.5 px-3 font-semibold text-sky-400">{r.prs}</td>
                        <td className="py-2.5 px-3 font-mono text-emerald-400">+{r.lines_added}</td>
                        <td className="py-2.5 px-3 font-mono text-rose-400">-{r.lines_deleted}</td>
                        <td className="py-2.5 px-3 font-mono font-semibold">
                          {r.lines_added - r.lines_deleted >= 0 ? (
                            <span className="text-emerald-400">+{r.lines_added - r.lines_deleted}</span>
                          ) : (
                            <span className="text-rose-400">{r.lines_added - r.lines_deleted}</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

