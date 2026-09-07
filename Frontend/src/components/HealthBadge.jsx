import React from 'react';
import { Activity, WifiOff } from 'lucide-react';

export function HealthBadge({ isOnline }) {
  return (
    <div
      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border transition-all ${
        isOnline
          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
          : 'bg-rose-50 text-rose-700 border-rose-200 animate-pulse'
      }`}
      title={isOnline ? 'Backend API Server Connected' : 'Backend API Offline'}
    >
      {isOnline ? (
        <>
          <Activity size={14} className="text-emerald-500" />
          <span>Backend Online</span>
        </>
      ) : (
        <>
          <WifiOff size={14} className="text-rose-500" />
          <span>Backend Offline</span>
        </>
      )}
    </div>
  );
}
