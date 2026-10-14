"use client";

import React, { useEffect, useRef } from "react";

interface Node3D {
  x: number;
  y: number;
  z: number;
  vx: number;
  vy: number;
  vz: number;
  radius: number;
  color: string;
}

export default function Neural3DCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    let mouseX = 0;
    let mouseY = 0;
    let targetRotX = 0;
    let targetRotY = 0;
    let rotX = 0;
    let rotY = 0;

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    const handleMouseMove = (e: MouseEvent) => {
      const halfW = width / 2;
      const halfH = height / 2;
      mouseX = (e.clientX - halfW) / halfW;
      mouseY = (e.clientY - halfH) / halfH;
      targetRotY = mouseX * 0.4;
      targetRotX = -mouseY * 0.4;
    };

    window.addEventListener("resize", handleResize);
    window.addEventListener("mousemove", handleMouseMove);

    // Initialize 3D nodes
    const nodeCount = 55;
    const nodes: Node3D[] = [];
    const colors = ["#6366f1", "#06b6d4", "#8b5cf6", "#10b981", "#38bdf8"];

    for (let i = 0; i < nodeCount; i++) {
      nodes.push({
        x: (Math.random() - 0.5) * 1100,
        y: (Math.random() - 0.5) * 750,
        z: (Math.random() - 0.5) * 800,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        vz: (Math.random() - 0.5) * 0.4,
        radius: Math.random() * 2.2 + 1.2,
        color: colors[Math.floor(Math.random() * colors.length)],
      });
    }

    const fov = 420;

    const render = () => {
      // Smooth camera interpolation
      rotX += (targetRotX - rotX) * 0.05;
      rotY += (targetRotY - rotY) * 0.05;

      ctx.clearRect(0, 0, width, height);

      const cx = width / 2;
      const cy = height / 2;

      // Draw subtle background cyber isometric grid lines
      ctx.lineWidth = 0.5;
      ctx.strokeStyle = "rgba(99, 102, 241, 0.04)";
      const gridSize = 45;
      for (let x = 0; x < width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = 0; y < height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      // Update and project 3D nodes
      const projectedNodes: Array<{ px: number; py: number; scale: number; alpha: number; node: Node3D }> = [];

      const cosY = Math.cos(rotY);
      const sinY = Math.sin(rotY);
      const cosX = Math.cos(rotX);
      const sinX = Math.sin(rotX);

      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        n.x += n.vx;
        n.y += n.vy;
        n.z += n.vz;

        // Bounce back within bounds
        if (Math.abs(n.x) > 550) n.vx *= -1;
        if (Math.abs(n.y) > 375) n.vy *= -1;
        if (Math.abs(n.z) > 400) n.vz *= -1;

        // 3D rotation around Y and X
        const x1 = n.x * cosY + n.z * sinY;
        const z1 = -n.x * sinY + n.z * cosY;

        const y2 = n.y * cosX - z1 * sinX;
        const z2 = n.y * sinX + z1 * cosX;

        const zDepth = z2 + 650;
        if (zDepth > 40) {
          const scale = fov / zDepth;
          const px = cx + x1 * scale;
          const py = cy + y2 * scale;
          const alpha = Math.min(1, Math.max(0.12, (zDepth - 100) / 700));

          projectedNodes.push({ px, py, scale, alpha, node: n });
        }
      }

      // Draw interconnecting neural beams
      ctx.lineWidth = 0.8;
      for (let i = 0; i < projectedNodes.length; i++) {
        for (let j = i + 1; j < projectedNodes.length; j++) {
          const p1 = projectedNodes[i];
          const p2 = projectedNodes[j];
          const dx = p1.px - p2.px;
          const dy = p1.py - p2.py;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 140) {
            const lineAlpha = (1 - dist / 140) * 0.22 * Math.min(p1.alpha, p2.alpha);
            ctx.strokeStyle = `rgba(99, 102, 241, ${lineAlpha})`;
            ctx.beginPath();
            ctx.moveTo(p1.px, p1.py);
            ctx.lineTo(p2.px, p2.py);
            ctx.stroke();
          }
        }
      }

      // Draw projected glowing nodes
      for (const p of projectedNodes) {
        const r = p.node.radius * p.scale;
        if (r <= 0) continue;

        // Outer glow
        const glowGrad = ctx.createRadialGradient(p.px, p.py, 0, p.px, p.py, r * 4.5);
        glowGrad.addColorStop(0, p.node.color);
        glowGrad.addColorStop(1, "transparent");

        ctx.fillStyle = glowGrad;
        ctx.beginPath();
        ctx.arc(p.px, p.py, r * 4.5, 0, Math.PI * 2);
        ctx.fill();

        // Core bright node
        ctx.fillStyle = p.node.color;
        ctx.beginPath();
        ctx.arc(p.px, p.py, r, 0, Math.PI * 2);
        ctx.fill();
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("mousemove", handleMouseMove);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="pointer-events-none fixed inset-0 z-0 opacity-80"
      style={{ mixBlendMode: "screen" }}
    />
  );
}
