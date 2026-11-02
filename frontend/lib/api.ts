export type User = {
  id: number;
  github_id: number;
  login: string;
  name: string | null;
  email: string | null;
  custom_display_name?: string | null;
  display_name?: string | null;
  avatar_url?: string | null;
};

export type Repository = {
  id: number;
  name: string;
  owner: string;
  description: string | null;
  default_branch: string;
  visibility: string;
  language: string | null;
  html_url: string;
  can_push: boolean;
  connected: boolean;
};

export type AnalysisFinding = {
  id: string;
  category: string;
  title: string;
  description: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  evidence: string;
  affected_paths: string[];
  recommended_action: string;
  confidence: number;
};

export type Analysis = {
  id: number;
  repository_id: number;
  commit_sha: string;
  status: "pending" | "completed" | "partial" | "failed";
  project_summary: string;
  detected_technologies: string[];
  file_inventory: { path: string; size: number; language: string }[];
  findings: AnalysisFinding[];
  recommendations: string[];
  development_plan: {
    id: string; title: string; description: string; priority: string;
    complexity: string; relevant_paths: string[]; reason: string;
    acceptance_criteria: string[]; test_strategy: string; risks: string[];
  }[];
  limitations: string[];
  model_identifier: string | null;
  token_usage: number | null;
  created_at: string;
  completed_at: string | null;
};

export type DevelopmentTask = {
  id: number;
  repository_id: number;
  base_commit_sha: string;
  task_type: string;
  instructions: string;
  status: string;
  plan: {
    summary: string;
    objective: string;
    files_to_create: string[];
    files_to_modify: string[];
    steps: string[];
    expected_behavior: string;
    acceptance_criteria: string[];
    testing_strategy: string;
    risks: string[];
  } | null;
  validation_results: { status: string; detail: string }[];
  test_results: { status: string; detail: string }[];
  token_usage: number | null;
  error_summary: string | null;
  changes: {
    id: number;
    file_path: string;
    operation: string;
    reason: string;
    proposed_content: string;
    validation_status: string;
    review_status: string;
  }[];
  created_at: string;
  completed_at: string | null;
};

export type ReadinessCheck = { name: string; status: "passed" | "failed" | "not_run"; detail: string };
export type ReleaseCandidate = {
  id: number;
  task_id: number;
  repository_id: number;
  base_commit_sha: string;
  target_branch: string;
  candidate_branch: string;
  approved_file_paths: string[];
  diff_hash: string;
  secret_scan_status: string;
  status: string;
  checks: ReadinessCheck[];
  approval_at: string | null;
  release_started_at: string | null;
  released_at: string | null;
  commit_sha: string | null;
  commit_url: string | null;
  pull_request_number: number | null;
  pull_request_url: string | null;
  error_summary: string | null;
  created_at: string;
};

export type TestRun = {
  id: number;
  task_id: number;
  base_commit_sha: string;
  candidate_hash: string;
  execution_profile: string;
  command_classification: string;
  status: string;
  exit_code: number | null;
  started_at: string | null;
  ended_at: string | null;
  duration_ms: number | null;
  timed_out: boolean;
  resource_violation: string | null;
  stdout: string;
  stderr: string;
  summary: string;
  error_details: string | null;
  created_at: string;
};

export type DashboardStats = {
  connected_repositories: number;
  tasks_executed: number;
  pending_reviews: number;
  successful_releases: number;
  active_analyses: number;
};

export type ActivityEvent = {
  id: number;
  task_id: number;
  event_type: string;
  details: Record<string, unknown>;
  created_at: string;
  repository_owner: string | null;
  repository_name: string | null;
};

export type SystemStatus = {
  app_name: string;
  app_env: string;
  github_configured: boolean;
  openai_configured: boolean;
  openai_model: string;
  sandbox_image: string;
  database_type: string;
  sandbox_available: boolean;
};

export type JobStatus = {
  job_id: string;
  state: string;
  ready: boolean;
  successful: boolean;
  failed: boolean;
  result: unknown;
  notice?: string;
  error?: string;
};

export type LocalProject = {
  id: number;
  user_id: number;
  repository_connection_id: number;
  repository_name: string | null;
  repository_owner: string | null;
  name: string;
  local_path: string;
  target_branch: string;
  backup_schedule: string;
  is_active: boolean;
  last_backup_at: string | null;
  last_backup_status: string | null;
  created_at: string;
  updated_at: string;
};

