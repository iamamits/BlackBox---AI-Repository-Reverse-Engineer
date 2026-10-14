/**
 * BlackBox API client
 * Interfaces with FastAPI backend at http://localhost:8000
 */

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Auth & User Types ────────────────────────────────────────────────────────

export interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string | null;
  avatar_url?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface UserProfileStats {
  user: User;
  repository_count: number;
  investigation_count: number;
  patch_count: number;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Token Storage Helpers
export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("blackbox_auth_token");
}

export function setStoredToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem("blackbox_auth_token", token);
  }
}

export function clearStoredToken(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem("blackbox_auth_token");
  }
}

export function getAuthHeaders(): HeadersInit {
  const token = getStoredToken();
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

// ── Core Domain Types ────────────────────────────────────────────────────────

export interface RepoSummary {
  id: number;
  name: string;
  source_type: "local" | "zip" | "git";
  source_path: string;
  status: "pending" | "indexing" | "ready" | "error";
  primary_language?: string;
  file_count: number;
  symbol_count: number;
  index_progress: number;
  created_at: string;
}

export interface SystemHealth {
  status: "ok" | "degraded" | "error";
  version: string;
  database: string;
  ai_provider: string;
  ai_model: string;
  workspace_root: string;
}

export interface SymbolItem {
  id: number;
  name: string;
  qualified_name?: string;
  kind: "function" | "class" | "method" | "variable" | "module";
  file_path: string;
  line_start: number;
  line_end: number;
  signature?: string;
  docstring?: string;
}

export interface DependencyNode {
  id: string;
  name: string;
  type: "file" | "package" | "module";
  language: string;
  symbolsCount: number;
  x?: number;
  y?: number;
}

export interface DependencyEdge {
  id: string;
  source: string;
  target: string;
  type: "import" | "call" | "inheritance";
  confidence: "verified" | "heuristic";
}

export interface InvestigationResult {
  id: number;
  repository_id: number;
  question: string;
  status: "pending" | "running" | "complete" | "error";
  summary?: string;
  findings?: Array<{
    title: string;
    description: string;
    severity: "low" | "medium" | "high" | "critical";
    file?: string;
    line?: number;
  }>;
  evidence_refs?: Array<{
    file: string;
    lines: string;
    snippet: string;
  }>;
  model_used?: string;
  created_at: string;
}

export interface ProposedPatch {
  id: number;
  investigation_id: number;
  file_path: string;
  explanation: string;
  diff: string;
  status: "proposed" | "accepted" | "rejected";
  sandbox_status?: "pending" | "passed" | "failed" | "running";
  test_output?: string;
}

// ── Report Engine Types ──────────────────────────────────────────────────────

export interface MetricCard {
  label: string;
  value: string;
  change?: string | null;
  status: "normal" | "good" | "warning" | "critical";
}

export interface AuditFinding {
  title: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  category: string;
  description: string;
  file_path?: string | null;
  line_number?: number | null;
  remediation?: string | null;
}

export interface RepoAuditReport {
  repository_id: number;
  repository_name: string;
  primary_language?: string | null;
  source_type: string;
  health_score: number;
  security_grade: string;
  generated_at: string;
  metrics: MetricCard[];
  summary: string;
  component_breakdown: Array<{
    language: string;
    files: number;
    percentage: number;
  }>;
  symbol_statistics: Record<string, number>;
  security_findings: AuditFinding[];
  investigation_history: Array<{
    id: number;
    question: string;
    status: string;
    summary: string;
    model_used: string;
    findings_count: number;
    created_at: string;
  }>;
  patches_summary: Array<{
    id: number;
    investigation_id: number;
    explanation: string;
    status: string;
    diff_preview: string;
    sandbox_status: string;
  }>;
}

export interface AIModelItem {
  id: string;
  name: string;
  tag: string;
  tier: string;
  description: string;
  context_window: string;
  recommended: boolean;
}

export interface TestLLMResponse {
  status: "connected" | "unconfigured" | "error" | "rate_limited" | "timeout";
  configured: boolean;
  latency_ms?: number | null;
  model: string;
  message: string;
  reply?: string;
}

// ── Authentication API Calls ─────────────────────────────────────────────────

export async function registerUser(
  email: string,
  username: string,
  password: string,
  fullName?: string
): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/api/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, username, password, full_name: fullName }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Registration failed" }));
    throw new Error(err.detail || "Registration failed");
  }
  const data: AuthResponse = await res.json();
  setStoredToken(data.access_token);
  return data;
}

export async function loginUser(usernameOrEmail: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username_or_email: usernameOrEmail, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Login failed" }));
    throw new Error(err.detail || "Invalid credentials");
  }
  const data: AuthResponse = await res.json();
  setStoredToken(data.access_token);
  return data;
}

