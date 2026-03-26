'use client';

import type { ReactNode } from 'react';

export default function ComposerLayout({ children }: { children: ReactNode }) {
  return (
    <div className="h-[calc(100vh-64px)] flex flex-col overflow-hidden bg-[#0a0a0f]">
      {children}
    </div>
  );
}
