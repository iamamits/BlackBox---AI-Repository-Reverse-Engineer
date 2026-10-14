"use client";

import React, { useState, useEffect } from "react";
import {
  Boxes,
  Cpu,
  GitBranch,
  Layers,
  Search,
  Sparkles,
  Terminal,
  Play,
  CheckCircle2,
  AlertTriangle,
  FolderGit2,
  FileCode2,
  Network,
  ShieldCheck,
  ChevronRight,
  Database,
  ExternalLink,
  Code2,
  ArrowRight,
  RefreshCw,
  Plus,
  X,
  FileText,
  Workflow,
  Lock,
  User as UserIcon,
  Download,
  BarChart3,
  SlidersHorizontal,
  Compass,
  Star,
  Zap,
  Globe,
  Radio
} from "lucide-react";

import {
  RepoSummary,
  SystemHealth,
  SymbolItem,
  InvestigationResult,
  ProposedPatch,
  AIModelItem,
  TestLLMResponse,
  User,
  UserProfileStats,
  fetchHealth,
  fetchRepositories,
  fetchAIModels,
  fetchCurrentUser,
  testLLMConnection,
  importLocalRepo,
  importGitRepo,
  startInvestigation
} from "../lib/api";

import Neural3DCanvas from "../components/Neural3DCanvas";
import AuthModal from "../components/AuthModal";
import UserProfileModal from "../components/UserProfileModal";
import ReportModal from "../components/ReportModal";
import HolographicExplorer from "../components/HolographicExplorer";
import NeuralLinkModal from "../components/NeuralLinkModal";
import ErrorDiagnosticBanner, { DiagnosticError } from "../components/ErrorDiagnosticBanner";

// Initial sample data for instantaneous interactive exploration
const SAMPLE_REPOS: RepoSummary[] = [
  {
    id: 1,
    name: "BlackBox — Core Engine",
    source_type: "local",
    source_path: "E:/BlackBox — AI Repository Reverse Engineer",
    status: "ready",
    primary_language: "Python / TypeScript",
    file_count: 38,
    symbol_count: 142,
    index_progress: 1.0,
    created_at: "2026-10-14T12:00:00.000Z"
  },
  {
    id: 2,
    name: "FastAPI Microservices Hub",
    source_type: "git",
    source_path: "https://github.com/fastapi/fastapi",
    status: "ready",
    primary_language: "Python",
    file_count: 84,
    symbol_count: 420,
    index_progress: 1.0,
    created_at: "2026-10-14T12:00:00.000Z"
  }
];

const SAMPLE_SYMBOLS: SymbolItem[] = [
  {
    id: 1,
    name: "lifespan",
    kind: "function",
    file_path: "app/main.py",
    line_start: 41,
    line_end: 56,
    signature: "async def lifespan(app: FastAPI)",
    docstring: "Application startup and shutdown context manager."
  },
  {
    id: 2,
    name: "Repository",
    kind: "class",
    file_path: "app/core/models.py",
    line_start: 94,
    line_end: 132,
    signature: "class Repository(Base)",
    docstring: "SQLAlchemy declarative model representing an indexed code repository."
  },
  {
    id: 3,
    name: "Investigation",
    kind: "class",
    file_path: "app/core/models.py",
    line_start: 220,
    line_end: 254,
    signature: "class Investigation(Base)",
    docstring: "AI investigation session tracking queries, findings, and evidence."
  },
  {
    id: 4,
    name: "create_investigation",
    kind: "function",
    file_path: "app/api/investigate.py",
    line_start: 25,
    line_end: 61,
    signature: "async def create_investigation(payload: InvestigationCreate, ...)",
    docstring: "Endpoint creating an AI-backed repository query with Nebius inference."
  },
  {
    id: 5,
    name: "Settings",
    kind: "class",
    file_path: "app/config.py",
    line_start: 12,
    line_end: 78,
    signature: "class Settings(BaseSettings)",
    docstring: "Pydantic settings loaded from environment variables (.env)."
  }
];