export async function fetchCurrentUser(): Promise<UserProfileStats | null> {
  const token = getStoredToken();
  if (!token) return null;
  try {
    const res = await fetch(`${API_BASE}/api/v1/auth/me`, {
      headers: getAuthHeaders(),
      cache: "no-store",
    });
    if (!res.ok) {
      clearStoredToken();
      return null;
    }
    return await res.json();
  } catch {
    return null;
  }
}

// ── System Health & Repository Calls ─────────────────────────────────────────

export async function fetchHealth(): Promise<SystemHealth> {
  try {
    const res = await fetch(`${API_BASE}/api/health`, { cache: "no-store" });
    if (!res.ok) throw new Error("Health check failed");
    return await res.json();
  } catch (err) {
    return {
      status: "degraded",
      version: "0.1.0",
      database: "connected (local)",
      ai_provider: "nebius (ready)",
      ai_model: "nvidia/Nemotron-3-Ultra-550b-a55b",
      workspace_root: "./workspace_data",
    };
  }
}

export async function fetchRepositories(): Promise<RepoSummary[]> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/repos/`, {
      headers: getAuthHeaders(),
      cache: "no-store",
    });
    if (!res.ok) throw new Error("Failed to fetch repositories");
    const data = await res.json();
    return data.items || [];
  } catch (err) {
    return [];
  }
}

export async function importLocalRepo(name: string, path: string): Promise<RepoSummary> {
  const res = await fetch(`${API_BASE}/api/v1/repos/import/local`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ name, path }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to import repo" }));
    throw new Error(err.detail || "Import failed");
  }
  return await res.json();
}

export async function importGitRepo(url: string, branch: string = "main"): Promise<RepoSummary> {
  const res = await fetch(`${API_BASE}/api/v1/repos/import/git`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ url, branch }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Git import failed" }));
    throw new Error(err.detail || "Git import failed");
  }
  return await res.json();
}

export async function fetchAIModels(): Promise<AIModelItem[]> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/ai/models`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch models");
    return await res.json();
  } catch (err) {
    return [
      {
        id: "nvidia/Nemotron-3-Ultra-550b-a55b",
        name: "NVIDIA Nemotron 3 Ultra 550B",
        tag: "NVIDIA Flagship",
        tier: "High Accuracy & Reasoning",
        description: "Premier NVIDIA open model on Nebius. Massive 550B architecture for deep architectural analysis, complex call tracing, and unified diff patches.",
        context_window: "128K",
        recommended: true,
      },
      {
        id: "nvidia/Nemotron-3_5-Lightning",
        name: "NVIDIA Nemotron 3.5 Lightning",
        tag: "NVIDIA Fast",
        tier: "Ultra Low Latency",
        description: "High-speed NVIDIA inference (~580ms latency). Ideal for fast repository exploration and lightweight Q&A.",
        context_window: "64K",
        recommended: false,
      },
      {
        id: "Qwen/Qwen3-30B-A3B-Instruct-2507",
        name: "Qwen 3 30B Instruct (MoE)",
        tag: "Code Specialist",
        tier: "Coding Pro",
        description: "Advanced Mixture-of-Experts coding model with benchmark-topping syntax comprehension and multi-file debugging.",
        context_window: "128K",
        recommended: false,
      },
      {
        id: "Qwen/Qwen3.8-27B",
        name: "Qwen 3.8 27B Instruct",
        tag: "Compact",
        tier: "Fast & Efficient",
        description: "Highly optimized 27B parameter coding engine with sub-second latency and minimal token consumption.",
        context_window: "32K",
        recommended: false,
      },
      {
        id: "google/gemma-3-27b-it",
        name: "Google Gemma 3 27B Instruct",
        tag: "Balanced",
        tier: "Instruction Tuned",
        description: "Google open-weights model fine-tuned for structured instruction following and architectural analysis.",
        context_window: "128K",
        recommended: false,
      },
      {
        id: "moonshotai/Kimi-K2.7-Code",
        name: "Moonshot Kimi K2.7 Code",
        tag: "Code Expert",
        tier: "Deep Code Analysis",
        description: "Specialized coding model trained specifically on massive software repositories and architectural patterns.",
        context_window: "128K",
        recommended: false,
      },
    ];
  }
}

export async function testLLMConnection(model?: string): Promise<TestLLMResponse> {
  const res = await fetch(`${API_BASE}/api/v1/ai/test`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ model }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Connection test request failed" }));
    return {
      status: "error",
      configured: false,
      model: model || "unknown",
      message: err.detail || `Server returned HTTP ${res.status}`,
    };
  }
  return await res.json();
}