export type BackupRecord = {
  id: number;
  user_id: number;
  local_project_id: number;
  project_name: string | null;
  repository_connection_id: number;
  target_branch: string;
  commit_sha: string | null;
  commit_url: string | null;
  commit_message: string;
  files_backed_up: string[];
  files_excluded: string[];
  status: "success" | "failed" | "dry_run" | "skipped";
  log_output: string;
  error_message: string | null;
  is_dry_run: boolean;
  created_at: string;
};

export type ScannedFileDetail = {
  path: string;
  status: "modified" | "added" | "deleted" | "untracked";
  size: number;
  is_secret: boolean;
  exclusion_reason: string | null;
};

export type BackupScanPreview = {
  local_path: string;
  target_branch: string;
  safe_files: ScannedFileDetail[];
  excluded_secrets: ScannedFileDetail[];
  total_safe_count: number;
  total_excluded_count: number;
};

export type NotificationPreferences = {
  email_on_backup: boolean;
  email_on_failure: boolean;
  email_on_pr: boolean;
  browser_notifications: boolean;
};

export type GitHubProfileDetails = {
  connected: boolean;
  github_id: number | null;
  login: string | null;
  name: string | null;
  email: string | null;
  avatar_url: string | null;
  html_url: string | null;
  public_repos: number | null;
  followers: number | null;
  following: number | null;
  github_created_at: string | null;
};

export type UserProfile = {
  id: number;
  github_id: number;
  github_login: string;
  github_name: string | null;
  github_email: string | null;
  custom_display_name: string | null;
  display_name: string;
  avatar_url: string | null;
  github_avatar_url: string | null;
  github_profile_url: string;
  timezone: string;
  notification_preferences: NotificationPreferences;
  created_at: string;
  updated_at: string;
  github_connected: boolean;
  connected_repositories_count: number;
  local_projects_count: number;
  automation_active: boolean;
  github_profile: GitHubProfileDetails | null;
};

export type ProfileUpdateRequest = {
  custom_display_name?: string | null;
  timezone?: string | null;
  notification_preferences?: NotificationPreferences | null;
};

export type RecentBackupActivity = {
  id: number;
  project_name: string;
  status: string;
  commit_sha: string | null;
  commit_url: string | null;
  is_dry_run: boolean;
  created_at: string;
};

export type RecentTaskActivity = {
  id: number;
  repository_name: string;
  task_type: string;
  status: string;
  created_at: string;
};

export type ProfileSummaryDashboard = {
  user_id: number;
  display_name: string;
  github_login: string;
  github_connected: boolean;
  avatar_url: string | null;
  timezone: string;
  connected_repositories_count: number;
  local_projects_count: number;
  automation_active: boolean;
  active_backups_count: number;
  last_backup_at: string | null;
  last_backup_status: string | null;
  recent_backups: RecentBackupActivity[];
  recent_tasks: RecentTaskActivity[];
};

export type AutomationSetting = {
  id: number;
  user_id: number;
  repository_connection_id: number;
  repository_name?: string | null;
  repository_owner?: string | null;
  default_branch?: string | null;
  is_enabled: boolean;
  schedule_time: string;
  timezone?: string;
  auto_publish?: boolean;
  next_run_at?: string | null;
  max_retries?: number;
  focus_areas: string[];
  target_branch_prefix: string;
  auto_test: boolean;
  require_approval: boolean;
  last_run_at: string | null;
  last_run_status: string | null;
  created_at: string;
  updated_at: string;
};

export type AutomationRun = {
  id: number;
  user_id: number;
  repository_connection_id: number;
  repository_name?: string | null;
  analysis_id?: number | null;
  development_task_id?: number | null;
  release_candidate_id?: number | null;
  status: "pending_approval" | "approved" | "completed" | "failed";
  summary: string;
  findings_count: number;
  changes_count: number;
  files_created_count?: number;
  files_modified_count?: number;
  files_deleted_count?: number;
  lines_added?: number;
  lines_deleted?: number;
  security_result?: string;
  test_result?: string;
  commit_message?: string | null;
  tests_passed: boolean | null;
  target_branch?: string | null;
  commit_sha?: string | null;
  commit_url?: string | null;
  pull_request_number?: number | null;
  pull_request_url?: string | null;
  validation_completed_at?: string | null;
  publishing_started_at?: string | null;
  commit_created_at?: string | null;
  push_completed_at?: string | null;
  remote_sha_verified_at?: string | null;
  publishing_duration_ms?: number | null;
  speed_target_met?: boolean | null;
  log_output: string;
  error_message?: string | null;
  created_at: string;
  completed_at?: string | null;
};

