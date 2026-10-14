/**
 * BlackBox API client
 * Interfaces with FastAPI backend at http://localhost:8000
 */

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
    const res = await fetch(`${API_BASE}/api/v1/repos/`, { cache: "no-store" });
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
    headers: { "Content-Type": "application/json" },
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
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, branch }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Git import failed" }));
    throw new Error(err.detail || "Git import failed");
  }
  return await res.json();
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
    headers: { "Content-Type": "application/json" },
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
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repository_id: repoId, question, model }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to start investigation" }));
    throw new Error(err.detail || "Investigation failed");
  }
  return await res.json();
}