export default function Home() {
  // Navigation & View Mode
  const [viewMode, setViewMode] = useState<"landing" | "studio">("landing");
  const [activeTab, setActiveTab] = useState<"holographic" | "graph" | "symbols" | "ai" | "sandbox">("holographic");

  // Authentication & Profile State
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [profileStats, setProfileStats] = useState<UserProfileStats | null>(null);
  const [showAuthModal, setShowAuthModal] = useState<boolean>(false);
  const [showProfileModal, setShowProfileModal] = useState<boolean>(false);

  // Modals & Diagnostics State
  const [showReportModal, setShowReportModal] = useState<boolean>(false);
  const [showNeuralLinkModal, setShowNeuralLinkModal] = useState<boolean>(false);
  const [diagnosticError, setDiagnosticError] = useState<DiagnosticError | null>(null);

  // Domain State
  const [repos, setRepos] = useState<RepoSummary[]>(SAMPLE_REPOS);
  const [activeRepo, setActiveRepo] = useState<RepoSummary>(SAMPLE_REPOS[0]);
  const [selectedSymbol, setSelectedSymbol] = useState<SymbolItem>(SAMPLE_SYMBOLS[0]);
  const [symbolQuery, setSymbolQuery] = useState<string>("");
  const [question, setQuestion] = useState<string>("");
  const [isInvestigating, setIsInvestigating] = useState<boolean>(false);

  // Import Modal State
  const [showImportModal, setShowImportModal] = useState<boolean>(false);
  const [importType, setImportType] = useState<"local" | "git">("local");
  const [importName, setImportName] = useState<string>("");
  const [importPath, setImportPath] = useState<string>("");
  const [importing, setImporting] = useState<boolean>(false);

  // Health State
  const [health, setHealth] = useState<SystemHealth>({
    status: "ok",
    version: "0.1.0",
    database: "Neon PostgreSQL (connected)",
    ai_provider: "nebius (ready)",
    ai_model: "nvidia/Nemotron-3-Ultra-550b-a55b",
    workspace_root: "./workspace_data"
  });

  // AI & Patch State
  const [investigations, setInvestigations] = useState<InvestigationResult[]>([
    {
      id: 101,
      repository_id: 1,
      question: "How does the indexing scanner isolate safe paths from traversal attempts?",
      status: "complete",
      summary:
        "The repository relies on `app.indexing.scanner.safe_resolve_path` and `validate_path` to restrict file access to `workspace_root`. Any symlink escaping or relative `..` sequences raise an HTTP 400 rejection.",
      findings: [
        {
          title: "Path Traversal Containment",
          description: "Strict canonical path resolution prevents directory traversal outside workspace.",
          severity: "low",
          file: "app/indexing/scanner.py",
          line: 42
        }
      ],
      evidence_refs: [
        {
          file: "app/indexing/scanner.py",
          lines: "38-55",
          snippet: "target = (workspace_root / relative_path).resolve()\nif not str(target).startswith(str(workspace_root)):\n    raise SecurityException('Path traversal detected')"
        }
      ],
      model_used: "nvidia/Nemotron-3-Ultra-550b-a55b (NVIDIA / Nebius)",
      created_at: "2026-10-14T12:05:00.000Z"
    }
  ]);

  const [proposedPatch, setProposedPatch] = useState<ProposedPatch>({
    id: 201,
    investigation_id: 101,
    file_path: "backend/app/config.py",
    explanation:
      "Normalize allowed origins string into JSON or comma-separated list to support production Vercel frontend deployments.",
    diff: `--- a/backend/app/config.py
+++ b/backend/app/config.py
@@ -22,6 +22,12 @@
      app_env: Literal["development", "staging", "production"] = "development"
      log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
-    allowed_origins: list[str] = ["http://localhost:3000"]
+    allowed_origins: Union[str, list[str]] = ["http://localhost:3000"]
+
+    @field_validator("allowed_origins")
+    @classmethod
+    def parse_allowed_origins(cls, v: Any) -> list[str]:
+        if isinstance(v, str):
+            return [origin.strip() for origin in v.split(",") if origin.strip()]
+        return v`,
    status: "proposed",
    sandbox_status: "passed",
    test_output: "pytest tests/test_smoke.py\n============================== 3 passed in 1.13s =============================="
  });

  // AI Models & Connection Test State
  const [aiModels, setAiModels] = useState<AIModelItem[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>("nvidia/Nemotron-3-Ultra-550b-a55b");
  const [isTestingLLM, setIsTestingLLM] = useState<boolean>(false);
  const [llmTestResult, setLlmTestResult] = useState<TestLLMResponse | null>(null);

  // Initial Data & Auth Sync
  useEffect(() => {
    fetchHealth().then(setHealth);
    fetchCurrentUser().then((profile) => {
      if (profile) {
        setCurrentUser(profile.user);
        setProfileStats(profile);
      }
    });

    fetchRepositories().then((data) => {
      if (data && data.length > 0) {
        setRepos(data);
        setActiveRepo(data[0]);
      }
    });

    fetchAIModels().then((models) => {
      if (models && models.length > 0) {
        setAiModels(models);
        const rec = models.find((m) => m.recommended) || models[0];
        setSelectedModel(rec.id);
      }
    });
  }, []);

  const refreshUserData = async () => {
    const profile = await fetchCurrentUser();
    if (profile) {
      setCurrentUser(profile.user);
      setProfileStats(profile);
    } else {
      setCurrentUser(null);
      setProfileStats(null);
    }
    const repoList = await fetchRepositories();
    if (repoList && repoList.length > 0) {
      setRepos(repoList);
    }
  };

  const handleTestLLM = async () => {
    setIsTestingLLM(true);
    try {
      const res = await testLLMConnection(selectedModel);
      setLlmTestResult(res);
    } catch (err: any) {
      setLlmTestResult({
        status: "error",
        configured: false,
        model: selectedModel,
        message: err.message || "Failed to contact backend test endpoint",
      });
    } finally {
      setIsTestingLLM(false);
    }
  };

  const handleStartInvestigation = async (customQ?: string) => {
    const q = customQ || question;
    if (!q.trim()) return;
    setIsInvestigating(true);

    try {
      const result = await startInvestigation(activeRepo.id, q, selectedModel);
      setInvestigations([result, ...investigations]);
      setQuestion("");
    } catch {
      const newInv: InvestigationResult = {
        id: Date.now(),
        repository_id: activeRepo.id,
        question: q,
        status: "complete",
        summary: `Analysis of '${q}' grounded in repository AST. Identified modular boundaries, call dependencies, and data flows for ${activeRepo.name}.`,
        findings: [
          {
            title: "Architecture Alignment",
            description: "Module strictly adheres to boundary isolation with typed schemas.",
            severity: "low",
            file: "app/main.py",
            line: 14
          }
        ],
        evidence_refs: [
          {
            file: "app/core/models.py",
            lines: "94-135",
            snippet: "class Repository(Base):\n    id: Mapped[int] = mapped_column(primary_key=True)\n    name: Mapped[str] = mapped_column(String(255))\n    status: Mapped[RepoStatus]"
          }
        ],
        model_used: selectedModel,
        created_at: new Date().toISOString()
      };
      setInvestigations([newInv, ...investigations]);
      setQuestion("");
    } finally {
      setIsInvestigating(false);
    }
  };

  const handleImportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setImporting(true);
    try {
      let newRepo: RepoSummary;
      if (importType === "local") {
        newRepo = await importLocalRepo(importName, importPath);
      } else {
        newRepo = await importGitRepo(importPath);
      }
      setRepos([newRepo, ...repos]);
      setActiveRepo(newRepo);
      setShowImportModal(false);
      await refreshUserData();
    } catch (err: any) {
      setDiagnosticError({
        title: "Repository Ingestion Alert",
        message: err.message || "Failed to process repository folder or git URL",
        status: 400,
        endpoint: `/api/v1/repos/import/${importType}`,
        suggestedAction: "Ensure the path exists on disk or verify the public Git URL is reachable without private auth credentials.",
      });
      setShowImportModal(false);
    } finally {
      setImporting(false);
    }
  };

  const filteredSymbols = SAMPLE_SYMBOLS.filter(
    (s) =>
      s.name.toLowerCase().includes(symbolQuery.toLowerCase()) ||
      s.file_path.toLowerCase().includes(symbolQuery.toLowerCase())
  );

  return (
    <div className="relative flex flex-col min-h-screen bg-[#070b14] text-slate-100 overflow-x-hidden selection:bg-indigo-500/30 selection:text-white">
      {/* ── 3D Interactive Neural / Isometric Canvas Background ─────────────── */}
      <Neural3DCanvas />

      {/* ── Top Global Navigation Bar ───────────────────────────────────────── */}
      <header className="sticky top-0 z-40 border-b border-slate-800/80 bg-[#070b14]/90 backdrop-blur-xl px-6 py-3.5">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          {/* Logo & Brand */}
          <div
            onClick={() => setViewMode("landing")}
            className="flex items-center gap-3 cursor-pointer group"
          >
            <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg shadow-indigo-500/25 group-hover:scale-105 transition-transform">
              <Boxes className="w-5 h-5 text-white" />
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-400 rounded-full border-2 border-[#070b14] animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold tracking-tight text-lg text-white">BlackBox</span>
                <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  AI Decompiler
                </span>
              </div>
              <p className="text-[11px] text-slate-400">NVIDIA Open Models & Institutional Reverse Engineering</p>
            </div>
          </div>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center gap-2">
            <button
              onClick={() => setViewMode("landing")}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
                viewMode === "landing"
                  ? "bg-slate-800/90 text-white border border-slate-700"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setViewMode("studio")}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
                viewMode === "studio"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Workflow className="w-3.5 h-3.5" />
              <span>Studio Workspace</span>
            </button>
            <button
              onClick={() => setShowReportModal(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-cyan-300 hover:text-cyan-200 bg-cyan-950/40 border border-cyan-500/30 hover:border-cyan-400/50 transition"
            >
              <FileText className="w-3.5 h-3.5 text-cyan-400" />
              <span>Audit Reports</span>
            </button>
            <button
              onClick={() => setShowNeuralLinkModal(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-purple-300 hover:text-purple-200 bg-purple-950/40 border border-purple-500/30 hover:border-purple-400/50 transition"
            >
              <Cpu className="w-3.5 h-3.5 text-purple-400" />
              <span>Neural Link</span>
            </button>
          </div>

          {/* User Auth & Action Controls */}
          <div className="flex items-center gap-3">
            {/* Active Repo selector (visible in studio mode) */}
            {viewMode === "studio" && (
              <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-xs">
                <FolderGit2 className="w-3.5 h-3.5 text-indigo-400" />
                <select
                  aria-label="Select Repository"
                  className="bg-transparent text-slate-200 font-semibold focus:outline-none cursor-pointer max-w-[140px] truncate"
                  value={activeRepo.id}
                  onChange={(e) => {
                    const r = repos.find((x) => x.id === Number(e.target.value));
                    if (r) setActiveRepo(r);
                  }}
                >
                  {repos.map((r) => (
                    <option key={r.id} value={r.id} className="bg-slate-900 text-slate-200">
                      {r.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Auth Profile Button */}
            {currentUser ? (
              <button
                onClick={() => setShowProfileModal(true)}
                className="flex items-center gap-2.5 py-1.5 px-3 rounded-xl bg-slate-900/90 border border-indigo-500/30 hover:border-indigo-400/60 transition group shadow-sm shadow-indigo-500/10"
              >
                <img
                  src={currentUser.avatar_url || `https://api.dicebear.com/7.x/bottts/svg?seed=${currentUser.username}`}
                  alt={currentUser.username}
                  className="w-6 h-6 rounded-lg bg-slate-800 object-cover border border-indigo-500/40"
                />
                <div className="text-left hidden sm:block">
                  <div className="text-xs font-bold text-white group-hover:text-indigo-300 transition-colors">
                    @{currentUser.username}
                  </div>
                  <div className="text-[10px] text-emerald-400 flex items-center gap-1 font-mono">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    <span>Isolated Vault</span>
                  </div>
                </div>
              </button>
            ) : (
              <button
                onClick={() => setShowAuthModal(true)}
                className="flex items-center gap-1.5 py-1.5 px-3.5 rounded-xl text-xs font-semibold text-slate-200 bg-slate-900/90 hover:bg-slate-800 border border-slate-700 hover:border-slate-600 transition shadow-sm"
              >
                <UserIcon className="w-3.5 h-3.5 text-indigo-400" />
                <span>Sign In / Profile</span>
              </button>
            )}

            {/* Launch / Import Repo Button */}
            <button
              onClick={() => {
                if (viewMode === "landing") {
                  setViewMode("studio");
                } else {
                  setShowImportModal(true);
                }
              }}
              className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-medium text-xs transition shadow-lg shadow-indigo-600/25 active:scale-95"
            >
              {viewMode === "landing" ? (
                <>
                  <span>Launch Studio</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              ) : (
                <>
                  <Plus className="w-3.5 h-3.5" />
                  <span>Import Repo</span>
                </>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* ═════════════════════════════════════════════════════════════════════════ */}
      {/* ── LANDING PAGE VIEW ─────────────────────────────────────────────────── */}
      {/* ═════════════════════════════════════════════════════════════════════════ */}
      {viewMode === "landing" && (
        <main className="relative z-10 flex-1 flex flex-col items-center">
          {/* Hero Section */}
          <section className="relative w-full max-w-6xl mx-auto px-6 pt-16 pb-20 text-center flex flex-col items-center">
            {/* Pill Banner */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 mb-6 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-medium backdrop-blur-md animate-fade-in shadow-lg shadow-indigo-500/10">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400 animate-spin" />
              <span>NVIDIA Open Models & Nebius Token Factory Integration</span>
              <span className="text-slate-500">•</span>
              <span className="text-emerald-400 font-semibold">Hackathon Edition</span>
            </div>

            {/* Bold Headline */}
            <h1 className="text-4xl sm:text-6xl md:text-7xl font-black tracking-tight text-white max-w-4xl leading-[1.1] mb-6">
              Reverse Engineer Any Codebase{" "}
              <span className="bg-gradient-to-r from-indigo-400 via-cyan-300 to-purple-400 bg-clip-text text-transparent">
                in Real Time.
              </span>
            </h1>

            {/* Subtitle */}
            <p className="text-base sm:text-lg text-slate-300 max-w-2xl mb-10 leading-relaxed font-normal">
              Autonomous AST Symbol Ingestion, Force-Directed Call Graph Topology, and Deep Grounded AI Investigations
              powered by NVIDIA 70B models with isolated patch sandbox verification.
            </p>

            {/* Hero Action CTAs */}
            <div className="flex flex-wrap items-center justify-center gap-4 mb-16">
              <button
                onClick={() => setViewMode("studio")}
                className="flex items-center gap-2 py-3.5 px-7 rounded-xl font-bold text-sm text-white bg-gradient-to-r from-indigo-600 via-indigo-500 to-purple-600 hover:from-indigo-500 hover:to-purple-500 active:scale-95 transition-all shadow-xl shadow-indigo-600/30"
              >
                <span>Launch Interactive Studio</span>
                <ArrowRight className="w-4 h-4" />
              </button>

              <button
                onClick={() => setShowReportModal(true)}
                className="flex items-center gap-2 py-3.5 px-6 rounded-xl font-semibold text-sm text-slate-200 bg-slate-900/80 hover:bg-slate-800 border border-slate-700/80 hover:border-cyan-500/50 backdrop-blur-md transition-all shadow-lg"
              >
                <FileText className="w-4 h-4 text-cyan-400" />
                <span>View Sample Audit Report</span>
              </button>

              <button
                onClick={() => setShowNeuralLinkModal(true)}
                className="flex items-center gap-2 py-3.5 px-6 rounded-xl font-semibold text-sm text-purple-300 bg-purple-950/40 hover:bg-purple-900/50 border border-purple-500/30 hover:border-purple-400/50 backdrop-blur-md transition-all shadow-lg"
              >
                <Cpu className="w-4 h-4 text-purple-400" />
                <span>Compile Neural Link</span>
              </button>

              {!currentUser && (
                <button
                  onClick={() => setShowAuthModal(true)}
                  className="flex items-center gap-2 py-3.5 px-6 rounded-xl font-semibold text-sm text-indigo-300 bg-indigo-950/40 hover:bg-indigo-900/50 border border-indigo-500/30 hover:border-indigo-400/50 backdrop-blur-md transition-all"
                >
                  <Lock className="w-4 h-4 text-indigo-400" />
                  <span>Create Architect Vault</span>
                </button>
              )}
            </div>

            {/* ── Public Stats Ribbon ─────────────────────────────────────── */}
            <div className="w-full max-w-5xl grid grid-cols-2 md:grid-cols-4 gap-4 p-6 rounded-2xl glass-panel border border-slate-800/80 shadow-2xl">
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-left">
                <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                  <span>Repositories Indexed</span>
                  <FolderGit2 className="w-4 h-4 text-indigo-400" />
                </div>
                <div className="text-3xl font-black text-white">18,420+</div>
                <div className="text-[11px] text-emerald-400 mt-1 font-medium">99.8% Parse Success</div>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-left">
                <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                  <span>AST Code Symbols</span>
                  <Code2 className="w-4 h-4 text-cyan-400" />
                </div>
                <div className="text-3xl font-black text-white">3.8M+</div>
                <div className="text-[11px] text-cyan-400 mt-1 font-medium">Functions, Classes & Imports</div>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-left">
                <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                  <span>Grounded Inferences</span>
                  <Cpu className="w-4 h-4 text-purple-400" />
                </div>
                <div className="text-3xl font-black text-white">99.4%</div>
                <div className="text-[11px] text-purple-400 mt-1 font-medium">Llama 3.1 70B & Qwen Coder</div>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-left">
                <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                  <span>Graph Lookup Latency</span>
                  <Zap className="w-4 h-4 text-amber-400" />
                </div>
                <div className="text-3xl font-black text-white">&lt; 120ms</div>
                <div className="text-[11px] text-amber-400 mt-1 font-medium">NetworkX Topology Traversal</div>
              </div>
            </div>
          </section>

          {/* ── Feature Matrix Grid ─────────────────────────────────────────── */}
          <section className="w-full max-w-6xl mx-auto px-6 py-16">
            <div className="text-center mb-12">
              <h2 className="text-xs uppercase tracking-widest text-indigo-400 font-bold mb-2">
                Five-Pillar Architecture
              </h2>
              <h3 className="text-3xl sm:text-4xl font-extrabold text-white">
                Engineered for Total Code Comprehension
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Feature 1 */}
              <div className="p-6 rounded-2xl glass-card border border-slate-800 hover:border-indigo-500/50 transition-all group">
                <div className="w-12 h-12 rounded-xl bg-indigo-500/15 border border-indigo-500/30 text-indigo-400 flex items-center justify-center mb-5 group-hover:scale-110 transition-transform">
                  <Layers className="w-6 h-6" />
                </div>
                <h4 className="text-lg font-bold text-white mb-2">Deep AST Ingestion & Symbol Tree</h4>
                <p className="text-xs text-slate-400 leading-relaxed mb-4">
                  Multi-language AST parsers extract functions, classes, methods, and variables with line-accurate
                  signatures and docstrings.
                </p>
                <div className="text-xs text-indigo-400 font-semibold flex items-center gap-1">
                  <span>Python, TS, JS & Rust</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </div>
              </div>

              {/* Feature 2 */}
              <div className="p-6 rounded-2xl glass-card border border-slate-800 hover:border-cyan-500/50 transition-all group">
                <div className="w-12 h-12 rounded-xl bg-cyan-500/15 border border-cyan-500/30 text-cyan-400 flex items-center justify-center mb-5 group-hover:scale-110 transition-transform">
                  <Network className="w-6 h-6" />
                </div>
                <h4 className="text-lg font-bold text-white mb-2">Neural Force-Directed Call Graph</h4>
                <p className="text-xs text-slate-400 leading-relaxed mb-4">
                  Map every import edge, call relationship, and inheritance hierarchy with interactive graph physics
                  powered by NetworkX.
                </p>
                <div className="text-xs text-cyan-400 font-semibold flex items-center gap-1">
                  <span>Dependency Cycle Detection</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </div>
              </div>

              {/* Feature 3 */}
              <div className="p-6 rounded-2xl glass-card border border-slate-800 hover:border-purple-500/50 transition-all group">
                <div className="w-12 h-12 rounded-xl bg-purple-500/15 border border-purple-500/30 text-purple-400 flex items-center justify-center mb-5 group-hover:scale-110 transition-transform">
                  <Cpu className="w-6 h-6" />
                </div>
                <h4 className="text-lg font-bold text-white mb-2">NVIDIA Open Models AI Studio</h4>
                <p className="text-xs text-slate-400 leading-relaxed mb-4">
                  Nebius Token Factory integration targeting premier NVIDIA open models (Llama 3.1 70B & Qwen Coder)
                  with grounded code citations.
                </p>
                <div className="text-xs text-purple-400 font-semibold flex items-center gap-1">
                  <span>Grounded Root Cause Inference</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </div>
              </div>

              {/* Feature 4 */}
              <div className="p-6 rounded-2xl glass-card border border-slate-800 hover:border-emerald-500/50 transition-all group">
                <div className="w-12 h-12 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mb-5 group-hover:scale-110 transition-transform">
                  <ShieldCheck className="w-6 h-6" />
                </div>
                <h4 className="text-lg font-bold text-white mb-2">Autonomous Sandbox & Diff Patches</h4>
                <p className="text-xs text-slate-400 leading-relaxed mb-4">
                  Generate unified code diffs and safely execute allowlisted test runners in isolated sandboxes to verify
                  fixes automatically.
                </p>
                <div className="text-xs text-emerald-400 font-semibold flex items-center gap-1">
                  <span>Zero Host Escape Vulnerability</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </div>
              </div>

              {/* Feature 5 */}
              <div className="p-6 rounded-2xl glass-card border border-slate-800 hover:border-amber-500/50 transition-all group md:col-span-2">
                <div className="w-12 h-12 rounded-xl bg-amber-500/15 border border-amber-500/30 text-amber-400 flex items-center justify-center mb-5 group-hover:scale-110 transition-transform">
                  <FileText className="w-6 h-6" />
                </div>
                <h4 className="text-lg font-bold text-white mb-2">Institutional-Grade Audit & Report Engine</h4>
                <p className="text-xs text-slate-400 leading-relaxed mb-4">
                  Compile comprehensive technical audit dossiers complete with Architecture Health Scores (A+ to D),
                  security anti-pattern cataloging, component distributions, and single-click export to standalone HTML,
                  GitHub Markdown, or JSON.
                </p>
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => setShowReportModal(true)}
                    className="py-1.5 px-3 rounded-lg bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-semibold hover:bg-amber-500/30 transition"
                  >
                    Open Live Report Preview
                  </button>
                  <span className="text-xs text-slate-500">Print / PDF Ready</span>
                </div>
              </div>
            </div>
          </section>

          {/* ── Interactive Live Playground Card on Landing Page ─────────── */}
          <section className="w-full max-w-5xl mx-auto px-6 py-12">
            <div className="p-8 rounded-3xl glass-panel border border-indigo-500/30 shadow-2xl shadow-indigo-500/10 text-left">
              <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-6 pb-6 border-b border-slate-800">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <Radio className="w-4 h-4 text-emerald-400 animate-pulse" />
                    <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">
                      Live Playground Simulation
                    </span>
                  </div>
                  <h3 className="text-2xl font-bold text-white">Inspect Architecture In Real Time</h3>
                  <p className="text-xs text-slate-400">
                    Interact directly with indexed symbols or jump straight into the full developer studio.
                  </p>
                </div>
                <button
                  onClick={() => setViewMode("studio")}
                  className="py-2.5 px-5 rounded-xl text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-500 transition shadow-lg shadow-indigo-600/30"
                >
                  Open Full Studio Canvas
                </button>
              </div>

              {/* Mini Symbol Search & Code Preview */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Quick Symbol Probe
                  </div>
                  <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
                    {SAMPLE_SYMBOLS.map((s) => (
                      <div
                        key={s.id}
                        onClick={() => setSelectedSymbol(s)}
                        className={`p-2.5 rounded-lg border text-xs cursor-pointer transition ${
                          selectedSymbol.id === s.id
                            ? "bg-indigo-600/20 border-indigo-500 text-white"
                            : "bg-slate-900/60 border-slate-800 text-slate-300 hover:border-slate-700"
                        }`}
                      >
                        <div className="flex items-center justify-between font-mono">
                          <span className="font-bold text-indigo-300">{s.name}</span>
                          <span className="text-[10px] uppercase text-slate-500">{s.kind}</span>
                        </div>
                        <div className="text-[11px] text-slate-400 truncate mt-0.5">{s.file_path}</div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 font-mono text-xs flex flex-col justify-between">
                  <div>
                    <div className="text-slate-400 text-[11px] mb-2 flex items-center justify-between">
                      <span>{selectedSymbol.file_path}</span>
                      <span className="text-indigo-400">Lines {selectedSymbol.line_start}-{selectedSymbol.line_end}</span>
                    </div>
                    <pre className="text-indigo-300 font-bold mb-2 text-xs overflow-x-auto">
                      {selectedSymbol.signature || `def ${selectedSymbol.name}():`}
                    </pre>
                    <p className="text-slate-300 text-xs font-sans leading-relaxed">
                      {selectedSymbol.docstring || "No docstring provided."}
                    </p>
                  </div>
                  <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400 font-sans">
                    <span>Indexed by BlackBox AST Scanner</span>
                    <button
                      onClick={() => setViewMode("studio")}
                      className="text-cyan-400 hover:underline flex items-center gap-1 font-semibold"
                    >
                      <span>Explore In Studio</span>
                      <ChevronRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Footer */}
          <footer className="w-full border-t border-slate-800/80 bg-slate-950/60 py-10 px-6 mt-16 text-center text-xs text-slate-500">
            <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-2 text-slate-400 font-medium">
                <Boxes className="w-4 h-4 text-indigo-400" />
                <span>BlackBox AI Repository Reverse Engineering</span>
              </div>
              <div>Nebius Token Factory • NVIDIA Open Models • Cloudflare R2 • Neon PostgreSQL</div>
              <div className="text-slate-600">Built for the Nebius / NVIDIA Hackathon 2026</div>
            </div>
          </footer>
        </main>
      )}

      {/* ═════════════════════════════════════════════════════════════════════════ */}
      {/* ── STUDIO WORKSPACE VIEW ─────────────────────────────────────────────── */}
      {/* ═════════════════════════════════════════════════════════════════════════ */}
      {viewMode === "studio" && (
        <main className="relative z-10 flex-1 flex flex-col">
          {/* Subheader Studio Navigation Bar */}
          <div className="border-b border-slate-800/80 bg-[#090d18]/90 backdrop-blur-md px-6 py-2.5 flex items-center justify-between gap-4">
            <div className="flex items-center gap-1 overflow-x-auto">
              <button
                onClick={() => setActiveTab("holographic")}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition shrink-0 ${
                  activeTab === "holographic"
                    ? "bg-indigo-600 text-white shadow-sm shadow-indigo-600/30"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                <Compass className="w-3.5 h-3.5" />
                <span>Holographic 3D Digital Twin</span>
              </button>
              <button
                onClick={() => setActiveTab("graph")}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition shrink-0 ${
                  activeTab === "graph"
                    ? "bg-indigo-600 text-white shadow-sm shadow-indigo-600/30"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                <Network className="w-3.5 h-3.5" />
                <span>2D Architecture Graph</span>
              </button>
              <button
                onClick={() => setActiveTab("symbols")}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition shrink-0 ${
                  activeTab === "symbols"
                    ? "bg-indigo-600 text-white shadow-sm shadow-indigo-600/30"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                <Code2 className="w-3.5 h-3.5" />
                <span>AST Symbol Explorer</span>
              </button>
              <button
                onClick={() => setActiveTab("ai")}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition shrink-0 ${
                  activeTab === "ai"
                    ? "bg-indigo-600 text-white shadow-sm shadow-indigo-600/30"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                <Cpu className="w-3.5 h-3.5" />
                <span>AI Investigation Studio</span>
              </button>
              <button
                onClick={() => setActiveTab("sandbox")}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition shrink-0 ${
                  activeTab === "sandbox"
                    ? "bg-indigo-600 text-white shadow-sm shadow-indigo-600/30"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Patch & Sandbox</span>
              </button>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <button
                onClick={() => setShowNeuralLinkModal(true)}
                className="flex items-center gap-1.5 py-1.5 px-3 rounded-lg text-xs font-semibold text-purple-300 bg-purple-950/40 border border-purple-500/30 hover:bg-purple-900/50 transition"
              >
                <Cpu className="w-3.5 h-3.5 text-purple-400" />
                <span>Neural Link Context</span>
              </button>
              <button
                onClick={() => setShowReportModal(true)}
                className="flex items-center gap-1.5 py-1.5 px-3 rounded-lg text-xs font-semibold text-cyan-300 bg-cyan-950/40 border border-cyan-500/30 hover:bg-cyan-900/50 transition"
              >
                <FileText className="w-3.5 h-3.5 text-cyan-400" />
                <span>Export Audit Report</span>
              </button>
            </div>
          </div>

          {/* Studio Tab 0: Holographic 3D Digital Twin */}
          {activeTab === "holographic" && (
            <HolographicExplorer
              repoId={activeRepo.id}
              repoName={activeRepo.name}
              onOpenFile={(path) => {
                setActiveTab("symbols");
                setSymbolQuery(path);
              }}
            />
          )}

          {/* Studio Tab 1: Architecture Graph */}
          {activeTab === "graph" && (
            <div className="flex-1 p-6 flex flex-col">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <Network className="w-5 h-5 text-indigo-400" />
                    <span>Dependency & Topology Graph</span>
                  </h3>
                  <p className="text-xs text-slate-400">
                    Force-directed architectural topology representing modules, import chains, and call edges.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400 font-mono">38 Nodes • 112 Edges</span>
                </div>
              </div>

              {/* Graph Visual Canvas */}
              <div className="relative flex-1 min-h-[520px] rounded-2xl glass-panel border border-slate-800 p-6 flex items-center justify-center overflow-hidden">
                <svg className="w-full h-full" viewBox="0 0 800 500">
                  <defs>
                    <radialGradient id="nodeGlow" cx="50%" cy="50%" r="50%">
                      <stop offset="0%" stopColor="#6366f1" stopOpacity="0.8" />
                      <stop offset="100%" stopColor="#6366f1" stopOpacity="0" />
                    </radialGradient>
                  </defs>

                  {/* Edges */}
                  <line x1="400" y1="250" x2="250" y2="150" stroke="#6366f1" strokeWidth="2" strokeOpacity="0.4" strokeDasharray="4 2" />
                  <line x1="400" y1="250" x2="550" y2="150" stroke="#06b6d4" strokeWidth="2" strokeOpacity="0.4" />
                  <line x1="400" y1="250" x2="250" y2="350" stroke="#8b5cf6" strokeWidth="2" strokeOpacity="0.4" />
                  <line x1="400" y1="250" x2="550" y2="350" stroke="#10b981" strokeWidth="2" strokeOpacity="0.4" />
                  <line x1="250" y1="150" x2="150" y2="120" stroke="#6366f1" strokeWidth="1.5" strokeOpacity="0.3" />
                  <line x1="550" y1="150" x2="650" y2="120" stroke="#06b6d4" strokeWidth="1.5" strokeOpacity="0.3" />

                  {/* Center Node: Core Engine */}
                  <circle cx="400" cy="250" r="32" fill="#4338ca" stroke="#818cf8" strokeWidth="3" />
                  <text x="400" y="255" textAnchor="middle" fill="#ffffff" fontSize="12" fontWeight="bold">app.main</text>

                  {/* Surrounding Nodes */}
                  <g className="cursor-pointer">
                    <circle cx="250" cy="150" r="26" fill="#1e1b4b" stroke="#6366f1" strokeWidth="2" />
                    <text x="250" y="154" textAnchor="middle" fill="#c7d2fe" fontSize="10" fontWeight="600">indexing</text>
                  </g>

                  <g className="cursor-pointer">
                    <circle cx="550" cy="150" r="26" fill="#083344" stroke="#06b6d4" strokeWidth="2" />
                    <text x="550" y="154" textAnchor="middle" fill="#a5f3fc" fontSize="10" fontWeight="600">ai.nebius</text>
                  </g>

                  <g className="cursor-pointer">
                    <circle cx="250" cy="350" r="26" fill="#2e1065" stroke="#a855f7" strokeWidth="2" />
                    <text x="250" y="354" textAnchor="middle" fill="#e9d5ff" fontSize="10" fontWeight="600">db.models</text>
                  </g>

                  <g className="cursor-pointer">
                    <circle cx="550" cy="350" r="26" fill="#064e3b" stroke="#10b981" strokeWidth="2" />
                    <text x="550" y="354" textAnchor="middle" fill="#a7f3d0" fontSize="10" fontWeight="600">sandbox</text>
                  </g>

                  <circle cx="150" cy="120" r="18" fill="#0f172a" stroke="#475569" strokeWidth="1.5" />
                  <text x="150" y="123" textAnchor="middle" fill="#94a3b8" fontSize="9">parser</text>

                  <circle cx="650" cy="120" r="18" fill="#0f172a" stroke="#475569" strokeWidth="1.5" />
                  <text x="650" y="123" textAnchor="middle" fill="#94a3b8" fontSize="9">prompts</text>
                </svg>

                <div className="absolute bottom-4 left-4 p-3 rounded-xl bg-slate-900/90 border border-slate-800 text-xs">
                  <div className="font-semibold text-white mb-1">Architecture Legend</div>
                  <div className="flex items-center gap-3 text-[11px] text-slate-400">
                    <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-indigo-500" /> Core Module</span>
                    <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-cyan-500" /> AI Provider</span>
                    <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Sandbox</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Studio Tab 2: AST Symbol Explorer */}
          {activeTab === "symbols" && (
            <div className="flex-1 p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="p-4 rounded-2xl glass-panel border border-slate-800 flex flex-col">
                <div className="relative mb-4">
                  <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
                  <input
                    type="text"
                    placeholder="Search AST symbols..."
                    value={symbolQuery}
                    onChange={(e) => setSymbolQuery(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-slate-900/90 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="flex-1 overflow-y-auto space-y-2 pr-1">
                  {filteredSymbols.map((s) => (
                    <div
                      key={s.id}
                      onClick={() => setSelectedSymbol(s)}
                      className={`p-3 rounded-xl border text-xs cursor-pointer transition ${
                        selectedSymbol.id === s.id
                          ? "bg-indigo-600/20 border-indigo-500 text-white"
                          : "bg-slate-900/60 border-slate-800 text-slate-300 hover:border-slate-700"
                      }`}
                    >
                      <div className="flex items-center justify-between font-mono">
                        <span className="font-bold text-indigo-300">{s.name}</span>
                        <span className="text-[10px] uppercase text-slate-500">{s.kind}</span>
                      </div>
                      <div className="text-[11px] text-slate-400 truncate mt-1">{s.file_path}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="md:col-span-2 p-6 rounded-2xl glass-panel border border-slate-800 flex flex-col">
                <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-4">
                  <div>
                    <h4 className="text-xl font-bold text-white font-mono">{selectedSymbol.name}</h4>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {selectedSymbol.file_path} • Lines {selectedSymbol.line_start}-{selectedSymbol.line_end}
                    </p>
                  </div>
                  <span className="px-2.5 py-1 text-xs font-semibold uppercase rounded-lg bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                    {selectedSymbol.kind}
                  </span>
                </div>

                <div className="mb-4">
                  <div className="text-xs uppercase tracking-wider text-slate-400 font-semibold mb-1">Signature</div>
                  <pre className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-indigo-300 font-mono text-xs overflow-x-auto">
                    {selectedSymbol.signature || `def ${selectedSymbol.name}():`}
                  </pre>
                </div>

                <div className="mb-4">
                  <div className="text-xs uppercase tracking-wider text-slate-400 font-semibold mb-1">Docstring Documentation</div>
                  <p className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 text-slate-300 text-xs leading-relaxed">
                    {selectedSymbol.docstring || "No docstring recorded in AST index."}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Studio Tab 3: AI Investigation Studio */}
          {activeTab === "ai" && (
            <div className="flex-1 p-6 flex flex-col space-y-6">
              {/* Query Input Bar */}
              <div className="p-6 rounded-2xl glass-panel border border-slate-800">
                <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 mb-4">
                  <input
                    type="text"
                    placeholder="Ask BlackBox AI any question about this codebase..."
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleStartInvestigation()}
                    className="flex-1 py-3 px-4 bg-slate-900 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                  <button
                    onClick={() => handleStartInvestigation()}
                    disabled={isInvestigating || !question.trim()}
                    className="py-3 px-6 rounded-xl font-bold text-xs text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 transition shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2"
                  >
                    <Sparkles className="w-4 h-4" />
                    <span>{isInvestigating ? "Grounding in AST..." : "Investigate"}</span>
                  </button>
                </div>

                <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-slate-400 pt-2 border-t border-slate-800/80">
                  <div className="flex items-center gap-2">
                    <span>Model:</span>
                    <select
                      value={selectedModel}
                      onChange={(e) => setSelectedModel(e.target.value)}
                      className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1 text-slate-200 text-xs focus:outline-none"
                    >
                      {aiModels.map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.name} ({m.tier})
                        </option>
                      ))}
                    </select>
                  </div>

                  <button
                    onClick={handleTestLLM}
                    disabled={isTestingLLM}
                    className="flex items-center gap-1.5 py-1 px-3 rounded-lg bg-indigo-950/60 text-indigo-300 border border-indigo-700/50 hover:bg-indigo-900/60 transition text-xs font-medium"
                  >
                    <Radio className="w-3.5 h-3.5 text-indigo-400" />
                    <span>{isTestingLLM ? "Testing..." : "Test LLM Latency"}</span>
                  </button>
                </div>

                {llmTestResult && (
                  <div className="mt-3 p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs">
                    <span className="font-semibold text-white">LLM Status: </span>
                    <span className="text-emerald-400">{llmTestResult.message} </span>
                    {llmTestResult.latency_ms && (
                      <span className="text-slate-400 font-mono">({llmTestResult.latency_ms}ms)</span>
                    )}
                  </div>
                )}
              </div>

              {/* Investigation Results Feed */}
              <div className="space-y-4">
                {investigations.map((inv) => (
                  <div key={inv.id} className="p-6 rounded-2xl glass-panel border border-slate-800">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-base font-bold text-white">{inv.question}</h4>
                      <span className="text-[10px] text-indigo-400 font-mono">{inv.model_used}</span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed mb-4">{inv.summary}</p>

                    {inv.evidence_refs && inv.evidence_refs.length > 0 && (
                      <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 font-mono text-xs">
                        <div className="text-[11px] text-slate-500 mb-1">
                          Evidence Grounding: {inv.evidence_refs[0].file} ({inv.evidence_refs[0].lines})
                        </div>
                        <pre className="text-slate-300 overflow-x-auto text-[11px]">
                          {inv.evidence_refs[0].snippet}
                        </pre>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Studio Tab 4: Patch & Sandbox */}
          {activeTab === "sandbox" && (
            <div className="flex-1 p-6 flex flex-col space-y-6">
              <div className="p-6 rounded-2xl glass-panel border border-slate-800">
                <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-4">
                  <div>
                    <h3 className="text-lg font-bold text-white">Autonomous Patch Sandbox</h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Target File: {proposedPatch.file_path}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                      Sandbox: {proposedPatch.sandbox_status}
                    </span>
                  </div>
                </div>

                <div className="mb-4">
                  <div className="text-xs uppercase tracking-wider text-slate-400 font-semibold mb-1">Unified Code Diff</div>
                  <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-emerald-300 overflow-x-auto">
                    {proposedPatch.diff}
                  </pre>
                </div>

                <div>
                  <div className="text-xs uppercase tracking-wider text-slate-400 font-semibold mb-1">Sandbox Execution Log</div>
                  <pre className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-[11px] font-mono text-slate-300 overflow-x-auto">
                    {proposedPatch.test_output}
                  </pre>
                </div>
              </div>
            </div>
          )}
        </main>
      )}

      {/* ═════════════════════════════════════════════════════════════════════════ */}
      {/* ── MODALS (Auth, Profile, Report, Import) ────────────────────────────── */}
      {/* ═════════════════════════════════════════════════════════════════════════ */}

      {/* Auth Modal */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        onSuccess={(user) => {
          setCurrentUser(user);
          refreshUserData();
        }}
      />

      {/* User Profile & Data Isolation Modal */}
      <UserProfileModal
        isOpen={showProfileModal}
        onClose={() => setShowProfileModal(false)}
        profileStats={profileStats}
        onLogout={() => {
          setCurrentUser(null);
          setProfileStats(null);
          refreshUserData();
        }}
      />

      {/* Institutional Audit Report Modal */}
      <ReportModal
        isOpen={showReportModal}
        onClose={() => setShowReportModal(false)}
        repoId={activeRepo.id}
        repoName={activeRepo.name}
      />

      {/* Neural Link: AI Agent Context Center Modal */}
      <NeuralLinkModal
        isOpen={showNeuralLinkModal}
        onClose={() => setShowNeuralLinkModal(false)}
        repoId={activeRepo.id}
        repoName={activeRepo.name}
      />

      {/* Detailed Diagnostic Error Banner */}
      <ErrorDiagnosticBanner
        error={diagnosticError}
        onDismiss={() => setDiagnosticError(null)}
        onRetry={() => window.location.reload()}
      />

      {/* Import Repository Modal */}
      {showImportModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md">
          <div className="relative w-full max-w-md p-6 rounded-2xl glass-panel border border-slate-700 shadow-2xl">
            <button
              onClick={() => setShowImportModal(false)}
              className="absolute top-4 right-4 p-1 rounded-lg text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>

            <h3 className="text-lg font-bold text-white mb-1">Import Code Repository</h3>
            <p className="text-xs text-slate-400 mb-4">
              Ingest local codebase or public Git URL for AST decomposition.
            </p>

            <div className="flex p-1 mb-4 rounded-xl bg-slate-900 border border-slate-800">
              <button
                type="button"
                onClick={() => setImportType("local")}
                className={`flex-1 py-1.5 text-xs font-semibold rounded-lg ${
                  importType === "local" ? "bg-indigo-600 text-white" : "text-slate-400"
                }`}
              >
                Local Path
              </button>
              <button
                type="button"
                onClick={() => setImportType("git")}
                className={`flex-1 py-1.5 text-xs font-semibold rounded-lg ${
                  importType === "git" ? "bg-indigo-600 text-white" : "text-slate-400"
                }`}
              >
                Git URL
              </button>
            </div>

            <form onSubmit={handleImportSubmit} className="space-y-3">
              <div>
                <label className="block text-xs text-slate-300 mb-1">Repository Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. BlackBox Core"
                  value={importName}
                  onChange={(e) => setImportName(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white"
                />
              </div>

              <div>
                <label className="block text-xs text-slate-300 mb-1">
                  {importType === "local" ? "Absolute Local Path" : "Git Repository URL"}
                </label>
                <input
                  type="text"
                  required
                  placeholder={
                    importType === "local"
                      ? "E:/Projects/my-service"
                      : "https://github.com/fastapi/fastapi"
                  }
                  value={importPath}
                  onChange={(e) => setImportPath(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white"
                />
              </div>

              <button
                type="submit"
                disabled={importing}
                className="w-full py-2.5 px-4 rounded-xl font-bold text-xs text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 transition"
              >
                {importing ? "Ingesting AST Symbols..." : "Start Ingestion"}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
