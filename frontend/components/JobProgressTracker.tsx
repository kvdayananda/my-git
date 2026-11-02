"use client";

import React, { useEffect, useState } from "react";
import {
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  Copy,
  Check,
  AlertTriangle,
  RefreshCw,
} from "lucide-react";
import { api, type JobStatus } from "../lib/api";

interface JobProgressTrackerProps {
  jobId: string;
  title: string;
  description?: string;
  onSuccess: (result: unknown) => void;
  onError: (error: string) => void;
  onDismiss?: () => void;
}

export function JobProgressTracker({
  jobId,
  title,
  description,
  onSuccess,
  onError,
  onDismiss,
}: JobProgressTrackerProps) {
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [copiedId, setCopiedId] = useState(false);
  const [pollError, setPollError] = useState<string | null>(null);

  // Timer ticker
  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Polling effect
  useEffect(() => {
    let cancelled = false;
    let pollTimeout: NodeJS.Timeout | null = null;

    const checkJob = async () => {
      try {
        const res = await api.jobs.status(jobId);
        if (cancelled) return;
        setStatus(res);
        setPollError(null);

        if (res.ready) {
          if (res.successful) {
            onSuccess(res.result);
          } else {
            const errMsg = res.error || "Background task failed in Celery worker.";
            onError(errMsg);
          }
          return;
        }

        // Still running, schedule next poll
        pollTimeout = setTimeout(checkJob, 1200);
      } catch (err) {
        if (cancelled) return;
        setPollError(err instanceof Error ? err.message : "Polling error.");
        pollTimeout = setTimeout(checkJob, 2000);
      }
    };

    void checkJob();

    return () => {
      cancelled = true;
      if (pollTimeout) clearTimeout(pollTimeout);
    };
  }, [jobId, onSuccess, onError]);

  const copyJobId = async () => {
    try {
      await navigator.clipboard.writeText(jobId);
      setCopiedId(true);
      setTimeout(() => setCopiedId(false), 1500);
    } catch {
      // fallback
    }
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  };

  const isComplete = status?.ready ?? false;
  const isSuccess = status?.successful ?? false;
  const isFailed = status?.failed ?? false;

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[#0f141a] p-5 shadow-lg space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--surface-raised)] border border-[var(--border)]">
            {isSuccess ? (
              <CheckCircle2 className="h-5 w-5 text-emerald-400" />
            ) : isFailed ? (
              <XCircle className="h-5 w-5 text-rose-400" />
            ) : (
              <Loader2 className="h-5 w-5 animate-spin text-[var(--accent)]" />
            )}
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white">{title}</h4>
            {description && <p className="text-xs text-[var(--muted)]">{description}</p>}
          </div>
        </div>

        {/* State Badge and Timer */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 text-xs text-[var(--muted)] font-mono">
            <Clock className="h-3.5 w-3.5" />
            <span>{formatTime(elapsedSeconds)}</span>
          </div>

          <span
            className={`rounded-full px-2.5 py-0.5 text-xs font-mono font-medium border ${
              isSuccess
                ? "bg-emerald-950/60 border-emerald-500/30 text-emerald-300"
                : isFailed
                ? "bg-rose-950/60 border-rose-500/30 text-rose-300"
                : status?.state === "STARTED"
                ? "bg-blue-950/60 border-blue-500/30 text-blue-300 animate-pulse"
                : "bg-amber-950/60 border-amber-500/30 text-amber-300 animate-pulse"
            }`}
          >
            {status?.state ?? "PENDING"}
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="relative h-1.5 w-full overflow-hidden rounded-full bg-[var(--surface-raised)]">
        {isSuccess ? (
          <div className="h-full w-full bg-emerald-500 transition-all duration-300" />
        ) : isFailed ? (
          <div className="h-full w-full bg-rose-500 transition-all duration-300" />
        ) : (
          <div className="h-full w-1/3 bg-[var(--accent)] animate-[pulse_1.5s_infinite] transition-all" />
        )}
      </div>

      {/* Notice / Details */}
      <div className="flex flex-wrap items-center justify-between text-xs text-[var(--muted)] pt-1">
        <div className="flex items-center gap-1.5 font-mono">
          <span>Celery Job:</span>
          <code className="text-white text-[11px]">{jobId.slice(0, 16)}...</code>
          <button
            type="button"
            onClick={() => void copyJobId()}
            className="hover:text-white transition"
            title="Copy full Job UUID"
          >
            {copiedId ? (
              <Check className="h-3 w-3 text-emerald-400" />
            ) : (
              <Copy className="h-3 w-3" />
            )}
          </button>
        </div>

        {status?.notice && (
          <span className="text-[11px] text-[var(--muted)] italic">
            {status.notice}
          </span>
        )}
      </div>

      {/* Failure or Poll Error */}
      {isFailed && status?.error && (
        <div className="rounded-lg border border-rose-500/20 bg-rose-500/10 p-3 text-xs text-rose-200">
          <strong>Worker Error:</strong> {status.error}
        </div>
      )}

      {pollError && !isComplete && (
        <div className="flex items-center gap-2 text-xs text-amber-300">
          <AlertTriangle className="h-3.5 w-3.5" />
          <span>Connection transient issue: {pollError}. Retrying…</span>
        </div>
      )}

      {/* Dismiss button when finished */}
      {isComplete && onDismiss && (
        <div className="flex justify-end pt-1">
          <button
            type="button"
            onClick={onDismiss}
            className="rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs text-[var(--muted)] hover:text-white hover:bg-[var(--surface-raised)] transition"
          >
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
}

