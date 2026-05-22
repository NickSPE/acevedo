import React from 'react';

export const CardSkeleton = () => (
  <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4 animate-pulse">
    <div className="flex items-center justify-between">
      <div className="h-4 w-28 bg-slate-800 rounded" />
      <div className="h-8 w-8 bg-slate-800 rounded-lg" />
    </div>
    <div className="h-8 w-36 bg-slate-800 rounded" />
    <div className="h-3 w-48 bg-slate-800 rounded" />
  </div>
);

export const ChartSkeleton = () => (
  <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4 animate-pulse">
    <div className="h-5 w-40 bg-slate-800 rounded" />
    <div className="h-64 w-full bg-slate-850/50 rounded-xl flex items-end justify-between p-4 gap-2">
      <div className="w-full bg-slate-800/80 rounded-t h-[40%]" />
      <div className="w-full bg-slate-800/80 rounded-t h-[70%]" />
      <div className="w-full bg-slate-800/80 rounded-t h-[55%]" />
      <div className="w-full bg-slate-800/80 rounded-t h-[90%]" />
      <div className="w-full bg-slate-800/80 rounded-t h-[30%]" />
    </div>
  </div>
);

export const TableSkeleton = () => (
  <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4 animate-pulse">
    <div className="flex justify-between items-center mb-4">
      <div className="h-5 w-32 bg-slate-800 rounded" />
      <div className="h-8 w-44 bg-slate-800 rounded-lg" />
    </div>
    <div className="space-y-3">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="flex items-center justify-between py-3 border-b border-slate-800/55">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-slate-800" />
            <div className="space-y-1.5">
              <div className="h-3.5 w-24 bg-slate-800 rounded" />
              <div className="h-3 w-16 bg-slate-800 rounded" />
            </div>
          </div>
          <div className="h-4 w-16 bg-slate-800 rounded" />
        </div>
      ))}
    </div>
  </div>
);

export const GoalsSkeleton = () => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    {[1, 2, 3].map((i) => (
      <div key={i} className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-5 animate-pulse">
        <div className="flex gap-4">
          <div className="w-12 h-12 rounded-xl bg-slate-800" />
          <div className="flex-1 space-y-2 mt-1">
            <div className="h-4 w-32 bg-slate-800 rounded" />
            <div className="h-3 w-20 bg-slate-800 rounded" />
          </div>
        </div>
        <div className="space-y-2">
          <div className="flex justify-between">
            <div className="h-3 w-20 bg-slate-800 rounded" />
            <div className="h-3 w-8 bg-slate-800 rounded" />
          </div>
          <div className="h-2 w-full bg-slate-800 rounded-full" />
        </div>
        <div className="h-8 w-full bg-slate-800 rounded-xl" />
      </div>
    ))}
  </div>
);
