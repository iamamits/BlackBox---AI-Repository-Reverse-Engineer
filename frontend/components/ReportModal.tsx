"use client";

import React, { useState, useEffect } from "react";
import {
  X,
  Download,
  Printer,
  FileCode2,
  FileText,
  ShieldAlert,
  CheckCircle2,
  Sparkles,
  Layers,
  ChevronRight,
  ExternalLink,
  Code2,
  FolderGit2
} from "lucide-react";
import { fetchReport, getReportDownloadUrl, RepoAuditReport } from "../lib/api";

interface ReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  repoId: number | null;
  repoName: string;
}

export default function ReportModal({ isOpen, onClose, repoId, repoName }: ReportModalProps) {
  const [report, setReport] = useState<RepoAuditReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"summary" | "components" | "symbols" | "security">("summary");

  useEffect(() => {
    if (!isOpen || !repoId) return;

    setLoading(true);
    setError(null);
    fetchReport(repoId)
      .then((data) => setReport(data))
      .catch((err) => setError(err.message || "Failed to load audit report"))
      .finally(() => setLoading(false));
  }, [isOpen, repoId]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <div className="relative w-full max-w-4xl max-h-[90vh] flex flex-col rounded-2xl glass-panel border border-slate-700/80 shadow-2xl shadow-indigo-500/10 overflow-hidden">
        {/* Glow decorative blur */}
        <div className="absolute -top-32 -right-32 w-64 h-64 bg-indigo-500/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-32 -left-32 w-64 h-64 bg-cyan-500/15 rounded-full blur-3xl pointer-events-none" />

        {/* Modal Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-800 bg-slate-950/40 shrink-0">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-500 text-white shadow-lg shadow-indigo-500/20">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-white">Repository Audit Report</h2>
                <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-md bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                  Institutional Grade
                </span>
              </div>
              <p className="text-xs text-slate-400">
                {repoName} • Generated autonomously via BlackBox & Nebius/NVIDIA
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {report && (
              <>
                <a
                  href={getReportDownloadUrl(report.repository_id, "html")}
                  download={`blackbox_report_${report.repository_id}.html`}
                  className="flex items-center gap-1.5 py-1.5 px-3 rounded-lg text-xs font-semibold text-slate-300 hover:text-white bg-slate-800/80 hover:bg-slate-700 border border-slate-700 transition-colors"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download HTML</span>
                </a>
                <a
                  href={getReportDownloadUrl(report.repository_id, "markdown")}
                  download={`blackbox_report_${report.repository_id}.md`}
                  className="flex items-center gap-1.5 py-1.5 px-3 rounded-lg text-xs font-semibold text-slate-300 hover:text-white bg-slate-800/80 hover:bg-slate-700 border border-slate-700 transition-colors"
                >
                  <FileCode2 className="w-3.5 h-3.5" />
                  <span>Export MD</span>
                </a>
              </>
            )}
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading && (
            <div className="flex flex-col items-center justify-center py-20 space-y-4">
              <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
              <div className="text-sm font-medium text-slate-300">
                Synthesizing Full Codebase Audit & Security Metrics...
              </div>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm">
              {error}
            </div>
          )}

          {report && !loading && (
            <>
              {/* Executive Score Card */}
              <div className="flex flex-col md:flex-row items-center justify-between p-6 rounded-2xl bg-gradient-to-r from-slate-900/90 to-slate-900/50 border border-slate-800 gap-6">
                <div>
                  <div className="text-xs uppercase tracking-wider text-slate-400 font-semibold mb-1">
                    Overall Architecture Rating
                  </div>
                  <h3 className="text-2xl font-black text-white">{report.repository_name}</h3>
                  <p className="text-xs text-slate-400 mt-1 max-w-xl">
                    {report.summary}
                  </p>
                </div>

                <div className="flex items-center gap-4 bg-slate-950/70 p-4 rounded-xl border border-slate-800 shrink-0">
                  <div className="text-right">
                    <div className="text-xs uppercase text-slate-400">Health Index</div>
                    <div className="text-3xl font-black text-white">{report.health_score}%</div>
                  </div>
                  <div className="flex items-center justify-center w-14 h-14 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 font-black text-2xl">
                    {report.security_grade}
                  </div>
                </div>
              </div>

              {/* 4 Key Metrics Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {report.metrics.map((m, idx) => (
                  <div key={idx} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                    <div className="text-xs text-slate-400 uppercase tracking-wider">{m.label}</div>
                    <div className="text-2xl font-bold text-white mt-1">{m.value}</div>
                    {m.change && (
                      <div className="text-xs text-cyan-400 mt-0.5 font-medium">{m.change}</div>
                    )}
                  </div>
                ))}
              </div>

              {/* Section Tabs */}
              <div className="flex border-b border-slate-800 gap-2">
                <button
                  onClick={() => setActiveTab("summary")}
                  className={`py-2 px-4 text-xs font-semibold rounded-t-lg transition-colors border-b-2 ${
                    activeTab === "summary"
                      ? "border-indigo-500 text-indigo-400 bg-indigo-500/10"
                      : "border-transparent text-slate-400 hover:text-white"
                  }`}
                >
                  Architecture Overview
                </button>
                <button
                  onClick={() => setActiveTab("components")}
                  className={`py-2 px-4 text-xs font-semibold rounded-t-lg transition-colors border-b-2 ${
                    activeTab === "components"
                      ? "border-indigo-500 text-indigo-400 bg-indigo-500/10"
                      : "border-transparent text-slate-400 hover:text-white"
                  }`}
                >
                  Component Distribution ({report.component_breakdown.length})
                </button>
                <button
                  onClick={() => setActiveTab("symbols")}
                  className={`py-2 px-4 text-xs font-semibold rounded-t-lg transition-colors border-b-2 ${
                    activeTab === "symbols"
                      ? "border-indigo-500 text-indigo-400 bg-indigo-500/10"
                      : "border-transparent text-slate-400 hover:text-white"
                  }`}
                >
                  AST Symbol Catalog
                </button>
                <button
                  onClick={() => setActiveTab("security")}
                  className={`py-2 px-4 text-xs font-semibold rounded-t-lg transition-colors border-b-2 ${
                    activeTab === "security"
                      ? "border-indigo-500 text-indigo-400 bg-indigo-500/10"
                      : "border-transparent text-slate-400 hover:text-white"
                  }`}
                >
                  Security Findings ({report.security_findings.length})
                </button>
              </div>

              {/* Tab 1: Architecture Overview */}
              {activeTab === "summary" && (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                    <h4 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-indigo-400" />
                      Executive Assessment
                    </h4>
                    <p className="text-xs text-slate-300 leading-relaxed">
                      {report.summary}
                    </p>
                  </div>

                  {report.investigation_history.length > 0 && (
                    <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                      <h4 className="text-sm font-semibold text-white mb-3">AI Deep Root-Cause Inferences</h4>
                      <div className="space-y-3">
                        {report.investigation_history.map((inv) => (
                          <div key={inv.id} className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
                            <div className="flex items-center justify-between text-xs font-medium text-slate-300">
                              <span className="font-semibold text-white">{inv.question}</span>
                              <span className="text-[10px] text-indigo-400 font-mono">{inv.model_used}</span>
                            </div>
                            <div className="text-xs text-slate-400 mt-1.5">{inv.summary}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Tab 2: Components */}
              {activeTab === "components" && (
                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                  <h4 className="text-sm font-semibold text-white mb-3">Module & Language Breakdown</h4>
                  <table className="w-full text-xs text-left">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-400">
                        <th className="pb-2">Language Environment</th>
                        <th className="pb-2">Indexed Files</th>
                        <th className="pb-2">Codebase Share</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {report.component_breakdown.map((comp, idx) => (
                        <tr key={idx} className="hover:bg-slate-800/20">
                          <td className="py-2.5 font-semibold text-white">{comp.language}</td>
                          <td className="py-2.5 text-slate-300">{comp.files}</td>
                          <td className="py-2.5">
                            <div className="flex items-center gap-2">
                              <div className="flex-1 max-w-[100px] h-1.5 rounded-full bg-slate-800 overflow-hidden">
                                <div
                                  className="h-full bg-indigo-500 rounded-full"
                                  style={{ width: `${comp.percentage}%` }}
                                />
                              </div>
                              <span className="text-slate-400 font-mono">{comp.percentage}%</span>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Tab 3: Symbols */}
              {activeTab === "symbols" && (
                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                  <h4 className="text-sm font-semibold text-white mb-3">AST Code Symbols Distribution</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {Object.entries(report.symbol_statistics).map(([kind, count]) => (
                      <div key={kind} className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
                        <div className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
                          {kind}s
                        </div>
                        <div className="text-xl font-bold text-white mt-0.5">{count}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tab 4: Security Findings */}
              {activeTab === "security" && (
                <div className="space-y-3">
                  {report.security_findings.map((f, idx) => (
                    <div
                      key={idx}
                      className={`p-4 rounded-xl border ${
                        f.severity === "critical"
                          ? "bg-rose-500/10 border-rose-500/30"
                          : f.severity === "high"
                          ? "bg-amber-500/10 border-amber-500/30"
                          : "bg-slate-900/60 border-slate-800"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-sm font-bold text-white">{f.title}</span>
                        <span
                          className={`px-2 py-0.5 text-[10px] font-bold uppercase rounded-md ${
                            f.severity === "critical"
                              ? "bg-rose-500/20 text-rose-400"
                              : f.severity === "high"
                              ? "bg-amber-500/20 text-amber-400"
                              : "bg-indigo-500/20 text-indigo-400"
                          }`}
                        >
                          {f.severity}
                        </span>
                      </div>
                      <div className="text-xs text-slate-400 font-mono mb-2">
                        {f.file_path || "Repository Global"} {f.line_number ? `Line ${f.line_number}` : ""} • Category: {f.category}
                      </div>
                      <div className="text-xs text-slate-300 leading-relaxed">{f.description}</div>
                      {f.remediation && (
                        <div className="mt-2 text-xs text-emerald-400 font-medium">
                          <strong>Remediation:</strong> {f.remediation}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
