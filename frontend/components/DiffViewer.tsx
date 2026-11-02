"use client";

import React, { useMemo, useState } from "react";
import {
  ChevronDown,
  ChevronRight,
  Copy,
  Check,
  FileCode,
  FilePlus,
  FileMinus,
  FileEdit,
  Columns,
  AlignJustify,
  Search,
  Maximize2,
  Minimize2,
} from "lucide-react";

export interface DiffLine {
  type: "add" | "delete" | "context" | "hunk-header";
  text: string;
  oldLineNumber?: number;
  newLineNumber?: number;
}

export interface DiffHunk {
  header: string;
  lines: DiffLine[];
}

export interface DiffFile {
  id: string;
  oldPath: string;
  newPath: string;
  displayPath: string;
  status: "added" | "deleted" | "modified";
  additions: number;
  deletions: number;
  hunks: DiffHunk[];
}

function parseUnifiedDiff(diffText: string): DiffFile[] {
  if (!diffText || !diffText.trim()) return [];

  const lines = diffText.split("\n");
  const files: DiffFile[] = [];

  let currentFile: Partial<DiffFile> | null = null;
  let currentHunk: DiffHunk | null = null;
  let oldLine = 0;
  let newLine = 0;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    if (line.startsWith("--- ")) {
      // Start of a new file header
      const oldPath = line.substring(4).trim().replace(/^a\//, "");
      // Lookahead for +++
      let newPath = "";
      if (i + 1 < lines.length && lines[i + 1].startsWith("+++ ")) {
        newPath = lines[i + 1].substring(4).trim().replace(/^b\//, "");
        i++; // skip next line
      }

      let status: "added" | "deleted" | "modified" = "modified";
      if (oldPath === "/dev/null" || oldPath.includes("[original content unavailable]")) {
        status = "added";
      } else if (newPath === "/dev/null") {
        status = "deleted";
      }

      const displayPath = newPath && newPath !== "/dev/null" ? newPath : oldPath;

      if (currentFile && currentFile.hunks) {
        if (currentHunk) currentFile.hunks.push(currentHunk);
        files.push(currentFile as DiffFile);
      }

      currentHunk = null;
      currentFile = {
        id: `file-${files.length}-${displayPath}`,
        oldPath,
        newPath,
        displayPath,
        status,
        additions: 0,
        deletions: 0,
        hunks: [],
      };
      continue;
    }

    if (line.startsWith("@@ ")) {
      if (currentFile && currentHunk) {
        currentFile.hunks!.push(currentHunk);
      }

      // Parse hunk header: @@ -oldStart,oldCount +newStart,newCount @@
      const match = line.match(/^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@(.*)$/);
      if (match) {
        oldLine = parseInt(match[1], 10);
        newLine = parseInt(match[2], 10);
      } else {
        oldLine = 1;
        newLine = 1;
      }

      currentHunk = {
        header: line,
        lines: [
          {
            type: "hunk-header",
            text: line,
          },
        ],
      };
      continue;
    }

    if (!currentFile) {
      // File header not yet encountered, ignore metadata or preamble
      continue;
    }

    if (!currentHunk) {
      currentHunk = {
        header: "@@ Chunk @@",
        lines: [],
      };
    }

    if (line.startsWith("+")) {
      currentFile.additions = (currentFile.additions || 0) + 1;
      currentHunk.lines.push({
        type: "add",
        text: line.substring(1),
        newLineNumber: newLine++,
      });
    } else if (line.startsWith("-")) {
      currentFile.deletions = (currentFile.deletions || 0) + 1;
      currentHunk.lines.push({
        type: "delete",
        text: line.substring(1),
        oldLineNumber: oldLine++,
      });
    } else if (line.startsWith(" ")) {
      currentHunk.lines.push({
        type: "context",
        text: line.substring(1),
        oldLineNumber: oldLine++,
        newLineNumber: newLine++,
      });
    } else if (line.startsWith("\\")) {
      // e.g. "\ No newline at end of file"
      currentHunk.lines.push({
        type: "context",
        text: line,
      });
    }
  }

  if (currentFile) {
    if (currentHunk) currentFile.hunks!.push(currentHunk);
    files.push(currentFile as DiffFile);
  }

  return files;
}

export function DiffViewer({
  diff,
  emptyMessage = "No changes to display.",
}: {
  diff: string;
  emptyMessage?: string;
}) {
  const [viewMode, setViewMode] = useState<"unified" | "split">("unified");
  const [search, setSearch] = useState("");
  const [collapsedFiles, setCollapsedFiles] = useState<Record<string, boolean>>({});
  const [copiedRaw, setCopiedRaw] = useState(false);
  const [copiedFile, setCopiedFile] = useState<string | null>(null);

  const parsedFiles = useMemo(() => parseUnifiedDiff(diff), [diff]);

  const filteredFiles = useMemo(() => {
    if (!search.trim()) return parsedFiles;
    const q = search.toLowerCase();
    return parsedFiles.filter(
      (f) =>
        f.displayPath.toLowerCase().includes(q) ||
        f.oldPath.toLowerCase().includes(q) ||
        f.newPath.toLowerCase().includes(q)
    );
  }, [parsedFiles, search]);

  const totals = useMemo(() => {
    let additions = 0;
    let deletions = 0;
    for (const f of parsedFiles) {
      additions += f.additions;
      deletions += f.deletions;
    }
    return { additions, deletions, files: parsedFiles.length };
  }, [parsedFiles]);

  const toggleCollapse = (fileId: string) => {
    setCollapsedFiles((prev) => ({
      ...prev,
      [fileId]: !prev[fileId],
    }));
  };

  const collapseAll = () => {
    const next: Record<string, boolean> = {};
    for (const f of parsedFiles) {
      next[f.id] = true;
    }
    setCollapsedFiles(next);
  };

  const expandAll = () => {
    setCollapsedFiles({});
  };

  const copyRawDiff = async () => {
    try {
      await navigator.clipboard.writeText(diff);
      setCopiedRaw(true);
      setTimeout(() => setCopiedRaw(false), 2000);
    } catch {
      // fallback
    }
  };

  const copyFilePath = async (path: string) => {
    try {
      await navigator.clipboard.writeText(path);
      setCopiedFile(path);
      setTimeout(() => setCopiedFile(null), 1500);
    } catch {
      // fallback
    }
  };

  if (!diff || !diff.trim() || parsedFiles.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-[var(--border)] bg-black/20 p-8 text-center">
        <FileCode className="mx-auto mb-2 h-7 w-7 text-[var(--muted)]" />
        <p className="text-xs text-[var(--muted)]">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4 font-sans">
      {/* Top Controls Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[var(--border)] bg-[var(--surface-raised)]/70 p-3.5 backdrop-blur-sm">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-white">
              {totals.files} {totals.files === 1 ? "file changed" : "files changed"}
            </span>
            <div className="flex items-center gap-1.5 text-xs font-mono">
              <span className="rounded bg-emerald-950/70 border border-emerald-500/30 px-1.5 py-0.5 text-emerald-400 font-medium">
                +{totals.additions}
              </span>
              <span className="rounded bg-rose-950/70 border border-rose-500/30 px-1.5 py-0.5 text-rose-400 font-medium">
                -{totals.deletions}
              </span>
            </div>
          </div>

          {/* Search / Filter file */}
          {parsedFiles.length > 1 && (
            <div className="relative min-w-[180px]">
              <Search className="absolute left-2.5 top-2 h-3.5 w-3.5 text-[var(--muted)]" />
              <input
                type="text"
                placeholder="Filter files…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full rounded-md border border-[var(--border)] bg-[var(--surface)] py-1 pl-8 pr-2.5 text-xs text-white placeholder:text-[var(--muted)] focus:border-[var(--accent)] focus:outline-none"
              />
            </div>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Mode switch: Unified vs Split */}
          <div className="flex rounded-lg border border-[var(--border)] bg-[var(--surface)] p-0.5 text-xs">
            <button
              onClick={() => setViewMode("unified")}
              className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 transition ${
                viewMode === "unified"
                  ? "bg-[#1c2a23] text-[var(--accent)] font-medium"
                  : "text-[var(--muted)] hover:text-white"
              }`}
              title="Unified view"
            >
              <AlignJustify className="h-3.5 w-3.5" />
              Unified
            </button>
            <button
              onClick={() => setViewMode("split")}
              className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 transition ${
                viewMode === "split"
                  ? "bg-[#1c2a23] text-[var(--accent)] font-medium"
                  : "text-[var(--muted)] hover:text-white"
              }`}
              title="Split side-by-side view"
            >
              <Columns className="h-3.5 w-3.5" />
              Split
            </button>
          </div>

          {/* Expand / Collapse all */}
          <button
            onClick={collapseAll}
            className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-1.5 text-[var(--muted)] hover:text-white"
            title="Collapse all files"
          >
            <Minimize2 className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={expandAll}
            className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-1.5 text-[var(--muted)] hover:text-white"
            title="Expand all files"
          >
            <Maximize2 className="h-3.5 w-3.5" />
          </button>

          {/* Copy raw diff */}
          <button
            onClick={() => void copyRawDiff()}
            className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-2.5 py-1 text-xs text-[var(--muted)] hover:text-white transition"
            title="Copy raw unified diff"
          >
            {copiedRaw ? (
              <>
                <Check className="h-3.5 w-3.5 text-emerald-400" />
                <span className="text-emerald-400 font-medium">Copied!</span>
              </>
            ) : (
              <>
                <Copy className="h-3.5 w-3.5" />
                <span>Raw diff</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* File List */}
      <div className="space-y-4">
        {filteredFiles.map((file) => {
          const isCollapsed = Boolean(collapsedFiles[file.id]);

          return (
            <div
              key={file.id}
              className="overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-md"
            >
              {/* File Header Bar */}
              <div
                onClick={() => toggleCollapse(file.id)}
                className="flex cursor-pointer select-none items-center justify-between border-b border-[var(--border)] bg-[var(--surface-raised)]/90 px-4 py-2.5 hover:bg-[#1a212c] transition"
              >
                <div className="flex items-center gap-2.5 overflow-hidden">
                  <button
                    type="button"
                    className="text-[var(--muted)] hover:text-white"
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleCollapse(file.id);
                    }}
                  >
                    {isCollapsed ? (
                      <ChevronRight className="h-4 w-4" />
                    ) : (
                      <ChevronDown className="h-4 w-4" />
                    )}
                  </button>

                  {/* Status icon badge */}
                  {file.status === "added" ? (
                    <span className="flex items-center gap-1 rounded bg-emerald-950/80 border border-emerald-500/30 px-1.5 py-0.5 text-[11px] font-medium text-emerald-300">
                      <FilePlus className="h-3 w-3" /> ADDED
                    </span>
                  ) : file.status === "deleted" ? (
                    <span className="flex items-center gap-1 rounded bg-rose-950/80 border border-rose-500/30 px-1.5 py-0.5 text-[11px] font-medium text-rose-300">
                      <FileMinus className="h-3 w-3" /> DELETED
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 rounded bg-blue-950/80 border border-blue-500/30 px-1.5 py-0.5 text-[11px] font-medium text-blue-300">
                      <FileEdit className="h-3 w-3" /> MODIFIED
                    </span>
                  )}

                  {/* File Path */}
                  <span className="truncate font-mono text-xs font-semibold text-white">
                    {file.displayPath}
                  </span>

                  {/* Copy Path Shortcut */}
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      void copyFilePath(file.displayPath);
                    }}
                    className="text-[var(--muted)] hover:text-white transition"
                    title="Copy file path"
                  >
                    {copiedFile === file.displayPath ? (
                      <Check className="h-3 w-3 text-emerald-400" />
                    ) : (
                      <Copy className="h-3 w-3 opacity-60 hover:opacity-100" />
                    )}
                  </button>
                </div>

                {/* File Additions / Deletions count */}
                <div className="flex items-center gap-2 font-mono text-xs">
                  {file.additions > 0 && (
                    <span className="text-emerald-400 font-medium">+{file.additions}</span>
                  )}
                  {file.deletions > 0 && (
                    <span className="text-rose-400 font-medium">-{file.deletions}</span>
                  )}
                </div>
              </div>

              {/* File Body Content */}
              {!isCollapsed && (
                <div className="overflow-x-auto text-xs font-mono leading-5">
                  {viewMode === "unified" ? (
                    <table className="w-full border-collapse">
                      <tbody>
                        {file.hunks.flatMap((hunk, hunkIdx) =>
                          hunk.lines.map((l, lineIdx) => {
                            if (l.type === "hunk-header") {
                              return (
                                <tr
                                  key={`hunk-${hunkIdx}-${lineIdx}`}
                                  className="bg-[#151c24] text-[var(--muted)] border-y border-[var(--border)]"
                                >
                                  <td
                                    colSpan={3}
                                    className="px-4 py-1 text-[11px] text-[#7d8b9d] italic"
                                  >
                                    {l.text}
                                  </td>
                                </tr>
                              );
                            }

                            const isAdd = l.type === "add";
                            const isDelete = l.type === "delete";

                            const rowBg = isAdd
                              ? "bg-emerald-950/30 hover:bg-emerald-950/50"
                              : isDelete
                              ? "bg-rose-950/30 hover:bg-rose-950/50"
                              : "hover:bg-[var(--surface-raised)]/40";

                            const textColor = isAdd
                              ? "text-emerald-200"
                              : isDelete
                              ? "text-rose-200"
                              : "text-[var(--text)]";

                            const prefixColor = isAdd
                              ? "text-emerald-400 font-bold"
                              : isDelete
                              ? "text-rose-400 font-bold"
                              : "text-[var(--muted)]";

                            const prefix = isAdd ? "+" : isDelete ? "-" : " ";

                            return (
                              <tr
                                key={`line-${hunkIdx}-${lineIdx}`}
                                className={`transition-colors ${rowBg}`}
                              >
                                {/* Old Line Number */}
                                <td className="w-12 select-none border-r border-[var(--border)]/40 px-2.5 py-0.5 text-right font-mono text-[11px] text-[var(--muted)] opacity-60">
                                  {l.oldLineNumber ?? ""}
                                </td>
                                {/* New Line Number */}
                                <td className="w-12 select-none border-r border-[var(--border)]/40 px-2.5 py-0.5 text-right font-mono text-[11px] text-[var(--muted)] opacity-60">
                                  {l.newLineNumber ?? ""}
                                </td>
                                {/* Line Content */}
                                <td
                                  className={`px-3 py-0.5 whitespace-pre font-mono ${textColor}`}
                                >
                                  <span className={`inline-block w-4 select-none ${prefixColor}`}>
                                    {prefix}
                                  </span>
                                  {l.text}
                                </td>
                              </tr>
                            );
                          })
                        )}
                      </tbody>
                    </table>
                  ) : (
                    /* Split Mode: Side-by-Side */
                    <table className="w-full border-collapse">
                      <thead>
                        <tr className="border-b border-[var(--border)] bg-[#121820] text-[11px] text-[var(--muted)]">
                          <th className="w-1/2 px-4 py-1 text-left font-normal border-r border-[var(--border)]">
                            Original (Base Commit)
                          </th>
                          <th className="w-1/2 px-4 py-1 text-left font-normal">
                            Proposed Changes
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {file.hunks.flatMap((hunk, hunkIdx) => {
                          const leftRows: DiffLine[] = [];
                          const rightRows: DiffLine[] = [];

                          for (const line of hunk.lines) {
                            if (line.type === "hunk-header") {
                              leftRows.push(line);
                              rightRows.push(line);
                            } else if (line.type === "delete") {
                              leftRows.push(line);
                            } else if (line.type === "add") {
                              rightRows.push(line);
                            } else {
                              // Context
                              // Align rows before context
                              while (leftRows.length < rightRows.length) {
                                leftRows.push({ type: "context", text: "" });
                              }
                              while (rightRows.length < leftRows.length) {
                                rightRows.push({ type: "context", text: "" });
                              }
                              leftRows.push(line);
                              rightRows.push(line);
                            }
                          }

                          while (leftRows.length < rightRows.length) {
                            leftRows.push({ type: "context", text: "" });
                          }
                          while (rightRows.length < leftRows.length) {
                            rightRows.push({ type: "context", text: "" });
                          }

                          return leftRows.map((left, idx) => {
                            const right = rightRows[idx];

                            if (left.type === "hunk-header") {
                              return (
                                <tr
                                  key={`split-hunk-${hunkIdx}-${idx}`}
                                  className="bg-[#151c24] text-[var(--muted)] border-y border-[var(--border)]"
                                >
                                  <td
                                    colSpan={2}
                                    className="px-4 py-1 text-[11px] text-[#7d8b9d] italic"
                                  >
                                    {left.text}
                                  </td>
                                </tr>
                              );
                            }

                            const leftBg =
                              left.type === "delete"
                                ? "bg-rose-950/30 text-rose-200"
                                : "text-[var(--text)]";
                            const rightBg =
                              right.type === "add"
                                ? "bg-emerald-950/30 text-emerald-200"
                                : "text-[var(--text)]";

                            return (
                              <tr key={`split-line-${hunkIdx}-${idx}`} className="border-b border-[var(--border)]/20">
                                {/* Left Side */}
                                <td
                                  className={`w-1/2 border-r border-[var(--border)] p-0 align-top ${leftBg}`}
                                >
                                  <div className="flex">
                                    <span className="w-10 select-none border-r border-[var(--border)]/40 px-2 py-0.5 text-right font-mono text-[11px] text-[var(--muted)] opacity-60">
                                      {left.oldLineNumber ?? ""}
                                    </span>
                                    <span className="px-2 py-0.5 whitespace-pre font-mono flex-1">
                                      {left.type === "delete" && (
                                        <span className="text-rose-400 font-bold mr-1.5">-</span>
                                      )}
                                      {left.text}
                                    </span>
                                  </div>
                                </td>

                                {/* Right Side */}
                                <td className={`w-1/2 p-0 align-top ${rightBg}`}>
                                  <div className="flex">
                                    <span className="w-10 select-none border-r border-[var(--border)]/40 px-2 py-0.5 text-right font-mono text-[11px] text-[var(--muted)] opacity-60">
                                      {right.newLineNumber ?? ""}
                                    </span>
                                    <span className="px-2 py-0.5 whitespace-pre font-mono flex-1">
                                      {right.type === "add" && (
                                        <span className="text-emerald-400 font-bold mr-1.5">+</span>
                                      )}
                                      {right.text}
                                    </span>
                                  </div>
                                </td>
                              </tr>
                            );
                          });
                        })}
                      </tbody>
                    </table>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