export type AutomationSettingCreate = {
  repository_connection_id: number;
  is_enabled?: boolean;
  schedule_time?: string;
  timezone?: string;
  auto_publish?: boolean;
  focus_areas?: string[];
  target_branch_prefix?: string;
  auto_test?: boolean;
};

export type AutomationSettingUpdate = {
  is_enabled?: boolean;
  schedule_time?: string;
  timezone?: string;
  auto_publish?: boolean;
  focus_areas?: string[];
  target_branch_prefix?: string;
  auto_test?: boolean;
};

export type RunSummary = {
  id: number;
  repository_id: number;
  repository_name: string;
  status: string;
  commit_sha: string | null;
  commit_url: string | null;
  pull_request_number: number | null;
  pull_request_url: string | null;
  commit_message: string | null;
  lines_added: number;
  lines_deleted: number;
  files_created_count: number;
  files_modified_count: number;
  files_deleted_count: number;
  speed_target_met: boolean | null;
  publishing_duration_ms: number | null;
  created_at: string;
  completed_at: string | null;
};

export type DailyAnalytics = {
  date: string;
  runs_count: number;
  successful_runs: number;
  failed_runs: number;
  commits_count: number;
  prs_count: number;
  lines_added: number;
  lines_deleted: number;
  files_created_count: number;
  files_modified_count: number;
  files_deleted_count: number;
  speed_target_met_count: number;
  avg_publishing_duration_ms: number | null;
  runs: RunSummary[];
};

export type DayData = {
  date: string;
  day_name: string;
  runs: number;
  commits: number;
  prs: number;
  lines_added: number;
  lines_deleted: number;
};

export type WeeklyAnalytics = {
  start_date: string;
  end_date: string;
  total_runs: number;
  total_commits: number;
  total_prs: number;
  total_lines_added: number;
  total_lines_deleted: number;
  daily_breakdown: DayData[];
};

export type RepoStats = {
  repository_id: number;
  repository_name: string;
  runs: number;
  commits: number;
  prs: number;
  lines_added: number;
  lines_deleted: number;
};

export type MonthlyAnalytics = {
  year: number;
  month: number;
  total_runs: number;
  total_commits: number;
  total_prs: number;
  total_lines_added: number;
  total_lines_deleted: number;
  active_repositories_count: number;
  repository_breakdown: RepoStats[];
  daily_breakdown: DayData[];
};

export type LifetimeAnalytics = {
  total_automated_repositories: number;
  total_runs: number;
  total_successful_runs: number;
  total_failed_runs: number;
  total_commits: number;
  total_prs: number;
  total_lines_added: number;
  total_lines_deleted: number;
  total_lines_changed: number;
  success_rate_percent: number;
  speed_target_met_count: number;
  speed_compliance_percent: number;
  avg_publishing_duration_ms: number | null;
  first_run_date: string | null;
  latest_run_date: string | null;
  repository_breakdown: RepoStats[];
};

type AuthStatus = { authenticated: boolean; user: User | null };
type RepositoryPage = { items: Repository[]; page: number; per_page: number; has_next: boolean };

