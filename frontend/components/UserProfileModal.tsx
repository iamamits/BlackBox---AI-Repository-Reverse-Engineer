"use client";

import React from "react";
import {
  X,
  User as UserIcon,
  ShieldCheck,
  FolderGit2,
  Cpu,
  GitBranch,
  LogOut,
  Calendar,
  Mail,
  ExternalLink,
  Sparkles
} from "lucide-react";
import { clearStoredToken, UserProfileStats } from "../lib/api";

interface UserProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  profileStats: UserProfileStats | null;
  onLogout: () => void;
  onSelectRepo?: (repoId: number) => void;
}

export default function UserProfileModal({
  isOpen,
  onClose,
  profileStats,
  onLogout,
}: UserProfileModalProps) {
  if (!isOpen || !profileStats) return null;

  const user = profileStats.user;

  const handleSignOut = () => {
    clearStoredToken();
    onLogout();
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md">
      <div className="relative w-full max-w-lg p-8 overflow-hidden rounded-2xl glass-panel border border-slate-700/80 shadow-2xl shadow-cyan-500/10">
        {/* Glow ambient background */}
        <div className="absolute -top-24 -left-24 w-52 h-52 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -right-24 w-52 h-52 bg-cyan-500/20 rounded-full blur-3xl pointer-events-none" />

        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/80 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* User Profile Header */}
        <div className="flex items-start gap-4 mb-6">
          <div className="relative">
            <img
              src={user.avatar_url || `https://api.dicebear.com/7.x/bottts/svg?seed=${user.username}`}
              alt={user.username}
              className="w-16 h-16 rounded-2xl border-2 border-indigo-500/40 bg-slate-900 object-cover shadow-lg shadow-indigo-500/20"
            />
            <div className="absolute -bottom-1 -right-1 p-1 rounded-full bg-emerald-500 border-2 border-slate-900" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-white truncate">{user.full_name || user.username}</h2>
              <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-md bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                Architect
              </span>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-slate-400 mt-1">
              <Mail className="w-3.5 h-3.5 text-slate-500" />
              <span className="truncate">{user.email}</span>
            </div>
            <div className="flex items-center gap-1.5 text-[11px] text-slate-500 mt-1">
              <Calendar className="w-3 h-3 text-slate-500" />
              <span>Joined {new Date(user.created_at).toLocaleDateString()}</span>
            </div>
          </div>
        </div>

        {/* Data Isolation Security Banner */}
        <div className="flex items-center gap-3 p-3.5 mb-6 rounded-xl bg-slate-900/80 border border-emerald-500/20 text-xs">
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <div className="font-semibold text-emerald-300">Data Isolation Vault Active</div>
            <div className="text-[11px] text-slate-400">
              Your indexed repositories, AST graphs, and AI debug reports are securely isolated to your account.
            </div>
          </div>
        </div>

        {/* Personal Metrics Grid */}
        <div className="grid grid-cols-3 gap-3 mb-6">
          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-center">
            <div className="flex items-center justify-center w-7 h-7 mx-auto mb-1 rounded-lg bg-indigo-500/15 text-indigo-400">
              <FolderGit2 className="w-3.5 h-3.5" />
            </div>
            <div className="text-xl font-bold text-white">{profileStats.repository_count}</div>
            <div className="text-[10px] uppercase tracking-wider text-slate-400">Repositories</div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-center">
            <div className="flex items-center justify-center w-7 h-7 mx-auto mb-1 rounded-lg bg-cyan-500/15 text-cyan-400">
              <Cpu className="w-3.5 h-3.5" />
            </div>
            <div className="text-xl font-bold text-white">{profileStats.investigation_count}</div>
            <div className="text-[10px] uppercase tracking-wider text-slate-400">AI Audits</div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-center">
            <div className="flex items-center justify-center w-7 h-7 mx-auto mb-1 rounded-lg bg-emerald-500/15 text-emerald-400">
              <GitBranch className="w-3.5 h-3.5" />
            </div>
            <div className="text-xl font-bold text-white">{profileStats.patch_count}</div>
            <div className="text-[10px] uppercase tracking-wider text-slate-400">Patches</div>
          </div>
        </div>

        {/* Footer actions */}
        <div className="flex items-center justify-between pt-4 border-t border-slate-800">
          <div className="text-xs text-slate-500">Session ID: @{user.username}</div>
          <button
            onClick={handleSignOut}
            className="flex items-center gap-2 py-2 px-3.5 rounded-xl text-xs font-semibold text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 border border-rose-500/20 transition-all"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      </div>
    </div>
  );
}
