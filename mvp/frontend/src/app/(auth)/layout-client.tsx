'use client';

import type { ReactNode } from 'react';
import { GuestGuard } from '@/components/guards';

export default function AuthLayoutClient({ children }: { children: ReactNode }) {
  return <GuestGuard>{children}</GuestGuard>;
}