function getBaseUrl(): string {
  if (process.env.NEXT_PUBLIC_API_URL) return process.env.NEXT_PUBLIC_API_URL;
  if (typeof window !== "undefined") {
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }
  return "http://localhost:8000";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const baseUrl = getBaseUrl();
  let response: Response;
  try {
    response = await fetch(`${baseUrl}/api/v1${path}`, {
      ...init,
      credentials: "include",
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    // Windows IPv6 / IPv4 fallback: if localhost failed, try 127.0.0.1 (or vice versa)
    const alternateUrl = baseUrl.includes("localhost")
      ? baseUrl.replace("localhost", "127.0.0.1")
      : baseUrl.includes("127.0.0.1")
      ? baseUrl.replace("127.0.0.1", "localhost")
      : null;

    if (alternateUrl) {
      try {
        response = await fetch(`${alternateUrl}/api/v1${path}`, {
          ...init,
          credentials: "include",
          headers: { "Content-Type": "application/json", ...init?.headers },
        });
      } catch {
        throw new Error(
          `Unable to reach the GitAuto AI backend at ${baseUrl}. Please verify the backend is running.`
        );
      }
    } else {
      throw new Error(
        `Unable to reach the GitAuto AI backend at ${baseUrl}. Please verify the backend is running.`
      );
    }
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? "The API request failed.");
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  auth: {
    me: () => request<AuthStatus>("/auth/me"),
    logout: () => request<void>("/auth/logout", { method: "POST" }),
    loginWithPat: (token: string) =>
      request<AuthStatus>("/auth/pat", {
        method: "POST",
        body: JSON.stringify({ token }),
      }),
    get loginUrl() {
      return `${getBaseUrl()}/api/v1/auth/github`;
    },
    get demoLoginUrl() {
      return `${getBaseUrl()}/api/v1/auth/demo-login`;
    },
  },
  repositories: {
    list: (page = 1, search = "") =>
      request<RepositoryPage>(`/repositories?page=${page}&per_page=30&search=${encodeURIComponent(search)}`),
    connect: (repositoryId: number) =>
      request<Repository>("/repositories/connect", {
        method: "POST",
        body: JSON.stringify({ repository_id: repositoryId }),
      }),
    connections: () => request<Repository[]>("/repositories/connections"),
  },
  analyses: {
    start: (repositoryId: number) =>
      request<Analysis>(`/analyses/repositories/${repositoryId}/analyze`, { method: "POST" }),
    startAsync: (repositoryId: number) =>
      request<{ job_id: string; analysis_id: number; status: string }>(
        `/analyses/repositories/${repositoryId}/analyze/async`,
        { method: "POST" }
      ),
    latest: (repositoryId: number) =>
      request<Analysis>(`/analyses/repositories/${repositoryId}/analysis/latest`),
  },
  tasks: {
    list: () => request<DevelopmentTask[]>("/development-tasks"),
    get: (taskId: number) => request<DevelopmentTask>(`/development-tasks/${taskId}`),
    create: (repositoryId: number, taskType: string, instructions: string) =>
      request<DevelopmentTask>(`/development-tasks/repositories/${repositoryId}`, {
        method: "POST", body: JSON.stringify({ task_type: taskType, instructions }),
      }),
    plan: (taskId: number) => request<DevelopmentTask>(`/development-tasks/${taskId}/plan`, { method: "POST" }),
    approvePlan: (taskId: number) => request<DevelopmentTask>(`/development-tasks/${taskId}/plan/approve`, { method: "POST" }),
    generate: (taskId: number) => request<DevelopmentTask>(`/development-tasks/${taskId}/generate`, { method: "POST" }),
    generateAsync: (taskId: number) =>
      request<{ job_id: string; task_id: number; status: string }>(
        `/development-tasks/${taskId}/generate/async`,
        { method: "POST" }
      ),
    diff: (taskId: number) => request<{ task_id: string; base_commit_sha: string; diff: string }>(`/development-tasks/${taskId}/diff`),
    testProfiles: (taskId: number) => request<{ name: string; command_classification: string; available: boolean; reason: string }[]>(`/development-tasks/${taskId}/tests/profiles`),
    runTests: (taskId: number) => request<TestRun>(`/development-tasks/${taskId}/tests`, { method: "POST" }),
    runTestsAsync: (taskId: number) =>
      request<{ job_id: string; test_run_id: number; status: string }>(
        `/development-tasks/${taskId}/tests/async`,
        { method: "POST" }
      ),
    latestTest: (taskId: number) => request<TestRun>(`/development-tasks/${taskId}/tests/latest`),
    cancelTest: (runId: number) => request<TestRun>(`/test-runs/${runId}/cancel`, { method: "POST" }),
    createCandidate: (taskId: number) =>
      request<ReleaseCandidate>(`/release-candidates/tasks/${taskId}`, { method: "POST" }),
    candidate: (candidateId: number) => request<ReleaseCandidate>(`/release-candidates/${candidateId}`),
    approveCandidate: (candidateId: number) =>
      request<ReleaseCandidate>(`/release-candidates/${candidateId}/approve`, { method: "POST" }),
    releaseCandidate: (candidateId: number) =>
      request<ReleaseCandidate>(`/release-candidates/${candidateId}/release`, { method: "POST" }),
    createPullRequest: (candidateId: number) =>
      request<ReleaseCandidate>(`/release-candidates/${candidateId}/pull-request`, { method: "POST" }),
    cancel: (taskId: number) => request<DevelopmentTask>(`/development-tasks/${taskId}/cancel`, { method: "POST" }),
  },
  dashboard: {
    stats: () => request<DashboardStats>("/dashboard/stats"),
    activity: () => request<ActivityEvent[]>("/dashboard/activity"),
    system: () => request<SystemStatus>("/dashboard/system"),
  },
  jobs: {
    status: (jobId: string) => request<JobStatus>(`/jobs/${jobId}`),
    health: () => request<{ status: string; broker_configured: boolean; task_always_eager: boolean }>("/jobs/health"),
  },
  backups: {
    projects: () => request<LocalProject[]>("/backups/projects"),
    createProject: (data: {
      name: string;
      local_path: string;
      repository_connection_id: number;
      target_branch?: string;
      backup_schedule?: string;
    }) =>
      request<LocalProject>("/backups/projects", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    deleteProject: (projectId: number) =>
      request<void>(`/backups/projects/${projectId}`, { method: "DELETE" }),
    preview: (projectId: number) =>
      request<BackupScanPreview>(`/backups/projects/${projectId}/preview`),
    run: (projectId: number, options: { dry_run?: boolean; custom_message?: string } = {}) =>
      request<BackupRecord>(`/backups/projects/${projectId}/run`, {
        method: "POST",
        body: JSON.stringify(options),
      }),
    records: (projectId?: number) =>
      request<BackupRecord[]>(
        projectId ? `/backups/projects/${projectId}/records` : "/backups/records"
      ),
  },
  profile: {
    get: () => request<UserProfile>("/profile"),
    update: (data: ProfileUpdateRequest) =>
      request<UserProfile>("/profile", {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    uploadAvatar: async (file: File): Promise<UserProfile> => {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(`${getBaseUrl()}/api/v1/profile/avatar`, {
        method: "POST",
        credentials: "include",
        body: formData,
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? "Avatar upload failed.");
      }
      return res.json() as Promise<UserProfile>;
    },
    removeAvatar: () =>
      request<UserProfile>("/profile/avatar", { method: "DELETE" }),
    dashboard: () =>
      request<ProfileSummaryDashboard>("/profile/dashboard"),
    disconnectGitHub: () =>
      request<{ disconnected: boolean; message: string }>("/profile/github/disconnect", {
        method: "POST",
      }),
  },
  automation: {
    settings: () => request<AutomationSetting[]>("/automation/settings"),
    createSetting: (data: AutomationSettingCreate) =>
      request<AutomationSetting>("/automation/settings", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    updateSetting: (settingId: number, data: AutomationSettingUpdate) =>
      request<AutomationSetting>(`/automation/settings/${settingId}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    toggleSetting: (settingId: number) =>
      request<AutomationSetting>(`/automation/settings/${settingId}/toggle`, {
        method: "POST",
      }),
    runNow: (settingId: number, focusArea?: string) =>
      request<AutomationRun>(`/automation/settings/${settingId}/run`, {
        method: "POST",
        body: JSON.stringify({ focus_area: focusArea }),
      }),
    runs: (settingId?: number) =>
      request<AutomationRun[]>(
        settingId ? `/automation/settings/${settingId}/runs` : "/automation/runs"
      ),
    getRun: (runId: number) => request<AutomationRun>(`/automation/runs/${runId}`),
    approveAndPublish: (runId: number) =>
      request<AutomationRun>(`/automation/runs/${runId}/approve-publish`, {
        method: "POST",
      }),
  },
  analytics: {
    daily: (date?: string, timezone?: string) => {
      const params = new URLSearchParams();
      if (date) params.append("date", date);
      if (timezone) params.append("timezone", timezone);
      const q = params.toString();
      return request<DailyAnalytics>(`/analytics/daily${q ? `?${q}` : ""}`);
    },
    weekly: (referenceDate?: string, timezone?: string) => {
      const params = new URLSearchParams();
      if (referenceDate) params.append("reference_date", referenceDate);
      if (timezone) params.append("timezone", timezone);
      const q = params.toString();
      return request<WeeklyAnalytics>(`/analytics/weekly${q ? `?${q}` : ""}`);
    },
    monthly: (year?: number, month?: number, timezone?: string) => {
      const params = new URLSearchParams();
      if (year) params.append("year", year.toString());
      if (month) params.append("month", month.toString());
      if (timezone) params.append("timezone", timezone);
      const q = params.toString();
      return request<MonthlyAnalytics>(`/analytics/monthly${q ? `?${q}` : ""}`);
    },
    lifetime: () => request<LifetimeAnalytics>("/analytics/lifetime"),
  },
};
