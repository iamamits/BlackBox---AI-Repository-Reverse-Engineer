"use client";

import React, { useState, useEffect } from "react";
import {
  X,
  Sparkles,
  Download,
  Copy,
  Check,
  Cpu,
  Layers,
  ShieldCheck,
  FileText,
  Sliders,
  SlidersHorizontal,
  Terminal,
  Bot,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  RefreshCw,
  FolderGit2
} from "lucide-react";
import {
  fetchProjectMemory,
  compileContextPack,
  getNeuralLinkExportUrl,
  ProjectMemoryResponse,
  ContextCompileResponse
} from "../lib/api";

interface NeuralLinkModalProps {
  isOpen: boolean;
  onClose: () => void;
  repoId: number;
  repoName: string;
}

export default function NeuralLinkModal({ isOpen, onClose, repoId, repoName }: NeuralLinkModalProps) {
  const [memory, setMemory] = useState<ProjectMemoryResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Compiler Configuration
  const [taskDescription, setTaskDescription] = useState<string>(
    "Implement new feature with verified tests and zero breaking changes to existing architecture"
  );
  const [tokenBudget, setTokenBudget] = useState<number>(8000);
  const [format, setFormat] = useState<string>("agents_md");
  const [targetAgent, setTargetAgent] = useState<string>("cursor");

  // Compilation Output
  const [compiledPack, setCompiledPack] = useState<ContextCompileResponse | null>(null);
  const [compiling, setCompiling] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"compiler" | "memory" | "integration">("compiler");

  // Load Project Memory
  useEffect(() => {
    if (!isOpen || !repoId) return;
    setLoading(true);
    setError(null);
    fetchProjectMemory(repoId)
      .then((data) => {
        setMemory(data);
      })
      .catch((err) => setError(err.message || "Failed to load project memory"))
      .finally(() => setLoading(false));
  }, [isOpen, repoId]);

  // Handle Compile
  const handleCompile = async () => {
    setCompiling(true);
    setError(null);
    try {
      const res = await compileContextPack(repoId, {
        task_description: taskDescription,
        token_budget: tokenBudget,
        format: format,
        target_agent: targetAgent,
      });
      setCompiledPack(res);
    } catch (err: any) {
      setError(err.message || "Failed to compile context pack");
    } finally {
      setCompiling(false);
    }
  };

  const handleCopy = () => {
    if (!compiledPack) return;
    navigator.clipboard.writeText(compiledPack.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md">
      <div className="relative w-full max-w-4xl max-h-[92vh] flex flex-col rounded-2xl glass-panel border border-indigo-500/30 shadow-2xl shadow-indigo-500/20 overflow-hidden">
        {/* Decorative Glow */}
        <div className="absolute -top-32 -right-32 w-72 h-72 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-32 -left-32 w-72 h-72 bg-cyan-500/20 rounded-full blur-3xl pointer-events-none" />

        {/* Modal Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-800 bg-slate-950/60 shrink-0">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-white shadow-lg shadow-indigo-500/30">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-white">Neural Link: AI Agent Context Center</h2>
                {memory && (
                  <span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded-md bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-mono">
                    v{memory.version} • {memory.is_fresh ? "Fresh" : "Needs Sync"}
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400">
                {repoName} • Transfer complete project memory to Cursor, Claude Code, Windsurf & Antigravity
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <a
              href={getNeuralLinkExportUrl(repoId, "agents_md")}
              download="AGENTS.md"
              className="flex items-center gap-1.5 py-1.5 px-3 rounded-lg text-xs font-semibold text-slate-300 hover:text-white bg-slate-800/80 hover:bg-slate-700 border border-slate-700 transition"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export AGENTS.md</span>
            </a>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Subheader Tabs */}
        <div className="flex px-6 pt-3 border-b border-slate-800 bg-slate-950/30 gap-2 shrink-0">
          <button
            onClick={() => setActiveTab("compiler")}
            className={`py-2 px-4 text-xs font-semibold rounded-t-lg transition border-b-2 ${
              activeTab === "compiler"
                ? "border-indigo-500 text-indigo-400 bg-indigo-500/10"
                : "border-transparent text-slate-400 hover:text-white"
            }`}
          >
            Token-Aware Context Compiler
          </button>
          <button
            onClick={() => setActiveTab("memory")}
            className={`py-2 px-4 text-xs font-semibold rounded-t-lg transition border-b-2 ${
              activeTab === "memory"
                ? "border-indigo-500 text-indigo-400 bg-indigo-500/10"
                : "border-transparent text-slate-400 hover:text-white"
            }`}
          >
            Persistent Project Memory
          </button>
          <button
            onClick={() => setActiveTab("integration")}
            className={`py-2 px-4 text-xs font-semibold rounded-t-lg transition border-b-2 ${
              activeTab === "integration"
                ? "border-indigo-500 text-indigo-400 bg-indigo-500/10"
                : "border-transparent text-slate-400 hover:text-white"
            }`}
          >
            Agent Setup Instructions
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
              {error}
            </div>
          )}

          {/* TAB 1: CONTEXT COMPILER */}
          {activeTab === "compiler" && (
            <div className="space-y-6">
              {/* Compiler Controls Panel */}
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Target Task / Feature Objective
                  </label>
                  <input
                    type="text"
                    value={taskDescription}
                    onChange={(e) => setTaskDescription(e.target.value)}
                    placeholder="Describe the task or bug to compile context for..."
                    className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  {/* Target Agent */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5">Target AI Agent</label>
                    <select
                      value={targetAgent}
                      onChange={(e) => setTargetAgent(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-slate-200 focus:outline-none"
                    >
                      <option value="cursor">Cursor (.cursorrules)</option>
                      <option value="windsurf">Windsurf (.windsurfrules)</option>
                      <option value="claude">Claude Code (CLAUDE.md)</option>
                      <option value="antigravity">Antigravity (AGENTS.md)</option>
                      <option value="codex">Codex / Generic LLM</option>
                    </select>
                  </div>

                  {/* Format */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5">Output Format</label>
                    <select
                      value={format}
                      onChange={(e) => setFormat(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-slate-200 focus:outline-none"
                    >
                      <option value="agents_md">AGENTS.md Format</option>
                      <option value="markdown">Detailed Markdown</option>
                      <option value="compact">Compact Prompt Pack</option>
                    </select>
                  </div>

                  {/* Token Budget Slider */}
                  <div>
                    <div className="flex items-center justify-between text-xs mb-1.5">
                      <span className="font-semibold text-slate-400">Token Budget</span>
                      <span className="font-mono text-cyan-400 font-bold">{tokenBudget.toLocaleString()} tokens</span>
                    </div>
                    <input
                      type="range"
                      min={2000}
                      max={32000}
                      step={2000}
                      value={tokenBudget}
                      onChange={(e) => setTokenBudget(Number(e.target.value))}
                      className="w-full accent-indigo-500 cursor-pointer"
                    />
                  </div>
                </div>

                <button
                  onClick={handleCompile}
                  disabled={compiling || !taskDescription.trim()}
                  className="w-full py-2.5 px-4 rounded-xl font-bold text-xs text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 transition shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>{compiling ? "Compiling Token-Budgeted Context..." : "Compile Context Pack"}</span>
                </button>
              </div>

              {/* Compiled Output Preview */}
              {compiledPack && (
                <div className="p-5 rounded-2xl bg-slate-950 border border-slate-800 space-y-3">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-white">Compiled Dossier</span>
                      <span
                        className={`px-2 py-0.5 text-[10px] font-bold uppercase rounded-md ${
                          compiledPack.within_budget
                            ? "bg-emerald-500/20 text-emerald-400"
                            : "bg-amber-500/20 text-amber-400"
                        }`}
                      >
                        ~{compiledPack.estimated_tokens.toLocaleString()} Tokens ({compiledPack.within_budget ? "Within Budget" : "Exceeds Budget"})
                      </span>
                    </div>

                    <button
                      onClick={handleCopy}
                      className="flex items-center gap-1.5 py-1 px-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition"
                    >
                      {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copied ? "Copied!" : "Copy Pack"}</span>
                    </button>
                  </div>

                  <pre className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 font-mono text-xs text-slate-300 max-h-72 overflow-y-auto leading-relaxed">
                    {compiledPack.content}
                  </pre>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: PERSISTENT PROJECT MEMORY */}
          {activeTab === "memory" && memory && (
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-400 mb-1">
                  1. Project Identity
                </h4>
                <pre className="font-mono text-xs text-slate-300 whitespace-pre-wrap">
                  {memory.sections.identity || "Not recorded."}
                </pre>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-400 mb-1">
                  2. Architecture Summary
                </h4>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {memory.sections.architecture || "Not recorded."}
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-400 mb-1">
                  3. Strict Engineering Constraints
                </h4>
                <pre className="font-mono text-xs text-rose-300 whitespace-pre-wrap">
                  {memory.sections.constraints || "Not recorded."}
                </pre>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-400 mb-1">
                  4. Coding Conventions
                </h4>
                <pre className="font-mono text-xs text-slate-300 whitespace-pre-wrap">
                  {memory.sections.conventions || "Not recorded."}
                </pre>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-400 mb-1">
                  5. Verification Commands
                </h4>
                <pre className="font-mono text-xs text-emerald-300 whitespace-pre-wrap">
                  {memory.sections.test_instructions || "Not recorded."}
                </pre>
              </div>
            </div>
          )}

          {/* TAB 3: AGENT SETUP INSTRUCTIONS */}
          {activeTab === "integration" && (
            <div className="space-y-4 text-xs">
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                <div className="font-bold text-white text-sm flex items-center gap-2">
                  <Bot className="w-4 h-4 text-indigo-400" />
                  <span>Cursor Setup</span>
                </div>
                <p className="text-slate-400">
                  Save the compiled context pack into a file named <code className="text-indigo-300">.cursorrules</code> at the root of your repository. Cursor will automatically reference these architecture boundaries and constraints in every prompt.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                <div className="font-bold text-white text-sm flex items-center gap-2">
                  <Bot className="w-4 h-4 text-cyan-400" />
                  <span>Windsurf Setup</span>
                </div>
                <p className="text-slate-400">
                  Save the compiled context into <code className="text-cyan-300">.windsurfrules</code>. Windsurf Cascade will read the verified conventions and test commands automatically.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                <div className="font-bold text-white text-sm flex items-center gap-2">
                  <Bot className="w-4 h-4 text-purple-400" />
                  <span>Claude Code & Antigravity Setup</span>
                </div>
                <p className="text-slate-400">
                  Save the exported <code className="text-purple-300">AGENTS.md</code> or <code className="text-purple-300">CLAUDE.md</code> in your project root. Every agent session will load project memory without needing re-explanation!
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
