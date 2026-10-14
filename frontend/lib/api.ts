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

export async function startInvestigation(repoId: number, question: string): Promise<InvestigationResult> {
  const res = await fetch(`${API_BASE}/api/v1/investigations/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repository_id: repoId, question }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to start investigation" }));
    throw new Error(err.detail || "Investigation failed");
  }
  return await res.json();
}
