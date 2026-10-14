"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Compass,
  RotateCcw,
  Search,
  Filter,
  Layers,
  Network,
  Maximize2,
  Minimize2,
  FileCode2,
  ShieldAlert,
  ArrowRight,
  ExternalLink,
  ChevronRight,
  Activity,
  Zap,
  Info,
  SlidersHorizontal,
  CheckCircle2
} from "lucide-react";
import {
  fetchTopology,
  fetchChangeImpact,
  HolographicTopology,
  HolographicNode3D,
  ChangeImpactResult
} from "../lib/api";

interface HolographicExplorerProps {
  repoId: number;
  repoName: string;
  onOpenFile?: (filePath: string) => void;
}

export default function HolographicExplorer({ repoId, repoName, onOpenFile }: HolographicExplorerProps) {
  const [topology, setTopology] = useState<HolographicTopology | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // View & Filter Controls
  const [viewDimension, setViewDimension] = useState<"3d" | "2d">("3d");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [selectedCluster, setSelectedCluster] = useState<string>("all");

  // Selection & Impact
  const [selectedNode, setSelectedNode] = useState<HolographicNode3D | null>(null);
  const [impactResult, setImpactResult] = useState<ChangeImpactResult | null>(null);
  const [loadingImpact, setLoadingImpact] = useState<boolean>(false);

  // 3D Canvas
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rotationRef = useRef<{ x: number; y: number; zoom: number; isDragging: boolean; lastX: number; lastY: number }>({
    x: 0.3,
    y: 0.5,
    zoom: 1.0,
    isDragging: false,
    lastX: 0,
    lastY: 0,
  });

  // Fetch Topology
  useEffect(() => {
    setLoading(true);
    setError(null);
    setSelectedNode(null);
    setImpactResult(null);

    fetchTopology(repoId, 160)
      .then((data) => {
        setTopology(data);
        if (data.nodes.length > 0) {
          setSelectedNode(data.nodes[0]);
        }
      })
      .catch((err) => setError(err.message || "Failed to load holographic topology"))
      .finally(() => setLoading(false));
  }, [repoId]);

  // Analyze Impact when Selected Node changes
  const handleAnalyzeImpact = async (node: HolographicNode3D) => {
    setLoadingImpact(true);
    try {
      const res = await fetchChangeImpact(repoId, node.path);
      setImpactResult(res);
    } catch {
      setImpactResult(null);
    } finally {
      setLoadingImpact(false);
    }
  };

  // 3D Canvas Rendering Loop
  useEffect(() => {
    if (!topology || topology.nodes.length === 0) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;

    const render = () => {
      const width = (canvas.width = canvas.parentElement?.clientWidth || 800);
      const height = (canvas.height = canvas.parentElement?.clientHeight || 550);
      ctx.clearRect(0, 0, width, height);

      const cx = width / 2;
      const cy = height / 2;
      const rot = rotationRef.current;

      // Filter nodes
      const filteredNodes = topology.nodes.filter((n) => {
        const matchesQuery = n.path.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesCat = selectedCategory === "all" || n.category === selectedCategory;
        const matchesClust = selectedCluster === "all" || n.cluster === selectedCluster;
        return matchesQuery && matchesCat && matchesClust;
      });

      const filteredIds = new Set(filteredNodes.map((n) => n.id));

      // Draw background grid
      ctx.lineWidth = 0.5;
      ctx.strokeStyle = "rgba(99, 102, 241, 0.05)";
      const step = 40;
      for (let x = 0; x < width; x += step) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = 0; y < height; y += step) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      // Project 3D nodes
      const cosY = Math.cos(viewDimension === "3d" ? rot.y : 0);
      const sinY = Math.sin(viewDimension === "3d" ? rot.y : 0);
      const cosX = Math.cos(viewDimension === "3d" ? rot.x : 0);
      const sinX = Math.sin(viewDimension === "3d" ? rot.x : 0);
      const fov = 450 * rot.zoom;

      const projected = new Map<string, { px: number; py: number; scale: number; node: HolographicNode3D }>();

      for (const n of filteredNodes) {
        const pos = n.position;
        const x1 = pos.x * cosY + pos.z * sinY;
        const z1 = -pos.x * sinY + pos.z * cosY;

        const y2 = pos.y * cosX - z1 * sinX;
        const z2 = pos.y * sinX + z1 * cosX;

        const zDepth = viewDimension === "3d" ? z2 + 500 : 500;
        if (zDepth > 20) {
          const scale = fov / zDepth;
          const px = cx + x1 * scale;
          const py = cy + y2 * scale;
          projected.set(n.id, { px, py, scale, node: n });
        }
      }

      // Draw Edges
      ctx.lineWidth = 0.8;
      for (const e of topology.edges) {
        if (!filteredIds.has(e.source) || !filteredIds.has(e.target)) continue;
        const p1 = projected.get(e.source);
        const p2 = projected.get(e.target);
        if (p1 && p2) {
          const isSelected = selectedNode && (selectedNode.id === e.source || selectedNode.id === e.target);
          ctx.strokeStyle = isSelected ? "rgba(6, 182, 212, 0.75)" : "rgba(99, 102, 241, 0.15)";
          ctx.lineWidth = isSelected ? 1.8 : 0.7;
          ctx.beginPath();
          ctx.moveTo(p1.px, p1.py);
          ctx.lineTo(p2.px, p2.py);
          ctx.stroke();
        }
      }

      // Draw Projected Nodes
      for (const [, p] of projected) {
        const isSelected = selectedNode?.id === p.node.id;
        const baseRadius = 4.0 + Math.min(8.0, p.node.symbol_count * 0.4);
        const r = Math.max(2.5, baseRadius * p.scale);

        // Color by category
        let color = "#6366f1"; // core_logic
        if (p.node.category === "api_route") color = "#06b6d4";
        else if (p.node.category === "data_model") color = "#a855f7";
        else if (p.node.category === "worker") color = "#f59e0b";
        else if (p.node.category === "test") color = "#10b981";

        // Glow ring if selected
        if (isSelected) {
          ctx.strokeStyle = "#38bdf8";
          ctx.lineWidth = 2.5;
          ctx.beginPath();
          ctx.arc(p.px, p.py, r * 2.2, 0, Math.PI * 2);
          ctx.stroke();
        }

        // Outer glow gradient
        const glow = ctx.createRadialGradient(p.px, p.py, 0, p.px, p.py, r * 3);
        glow.addColorStop(0, color);
        glow.addColorStop(1, "transparent");
        ctx.fillStyle = glow;
        ctx.beginPath();
        ctx.arc(p.px, p.py, r * 3, 0, Math.PI * 2);
        ctx.fill();

        // Core solid node
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(p.px, p.py, r, 0, Math.PI * 2);
        ctx.fill();

        // Label if zoomed in or selected
        if (isSelected || p.scale > 0.85) {
          ctx.font = isSelected ? "bold 11px sans-serif" : "9px monospace";
          ctx.fillStyle = isSelected ? "#ffffff" : "#94a3b8";
          ctx.textAlign = "center";
          ctx.fillText(p.node.label, p.px, p.py - r - 4);
        }
      }

      animId = requestAnimationFrame(render);
    };

    render();

    return () => cancelAnimationFrame(animId);
  }, [topology, viewDimension, searchQuery, selectedCategory, selectedCluster, selectedNode]);

  // Mouse Interaction handlers for orbit & pan
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    rotationRef.current.isDragging = true;
    rotationRef.current.lastX = e.clientX;
    rotationRef.current.lastY = e.clientY;
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!rotationRef.current.isDragging) return;
    const dx = e.clientX - rotationRef.current.lastX;
    const dy = e.clientY - rotationRef.current.lastY;
    rotationRef.current.y += dx * 0.008;
    rotationRef.current.x += dy * 0.008;
    rotationRef.current.lastX = e.clientX;
    rotationRef.current.lastY = e.clientY;
  };

  const handleMouseUp = () => {
    rotationRef.current.isDragging = false;
  };

  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.08 : 0.92;
    rotationRef.current.zoom = Math.max(0.4, Math.min(2.8, rotationRef.current.zoom * zoomFactor));
  };

  const handleResetCamera = () => {
    rotationRef.current = {
      x: 0.3,
      y: 0.5,
      zoom: 1.0,
      isDragging: false,
      lastX: 0,
      lastY: 0,
    };
  };

  // Node Click Selection on Canvas
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!topology) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    const rot = rotationRef.current;

    const cosY = Math.cos(viewDimension === "3d" ? rot.y : 0);
    const sinY = Math.sin(viewDimension === "3d" ? rot.y : 0);
    const cosX = Math.cos(viewDimension === "3d" ? rot.x : 0);
    const sinX = Math.sin(viewDimension === "3d" ? rot.x : 0);
    const fov = 450 * rot.zoom;

    let closestNode: HolographicNode3D | null = null;
    let minDist = 22.0;

    for (const n of topology.nodes) {
      const pos = n.position;
      const x1 = pos.x * cosY + pos.z * sinY;
      const z1 = -pos.x * sinY + pos.z * cosY;
      const y2 = pos.y * cosX - z1 * sinX;
      const z2 = pos.y * sinX + z1 * cosX;

      const zDepth = viewDimension === "3d" ? z2 + 500 : 500;
      if (zDepth > 20) {
        const scale = fov / zDepth;
        const px = cx + x1 * scale;
        const py = cy + y2 * scale;
        const dist = Math.hypot(mouseX - px, mouseY - py);
        if (dist < minDist) {
          minDist = dist;
          closestNode = n;
        }
      }
    }

    if (closestNode) {
      setSelectedNode(closestNode);
      handleAnalyzeImpact(closestNode);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden">
      {/* ── Explorer Toolbar ────────────────────────────────────────────── */}
      <div className="p-4 border-b border-slate-800 bg-slate-950/70 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-700/80 rounded-xl p-1 text-xs">
            <button
              onClick={() => setViewDimension("3d")}
              className={`py-1 px-2.5 rounded-lg font-semibold transition ${
                viewDimension === "3d" ? "bg-indigo-600 text-white shadow-sm" : "text-slate-400 hover:text-white"
              }`}
            >
              3D Digital Twin
            </button>
            <button
              onClick={() => setViewDimension("2d")}
              className={`py-1 px-2.5 rounded-lg font-semibold transition ${
                viewDimension === "2d" ? "bg-indigo-600 text-white shadow-sm" : "text-slate-400 hover:text-white"
              }`}
            >
              2D Schematic
            </button>
          </div>

          {/* Search Input */}
          <div className="relative">
            <Search className="absolute left-3 top-2.5 w-3.5 h-3.5 text-slate-500" />
            <input
              type="text"
              placeholder="Search file in topology..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 pr-3 py-1.5 bg-slate-900/90 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 w-48 sm:w-64"
            />
          </div>

          {/* Category Filter */}
          <select
            aria-label="Filter by Node Category"
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-xl px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none"
          >
            <option value="all">All Categories</option>
            <option value="api_route">API Routes (Cyan)</option>
            <option value="data_model">Data Models (Purple)</option>
            <option value="core_logic">Core Logic (Indigo)</option>
            <option value="worker">Background Workers (Amber)</option>
            <option value="test">Test Suites (Emerald)</option>
          </select>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          {topology && (
            <span className="text-xs text-slate-400 font-mono hidden md:inline">
              {topology.node_count} Files • {topology.edge_count} Edges
            </span>
          )}
          <button
            onClick={handleResetCamera}
            className="flex items-center gap-1.5 py-1.5 px-3 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs text-slate-300 transition"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Camera</span>
          </button>
        </div>
      </div>

      {/* ── Main Canvas & Inspector Split ───────────────────────────────── */}
      <div className="flex-1 flex flex-col lg:flex-row relative overflow-hidden">
        {/* Holographic Canvas */}
        <div className="flex-1 relative min-h-[420px] bg-[#070b14] flex items-center justify-center cursor-grab active:cursor-grabbing">
          {loading && (
            <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-black/60 backdrop-blur-sm">
              <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-3" />
              <div className="text-xs font-semibold text-slate-300">
                Computing 3D Topological Coordinates & Clusters...
              </div>
            </div>
          )}

          {error && (
            <div className="absolute top-6 left-6 right-6 z-20 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
              {error}
            </div>
          )}

          <canvas
            ref={canvasRef}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onWheel={handleWheel}
            onClick={handleCanvasClick}
            className="w-full h-full block"
          />

          {/* Canvas Floating Instructions */}
          <div className="absolute bottom-4 left-4 p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-[11px] text-slate-400 backdrop-blur-md pointer-events-none hidden sm:block">
            <span>Click node to inspect • Drag to rotate • Wheel to zoom</span>
          </div>
        </div>

        {/* ── Selected Node Inspector & Change Impact Panel ───────────────── */}
        {selectedNode && (
          <div className="w-full lg:w-96 border-t lg:border-t-0 lg:border-l border-slate-800 bg-slate-950/90 backdrop-blur-xl p-5 overflow-y-auto space-y-4 shrink-0">
            {/* Header */}
            <div className="flex items-start justify-between gap-2 pb-3 border-b border-slate-800">
              <div className="min-w-0">
                <span
                  className={`inline-block px-2 py-0.5 text-[10px] font-bold uppercase rounded-md mb-1.5 ${
                    selectedNode.category === "api_route"
                      ? "bg-cyan-500/20 text-cyan-400"
                      : selectedNode.category === "data_model"
                      ? "bg-purple-500/20 text-purple-400"
                      : selectedNode.category === "worker"
                      ? "bg-amber-500/20 text-amber-400"
                      : selectedNode.category === "test"
                      ? "bg-emerald-500/20 text-emerald-400"
                      : "bg-indigo-500/20 text-indigo-400"
                  }`}
                >
                  {selectedNode.category.replace("_", " ")}
                </span>
                <h4 className="text-sm font-bold text-white truncate font-mono">{selectedNode.label}</h4>
                <div className="text-[11px] text-slate-400 truncate mt-0.5">{selectedNode.path}</div>
              </div>

              {onOpenFile && (
                <button
                  onClick={() => onOpenFile(selectedNode.path)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
                  title="Open source file"
                >
                  <ExternalLink className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Quick Metrics */}
            <div className="grid grid-cols-3 gap-2 text-center text-xs">
              <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800">
                <div className="text-[10px] uppercase text-slate-500">Symbols</div>
                <div className="font-bold text-white mt-0.5">{selectedNode.symbol_count}</div>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800">
                <div className="text-[10px] uppercase text-slate-500">Lines</div>
                <div className="font-bold text-white mt-0.5">{selectedNode.lines || "-"}</div>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800">
                <div className="text-[10px] uppercase text-slate-500">Language</div>
                <div className="font-bold text-cyan-300 mt-0.5 truncate">{selectedNode.language}</div>
              </div>
            </div>

            {/* Change Impact Analysis Section */}
            <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-white flex items-center gap-1.5">
                  <Activity className="w-4 h-4 text-amber-400" />
                  <span>Change Impact Reachability</span>
                </span>
                <button
                  onClick={() => handleAnalyzeImpact(selectedNode)}
                  disabled={loadingImpact}
                  className="text-[10px] text-indigo-400 hover:text-indigo-300 font-semibold uppercase"
                >
                  {loadingImpact ? "Analyzing..." : "Re-Analyze"}
                </button>
              </div>

              {impactResult ? (
                <div className="space-y-2 text-xs">
                  <div className="flex items-center justify-between p-2 rounded-lg bg-slate-950 border border-slate-800/80">
                    <span className="text-slate-400">Risk Assessment</span>
                    <span
                      className={`font-bold uppercase text-[11px] ${
                        impactResult.risk_level === "critical"
                          ? "text-rose-400"
                          : impactResult.risk_level === "high"
                          ? "text-amber-400"
                          : "text-emerald-400"
                      }`}
                    >
                      {impactResult.risk_level} ({impactResult.impact_score}%)
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-[11px]">
                    <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800">
                      <div className="text-slate-500">Upstream Callers</div>
                      <div className="font-bold text-white mt-0.5">
                        {impactResult.upstream_dependents_count} files
                      </div>
                    </div>
                    <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800">
                      <div className="text-slate-500">Downstream Imports</div>
                      <div className="font-bold text-white mt-0.5">
                        {impactResult.downstream_dependencies_count} files
                      </div>
                    </div>
                  </div>

                  {impactResult.recommended_test_files.length > 0 && (
                    <div className="pt-2 border-t border-slate-800">
                      <div className="text-[10px] text-emerald-400 font-semibold mb-1">
                        Recommended Test Suites to Run:
                      </div>
                      <div className="space-y-1">
                        {impactResult.recommended_test_files.map((t, idx) => (
                          <div key={idx} className="font-mono text-[10px] text-slate-300 truncate">
                            • {t}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-xs text-slate-400 text-center py-2">
                  Click Re-Analyze to trace upstream and downstream callers.
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
