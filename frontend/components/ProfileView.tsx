"use client";

import { useEffect, useRef, useState } from "react";
import {
  AlertTriangle,
  Bell,
  Calendar,
  Camera,
  CheckCircle2,
  Clock,
  ExternalLink,
  FolderGit2,
  GitBranch,
  GitCommit,
  Globe,
  HardDrive,
  Lock,
  Mail,
  RefreshCw,
  Save,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Trash2,
  Unlink,
  User as UserIcon,
  Users,
  X,
} from "lucide-react";
import {
  api,
  type NotificationPreferences,
  type ProfileSummaryDashboard,
  type User,
  type UserProfile,
} from "../lib/api";

type Props = {
  user: User | null;
  onUserUpdated: (user: User) => void;
  onOpenPatModal: () => void;
};

const TIMEZONES = [
  "UTC",
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "Europe/London",
  "Europe/Paris",
  "Europe/Berlin",
  "Asia/Dubai",
  "Asia/Kolkata",
  "Asia/Singapore",
  "Asia/Tokyo",
  "Australia/Sydney",
];

export function ProfileView({ user, onUserUpdated, onOpenPatModal }: Props) {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [dashboard, setDashboard] = useState<ProfileSummaryDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Editable settings fields
  const [customDisplayName, setCustomDisplayName] = useState("");
  const [selectedTimezone, setSelectedTimezone] = useState("UTC");
  const [notifications, setNotifications] = useState<NotificationPreferences>({
    email_on_backup: true,
    email_on_failure: true,
    email_on_pr: true,
    browser_notifications: true,
  });

  // Disconnect modal
  const [showDisconnectModal, setShowDisconnectModal] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const loadProfile = async () => {
    if (!user) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [profData, dashData] = await Promise.all([
        api.profile.get(),
        api.profile.dashboard().catch(() => null),
      ]);
      setProfile(profData);
      setDashboard(dashData);
      setCustomDisplayName(profData.custom_display_name || "");
      setSelectedTimezone(profData.timezone || "UTC");
      setNotifications(profData.notification_preferences);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load profile data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadProfile();
  }, [user]);

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const updated = await api.profile.update({
        custom_display_name: customDisplayName.trim() || null,
        timezone: selectedTimezone,
        notification_preferences: notifications,
      });
      setProfile(updated);
      onUserUpdated({
        id: updated.id,
        github_id: updated.github_id,
        login: updated.github_login,
        name: updated.github_name,
        email: updated.github_email,
        custom_display_name: updated.custom_display_name,
        display_name: updated.display_name,
        avatar_url: updated.avatar_url,
      });
      setSuccessMsg("Profile settings updated successfully!");
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update profile settings.");
    } finally {
      setSaving(false);
    }
  };

  const handleAvatarFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 2 * 1024 * 1024) {
      setError("Image file exceeds the 2 MB limit.");
      return;
    }

    setUploadingAvatar(true);
    setError(null);
    try {
      const updated = await api.profile.uploadAvatar(file);
      setProfile(updated);
      onUserUpdated({
        id: updated.id,
        github_id: updated.github_id,
        login: updated.github_login,
        name: updated.github_name,
        email: updated.github_email,
        custom_display_name: updated.custom_display_name,
        display_name: updated.display_name,
        avatar_url: updated.avatar_url,
      });
      setSuccessMsg("Profile picture uploaded successfully!");
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload avatar.");
    } finally {
      setUploadingAvatar(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleRemoveAvatar = async () => {
    if (!confirm("Revert profile picture back to your GitHub avatar?")) return;
    setUploadingAvatar(true);
    setError(null);
    try {
      const updated = await api.profile.removeAvatar();
      setProfile(updated);
      onUserUpdated({
        id: updated.id,
        github_id: updated.github_id,
        login: updated.github_login,
        name: updated.github_name,
        email: updated.github_email,
        custom_display_name: updated.custom_display_name,
        display_name: updated.display_name,
        avatar_url: updated.avatar_url,
      });
      setSuccessMsg("Profile picture reverted to GitHub avatar.");
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reset avatar.");
    } finally {
      setUploadingAvatar(false);
    }
  };

  const handleDisconnectGitHub = async () => {
    setDisconnecting(true);
    setError(null);
    try {
      await api.profile.disconnectGitHub();
      setShowDisconnectModal(false);
      setSuccessMsg("GitHub account has been disconnected. You can reconnect anytime.");
      void loadProfile();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to disconnect GitHub account.");
    } finally {
      setDisconnecting(false);
    }
  };

  if (!user) {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-12 text-center">
        <UserIcon className="mx-auto h-12 w-12 text-[var(--accent)]" />
        <h3 className="mt-4 text-lg font-semibold text-white">Sign In Required</h3>
        <p className="mt-2 text-sm text-[var(--muted)] max-w-md mx-auto">
          Connect your GitHub account or use Instant Demo to view and manage your developer profile.
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

  if (loading) {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-12 text-center text-sm text-[var(--muted)]">
        <RefreshCw className="mx-auto h-6 w-6 animate-spin text-[var(--accent)] mb-2" />
        Loading profile and GitHub account information...
      </div>
    );
  }

  const effectiveAvatar =
    profile?.avatar_url || profile?.github_avatar_url || "https://avatars.githubusercontent.com/u/0?v=4";
  const hasCustomAvatar = Boolean(
    profile?.avatar_url && profile.avatar_url.startsWith("/api/v1/profile/avatar-file/")
  );

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

      {/* Header Profile Hero Card */}
      <div className="rounded-2xl border border-[var(--border)] bg-gradient-to-br from-[#121915] via-[var(--surface)] to-[#0e1411] p-6 sm:p-8">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-col gap-5 sm:flex-row sm:items-center">
            {/* Avatar with upload overlay */}
            <div className="relative group shrink-0">
              <img
                src={effectiveAvatar}
                alt={profile?.display_name || "Profile avatar"}
                className="h-24 w-24 rounded-2xl border-2 border-[var(--border)] object-cover shadow-lg bg-black/40"
              />
              <button
                disabled={uploadingAvatar}
                onClick={() => fileInputRef.current?.click()}
                className="absolute inset-0 flex flex-col items-center justify-center rounded-2xl bg-black/70 opacity-0 group-hover:opacity-100 transition duration-200 text-white text-xs gap-1 font-medium backdrop-blur-xs cursor-pointer"
                title="Upload custom profile picture"
              >
                <Camera className="h-5 w-5 text-emerald-300" />
                <span>Change</span>
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/png,image/jpeg,image/webp,image/gif"
                onChange={handleAvatarFileChange}
                className="hidden"
              />
            </div>

            {/* Profile Info */}
            <div className="space-y-1.5">
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-2xl font-bold tracking-tight text-white">
                  {profile?.display_name || profile?.github_login}
                </h1>
                {profile?.custom_display_name && (
                  <span className="rounded bg-black/40 border border-[var(--border)] px-2 py-0.5 text-[11px] font-mono text-zinc-400">
                    Custom Name
                  </span>
                )}
                {profile?.github_connected ? (
                  <span className="inline-flex items-center gap-1 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-300">
                    <CheckCircle2 className="h-3 w-3" />
                    GitHub Verified
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 rounded-full border border-amber-400/30 bg-amber-400/10 px-2.5 py-0.5 text-[11px] font-semibold text-amber-300">
                    <AlertTriangle className="h-3 w-3" />
                    GitHub Disconnected
                  </span>
                )}
              </div>

              <div className="flex flex-wrap items-center gap-4 text-xs text-[var(--muted)]">
                <a
                  href={profile?.github_profile_url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1 text-emerald-300 hover:text-emerald-200 transition font-mono"
                >
                  @{profile?.github_login}
                  <ExternalLink className="h-3 w-3" />
                </a>
                {profile?.github_email && (
                  <span className="flex items-center gap-1 text-zinc-300">
                    <Mail className="h-3 w-3 text-zinc-500" />
                    {profile.github_email}
                  </span>
                )}
                {profile?.created_at && (
                  <span className="flex items-center gap-1 text-zinc-400">
                    <Calendar className="h-3 w-3 text-zinc-500" />
                    Joined {new Date(profile.created_at).toLocaleDateString()}
                  </span>
                )}
              </div>

              <div className="flex flex-wrap items-center gap-2 pt-1 text-[11px]">
                {hasCustomAvatar && (
                  <button
                    onClick={handleRemoveAvatar}
                    disabled={uploadingAvatar}
                    className="inline-flex items-center gap-1 text-zinc-400 hover:text-red-400 transition"
                  >
                    <Trash2 className="h-3 w-3" /> Revert to GitHub picture
                  </button>
                )}
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 shrink-0">
            <button
              onClick={() => void loadProfile()}
              className="flex items-center gap-1.5 rounded-lg border border-[var(--border)] bg-black/40 px-3 py-2 text-xs text-zinc-300 hover:text-white transition"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
              Sync Data
            </button>
            {!profile?.github_connected && (
              <button
                onClick={onOpenPatModal}
                className="flex items-center gap-1.5 rounded-lg bg-[var(--accent-strong)] px-4 py-2 text-xs font-semibold text-[#06130b] hover:bg-[var(--accent)] transition"
              >
                Reconnect GitHub
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Grid: GitHub Account Details & Profile Settings */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* 1. Connected GitHub Account Details */}
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 space-y-5">
          <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
            <div className="flex items-center gap-2">
              <FolderGit2 className="h-5 w-5 text-[var(--accent)]" />
              <h2 className="text-base font-semibold text-white">GitHub Account Profile</h2>
            </div>
            <span
              className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                profile?.github_connected
                  ? "bg-emerald-400/10 text-emerald-300 border border-emerald-400/20"
                  : "bg-amber-400/10 text-amber-300 border border-amber-400/20"
              }`}
            >
              {profile?.github_connected ? "Connected" : "Disconnected"}
            </span>
          </div>

          {profile?.github_profile && (
            <div className="space-y-4">
              <div className="flex items-center gap-3 p-3 rounded-lg bg-black/30 border border-[var(--border)]">
                <img
                  src={profile.github_profile.avatar_url || effectiveAvatar}
                  alt={profile.github_profile.login || "GitHub avatar"}
                  className="h-12 w-12 rounded-xl border border-[var(--border)] object-cover"
                />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-semibold text-white truncate">
                      {profile.github_profile.name || profile.github_profile.login}
                    </p>
                    <span className="text-xs text-[var(--muted)] font-mono">
                      @{profile.github_profile.login}
                    </span>
                  </div>
                  {profile.github_profile.html_url && (
                    <a
                      href={profile.github_profile.html_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 text-xs text-emerald-400 hover:underline mt-0.5"
                    >
                      View GitHub Public Profile <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                </div>
              </div>

              {/* GitHub Statistics Row */}
              <div className="grid grid-cols-3 gap-3">
                <div className="rounded-lg border border-[var(--border)] bg-black/20 p-3 text-center">
                  <p className="text-[11px] text-[var(--muted)]">Public Repos</p>
                  <p className="mt-1 text-lg font-bold text-white">
                    {profile.github_profile.public_repos ?? "—"}
                  </p>
                </div>
                <div className="rounded-lg border border-[var(--border)] bg-black/20 p-3 text-center">
                  <p className="text-[11px] text-[var(--muted)] flex items-center justify-center gap-1">
                    <Users className="h-3 w-3" /> Followers
                  </p>
                  <p className="mt-1 text-lg font-bold text-white">
                    {profile.github_profile.followers ?? "—"}
                  </p>
                </div>
                <div className="rounded-lg border border-[var(--border)] bg-black/20 p-3 text-center">
                  <p className="text-[11px] text-[var(--muted)]">Following</p>
                  <p className="mt-1 text-lg font-bold text-white">
                    {profile.github_profile.following ?? "—"}
                  </p>
                </div>
              </div>

              <div className="rounded-lg border border-[var(--border)] bg-black/30 p-3 text-xs text-[var(--muted)] space-y-1">
                <span className="font-semibold text-zinc-300 flex items-center gap-1">
                  <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" /> Authenticated via OAuth / PAT
                </span>
                <p className="text-[11px] text-zinc-400 leading-relaxed">
                  Repository access tokens are encrypted with AES-256 and never exposed in API payloads or browser storage.
                </p>
              </div>

              {/* Disconnect Action */}
              <div className="pt-2 flex items-center justify-between">
                <p className="text-[11px] text-zinc-500">Need to switch accounts or revoke access?</p>
                {profile.github_connected ? (
                  <button
                    onClick={() => setShowDisconnectModal(true)}
                    className="flex items-center gap-1 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-1.5 text-xs font-medium text-red-300 hover:bg-red-500/20 transition"
                  >
                    <Unlink className="h-3.5 w-3.5" /> Disconnect GitHub
                  </button>
                ) : (
                  <button
                    onClick={onOpenPatModal}
                    className="flex items-center gap-1 rounded-lg bg-[var(--accent-strong)] px-3 py-1.5 text-xs font-semibold text-[#06130b] hover:bg-[var(--accent)] transition"
                  >
                    Connect GitHub
                  </button>
                )}
              </div>
            </div>
          )}
        </div>

        {/* 2. Profile Settings & Preferences */}
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 space-y-5">
          <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
            <div className="flex items-center gap-2">
              <Globe className="h-5 w-5 text-[var(--accent)]" />
              <h2 className="text-base font-semibold text-white">Profile & Preferences</h2>
            </div>
            <span className="text-xs text-[var(--muted)]">GitAuto AI Settings</span>
          </div>

          <form onSubmit={handleSaveSettings} className="space-y-4">
            {/* Custom Display Name */}
            <div>
              <label className="block text-xs font-medium text-zinc-300">
                GitAuto AI Display Name
              </label>
              <input
                type="text"
                placeholder={profile?.github_name || profile?.github_login || "e.g. Lead AI Architect"}
                value={customDisplayName}
                onChange={(e) => setCustomDisplayName(e.target.value)}
                className="mt-1 w-full rounded-lg border border-[var(--border)] bg-black/40 px-3 py-2 text-sm text-white placeholder-zinc-500 focus:border-[var(--accent)] focus:outline-none"
              />
              <p className="mt-1 text-[11px] text-zinc-400">
                Custom name shown across dashboards, release candidate reviews, and commit proposals.
              </p>
            </div>

            {/* Timezone */}
            <div>
              <label className="block text-xs font-medium text-zinc-300">
                Preferred Timezone
              </label>
              <select
                value={selectedTimezone}
                onChange={(e) => setSelectedTimezone(e.target.value)}
                className="mt-1 w-full rounded-lg border border-[var(--border)] bg-[#171f28] px-3 py-2 text-sm text-white focus:border-[var(--accent)] focus:outline-none"
              >
                {TIMEZONES.map((tz) => (
                  <option key={tz} value={tz}>
                    {tz}
                  </option>
                ))}
              </select>
              <p className="mt-1 text-[11px] text-zinc-400">
                Aligns daily backup schedules and recurring AI automated jobs to your local clock.
              </p>
            </div>

            {/* Notifications */}
            <div className="space-y-2 pt-2 border-t border-[var(--border)]">
              <label className="block text-xs font-semibold text-zinc-200 flex items-center gap-1.5">
                <Bell className="h-3.5 w-3.5 text-[var(--accent)]" />
                Notification Preferences
              </label>

              <div className="space-y-2">
                <label className="flex items-center gap-2.5 text-xs text-zinc-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={notifications.email_on_backup}
                    onChange={(e) =>
                      setNotifications((prev) => ({ ...prev, email_on_backup: e.target.checked }))
                    }
                    className="h-4 w-4 rounded border-[var(--border)] bg-black/40 text-[var(--accent)] focus:ring-0"
                  />
                  <span>Email notifications upon successful daily backups</span>
                </label>

                <label className="flex items-center gap-2.5 text-xs text-zinc-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={notifications.email_on_failure}
                    onChange={(e) =>
                      setNotifications((prev) => ({ ...prev, email_on_failure: e.target.checked }))
                    }
                    className="h-4 w-4 rounded border-[var(--border)] bg-black/40 text-[var(--accent)] focus:ring-0"
                  />
                  <span>Alert on backup failures or secret detection warnings</span>
                </label>

                <label className="flex items-center gap-2.5 text-xs text-zinc-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={notifications.email_on_pr}
                    onChange={(e) =>
                      setNotifications((prev) => ({ ...prev, email_on_pr: e.target.checked }))
                    }
                    className="h-4 w-4 rounded border-[var(--border)] bg-black/40 text-[var(--accent)] focus:ring-0"
                  />
                  <span>Notify when AI creates candidate Pull Requests ready for review</span>
                </label>

                <label className="flex items-center gap-2.5 text-xs text-zinc-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={notifications.browser_notifications}
                    onChange={(e) =>
                      setNotifications((prev) => ({
                        ...prev,
                        browser_notifications: e.target.checked,
                      }))
                    }
                    className="h-4 w-4 rounded border-[var(--border)] bg-black/40 text-[var(--accent)] focus:ring-0"
                  />
                  <span>In-browser desktop push notifications</span>
                </label>
              </div>
            </div>

            <div className="pt-4 flex justify-end">
              <button
                type="submit"
                disabled={saving}
                className="flex items-center gap-2 rounded-lg bg-[var(--accent-strong)] px-5 py-2 text-xs font-semibold text-[#06130b] hover:bg-[var(--accent)] transition disabled:opacity-50"
              >
                <Save className="h-3.5 w-3.5" />
                {saving ? "Saving Changes..." : "Save Preferences"}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* 3. Profile Dashboard Summary Card */}
      {dashboard && (
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
            <div>
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <Shield className="h-5 w-5 text-[var(--accent)]" />
                Profile Operational Dashboard
              </h2>
              <p className="text-xs text-[var(--muted)] mt-0.5">
                Unified overview of your connected systems, daily backups, and AI developer tasks.
              </p>
            </div>
            <span className="text-xs text-zinc-400 font-mono">Timezone: {dashboard.timezone}</span>
          </div>

          {/* Metric cards */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-xl border border-[var(--border)] bg-black/30 p-4">
              <span className="text-xs text-[var(--muted)]">Connected Repos</span>
              <p className="mt-1 text-2xl font-bold text-white">
                {dashboard.connected_repositories_count}
              </p>
              <p className="text-[10px] text-zinc-500 mt-0.5">Active GitHub connections</p>
            </div>

            <div className="rounded-xl border border-[var(--border)] bg-black/30 p-4">
              <span className="text-xs text-[var(--muted)]">Local Projects</span>
              <p className="mt-1 text-2xl font-bold text-white">
                {dashboard.local_projects_count}
              </p>
              <p className="text-[10px] text-zinc-500 mt-0.5">System A Daily Backup targets</p>
            </div>

            <div className="rounded-xl border border-[var(--border)] bg-black/30 p-4">
              <span className="text-xs text-[var(--muted)]">Automation Pipeline</span>
              <p className="mt-1 text-base font-bold text-emerald-300 flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                {dashboard.automation_active ? "Active" : "Standby"}
              </p>
              <p className="text-[10px] text-zinc-500 mt-0.5">Scheduled Windows runner</p>
            </div>

            <div className="rounded-xl border border-[var(--border)] bg-black/30 p-4">
              <span className="text-xs text-[var(--muted)]">Last Backup Status</span>
              <p className="mt-1 text-base font-bold text-white capitalize">
                {dashboard.last_backup_status || "Not run yet"}
              </p>
              <p className="text-[10px] text-zinc-500 mt-0.5">
                {dashboard.last_backup_at
                  ? new Date(dashboard.last_backup_at).toLocaleString()
                  : "Awaiting first run"}
              </p>
            </div>
          </div>

          {/* Two-column Activity Lists */}
          <div className="grid gap-6 md:grid-cols-2 pt-2">
            {/* Recent Backups */}
            <div className="space-y-3">
              <h3 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider flex items-center gap-1.5">
                <HardDrive className="h-3.5 w-3.5 text-emerald-400" />
                Recent Backup Activity
              </h3>
              {dashboard.recent_backups.length === 0 ? (
                <div className="rounded-lg border border-dashed border-[var(--border)] p-6 text-center text-xs text-zinc-500 italic">
                  No backup records recorded yet.
                </div>
              ) : (
                <div className="divide-y divide-[var(--border)] rounded-lg border border-[var(--border)] bg-black/20 p-2">
                  {dashboard.recent_backups.map((b) => (
                    <div key={b.id} className="py-2.5 px-2 flex items-center justify-between text-xs">
                      <div>
                        <div className="flex items-center gap-2">
                          <span
                            className={`rounded px-1.5 py-0.5 text-[9px] font-bold uppercase ${
                              b.status === "success"
                                ? "bg-emerald-400/20 text-emerald-300"
                                : b.status === "dry_run"
                                ? "bg-sky-400/20 text-sky-300"
                                : "bg-zinc-700 text-zinc-300"
                            }`}
                          >
                            {b.status}
                          </span>
                          <span className="font-medium text-white">{b.project_name}</span>
                        </div>
                        {b.commit_sha && (
                          <span className="font-mono text-[10px] text-zinc-400 flex items-center gap-1 mt-0.5">
                            <GitCommit className="h-2.5 w-2.5" />
                            {b.commit_sha.substring(0, 7)}
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] text-zinc-400">
                        {new Date(b.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Recent Tasks */}
            <div className="space-y-3">
              <h3 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider flex items-center gap-1.5">
                <GitBranch className="h-3.5 w-3.5 text-[var(--accent)]" />
                Recent AI Development Activity
              </h3>
              {dashboard.recent_tasks.length === 0 ? (
                <div className="rounded-lg border border-dashed border-[var(--border)] p-6 text-center text-xs text-zinc-500 italic">
                  No AI tasks executed yet. Start one in the AI Workspace.
                </div>
              ) : (
                <div className="divide-y divide-[var(--border)] rounded-lg border border-[var(--border)] bg-black/20 p-2">
                  {dashboard.recent_tasks.map((t) => (
                    <div key={t.id} className="py-2.5 px-2 flex items-center justify-between text-xs">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="rounded bg-black/50 border border-[var(--border)] px-1.5 py-0.5 text-[9px] font-mono text-zinc-300 uppercase">
                            {t.task_type}
                          </span>
                          <span className="font-medium text-white">{t.repository_name}</span>
                        </div>
                        <span className="text-[10px] text-zinc-400 capitalize mt-0.5 block">
                          Status: {t.status.replace("_", " ")}
                        </span>
                      </div>
                      <span className="text-[10px] text-zinc-400">
                        {new Date(t.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Disconnect Confirmation Modal */}
      {showDisconnectModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-red-500/30 bg-[#14181f] p-6 shadow-2xl">
            <div className="flex items-center gap-3 text-red-400">
              <ShieldAlert className="h-6 w-6 shrink-0" />
              <h3 className="text-base font-semibold text-white">Disconnect GitHub Account?</h3>
            </div>
            <p className="mt-3 text-xs leading-5 text-zinc-300">
              Disconnecting will revoke active GitHub token access from GitAuto AI. Automated backups and PR publishing will be paused until you re-authorize.
            </p>
            <p className="mt-2 text-xs text-zinc-500">
              Your local projects and historical backup records will not be deleted.
            </p>

            <div className="mt-6 flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={() => setShowDisconnectModal(false)}
                className="rounded-lg border border-[var(--border)] px-4 py-2 text-xs font-medium text-zinc-300 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={disconnecting}
                onClick={handleDisconnectGitHub}
                className="rounded-lg bg-red-600 px-4 py-2 text-xs font-semibold text-white hover:bg-red-500 transition disabled:opacity-50"
              >
                {disconnecting ? "Disconnecting..." : "Confirm Disconnect"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