export async function startInvestigation(
  repoId: number,
  question: string,
  model?: string
): Promise<InvestigationResult> {
  const res = await fetch(`${API_BASE}/api/v1/investigations/`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ repository_id: repoId, question, model }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to start investigation" }));
    throw new Error(err.detail || "Investigation failed");
  }
  return await res.json();
}

// ── Report Engine Calls ──────────────────────────────────────────────────────

export async function fetchReport(repoId: number): Promise<RepoAuditReport> {
  const res = await fetch(`${API_BASE}/api/v1/reports/${repoId}`, {
    headers: getAuthHeaders(),
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to load audit report for repository #${repoId}`);
  }
  return await res.json();
}

export function getReportDownloadUrl(repoId: number, format: "html" | "markdown" | "json" = "html"): string {
  return `${API_BASE}/api/v1/reports/${repoId}/download?format=${format}`;
}

// ── Holographic Visualization Types & Calls ──────────────────────────────────

export interface HolographicNode3D {
  id: string;
  file_id: number;
  label: string;
  path: string;
  language: string;
  category: "api_route" | "data_model" | "core_logic" | "worker" | "test";
  cluster: string;
  symbol_count: number;
  size_bytes: number;
  lines: number;
  position: { x: number; y: number; z: number };
}

export interface HolographicEdge3D {
  id: string;
  source: string;
  target: string;
  type: string;
  confidence: string;
  evidence?: string | null;
}

export interface HolographicTopology {
  repository_id: number;
  repository_name: string;
  primary_language?: string | null;
  clusters: Array<{ name: string; count: number }>;
  node_count: number;
  edge_count: number;
  nodes: HolographicNode3D[];
  edges: HolographicEdge3D[];
}

export interface ChangeImpactResult {
  repository_id: number;
  target_file: string;
  risk_level: "low" | "medium" | "high" | "critical";
  impact_score: number;
  upstream_dependents_count: number;
  downstream_dependencies_count: number;
  upstream_dependents: Array<{ id: number; path: string; language: string }>;
  downstream_dependencies: Array<{ id: number; path: string; language: string }>;
  recommended_test_files: string[];
}

export async function fetchTopology(repoId: number, maxNodes: number = 150): Promise<HolographicTopology> {
  const res = await fetch(`${API_BASE}/api/v1/visualization/${repoId}/topology?max_nodes=${maxNodes}`, {
    headers: getAuthHeaders(),
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to load holographic topology for repository #${repoId}`);
  }
  return await res.json();
}

export async function fetchChangeImpact(repoId: number, filePath: string): Promise<ChangeImpactResult> {
  const res = await fetch(
    `${API_BASE}/api/v1/visualization/${repoId}/impact?file_path=${encodeURIComponent(filePath)}`,
    {
      headers: getAuthHeaders(),
      cache: "no-store",
    }
  );
  if (!res.ok) {
    throw new Error(`Failed to analyze impact for file '${filePath}'`);
  }
  return await res.json();
}

// ── Neural Link Context Types & Calls ────────────────────────────────────────

export interface ProjectMemoryResponse {
  repository_id: number;
  repository_name: string;
  version: number;
  content_fingerprint: string;
  is_fresh: boolean;
  is_verified: boolean;
  updated_at: string;
  sections: {
    identity?: string | null;
    architecture?: string | null;
    conventions?: string | null;
    decisions?: string | null;
    constraints?: string | null;
    limitations?: string | null;
    test_instructions?: string | null;
    task_continuity?: string | null;
  };
}

export interface ContextCompileResponse {
  id: number;
  repository_id: number;
  format: string;
  target_agent: string;
  token_budget: number;
  estimated_tokens: number;
  within_budget: boolean;
  content: string;
}

export async function fetchProjectMemory(repoId: number): Promise<ProjectMemoryResponse> {
  const res = await fetch(`${API_BASE}/api/v1/neural-link/${repoId}`, {
    headers: getAuthHeaders(),
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to load project memory for repository #${repoId}`);
  }
  return await res.json();
}

export async function compileContextPack(
  repoId: number,
  payload: {
    task_description: string;
    token_budget?: number;
    format?: string;
    target_agent?: string;
    relevant_files?: string[];
  }
): Promise<ContextCompileResponse> {
  const res = await fetch(`${API_BASE}/api/v1/neural-link/${repoId}/compile`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Context compilation failed" }));
    throw new Error(err.detail || "Context compilation failed");
  }
  return await res.json();
}

export function getNeuralLinkExportUrl(
  repoId: number,
  format: "agents_md" | "markdown" | "json" = "agents_md"
): string {
  return `${API_BASE}/api/v1/neural-link/${repoId}/export?format=${format}`;
}

