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
      ai_model: "meta-llama/Meta-Llama-3.1-70B-Instruct",
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
        id: "meta-llama/Meta-Llama-3.1-70B-Instruct",
        name: "Llama 3.1 70B Instruct",
        tag: "Flagship",
        tier: "High Accuracy",
        description: "NVIDIA premier open model. Best for deep architectural analysis and diff patches.",
        context_window: "128K",
        recommended: true,
      },
      {
        id: "meta-llama/Meta-Llama-3.1-8B-Instruct",
        name: "Llama 3.1 8B Instruct",
        tag: "Ultra Fast",
        tier: "Lightweight & Fast",
        description: "Lightning fast inference and minimal token consumption. Free tier friendly.",
        context_window: "128K",
        recommended: false,
      },
      {
        id: "Qwen/Qwen2.5-Coder-32B-Instruct",
        name: "Qwen 2.5 Coder 32B",
        tag: "Code Specialist",
        tier: "Coding Pro",
        description: "Benchmark-topping code comprehension and syntax analysis.",
        context_window: "32K",
        recommended: false,
      },
      {
        id: "mistralai/Mistral-7B-Instruct-v0.3",
        name: "Mistral 7B Instruct v0.3",
        tag: "Compact",
        tier: "Low Latency",
        description: "High token efficiency with concise technical explanations.",
        context_window: "32K",
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
