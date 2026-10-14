"use client";

import React, { useState } from "react";
import { AlertCircle, ChevronDown, ChevronUp, RefreshCw, X, ShieldAlert, Wrench } from "lucide-react";

export interface DiagnosticError {
  title: string;
  message: string;
  status?: number;
  code?: string;
  endpoint?: string;
  suggestedAction?: string;
}

interface ErrorDiagnosticBannerProps {
  error: DiagnosticError | null;
  onDismiss: () => void;
  onRetry?: () => void;
}

export default function ErrorDiagnosticBanner({
  error,
  onDismiss,
  onRetry,
}: ErrorDiagnosticBannerProps) {
  const [expanded, setExpanded] = useState<boolean>(false);

  if (!error) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 max-w-lg w-full animate-slide-up">
      <div className="rounded-2xl glass-panel border border-rose-500/40 bg-slate-950/95 shadow-2xl shadow-rose-500/20 p-4 text-xs">
        {/* Main Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-2.5 min-w-0">
            <div className="p-1.5 rounded-lg bg-rose-500/20 text-rose-400 shrink-0 mt-0.5">
              <AlertCircle className="w-4 h-4" />
            </div>
            <div>
              <div className="font-bold text-white text-sm">{error.title}</div>
              <div className="text-slate-300 mt-0.5 leading-relaxed">{error.message}</div>
            </div>
          </div>

          <button
            onClick={onDismiss}
            className="p-1 text-slate-400 hover:text-white rounded-lg transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Action Bar */}
        <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-800">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 text-[11px] font-semibold text-indigo-400 hover:text-indigo-300 transition"
          >
            <Wrench className="w-3 h-3" />
            <span>{expanded ? "Hide Diagnostics" : "Inspect Diagnostics & Resolution"}</span>
            {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>

          {onRetry && (
            <button
              onClick={onRetry}
              className="flex items-center gap-1.5 py-1 px-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-[11px] transition shadow-md shadow-indigo-600/30"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Retry Operation</span>
            </button>
          )}
        </div>

        {/* Expandable Technical Diagnostics Panel */}
        {expanded && (
          <div className="mt-3 p-3 rounded-xl bg-slate-900/90 border border-slate-800 font-mono text-[11px] space-y-2 text-slate-300">
            {error.status && (
              <div className="flex justify-between">
                <span className="text-slate-500">HTTP Status:</span>
                <span className="text-rose-400 font-bold">{error.status}</span>
              </div>
            )}
            {error.code && (
              <div className="flex justify-between">
                <span className="text-slate-500">Error Code:</span>
                <span className="text-amber-300">{error.code}</span>
              </div>
            )}
            {error.endpoint && (
              <div className="flex justify-between">
                <span className="text-slate-500">Endpoint:</span>
                <span className="text-slate-400 truncate max-w-[240px]">{error.endpoint}</span>
              </div>
            )}
            {error.suggestedAction && (
              <div className="pt-2 border-t border-slate-800/80 text-[11px] font-sans">
                <span className="font-bold text-emerald-400">Suggested Action: </span>
                <span className="text-slate-300">{error.suggestedAction}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
