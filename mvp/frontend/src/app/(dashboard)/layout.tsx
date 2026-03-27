/**
 * Dashboard Layout - Hybrid Approach (Sneat VerticalLayout + MVP Auth)
 * Uses Sneat's VerticalLayout with MVP JWT authentication - REFONTE
 */

'use client';

// Type Imports
import type { ChildrenType } from '@core/types';

// Layout Imports
import VerticalLayout from '@layouts/VerticalLayout';
import Navigation from '@components/layout/vertical/Navigation';
import Navbar from '@components/layout/vertical/Navbar';
import Footer from '@components/layout/vertical/Footer';

// Guard Imports (REFONTE)
import { AuthGuard } from '@/components/guards';

// Breadcrumb
import { BreadcrumbBar } from '@/components/layout/shared/BreadcrumbBar';
import { EmailVerificationBanner } from '@/components/layout/shared/EmailVerificationBanner';
import CommandPalette from '@/components/ui/CommandPalette';
import BottomNav from '@/components/mobile/BottomNav';

/* ========================================================================
   COMPONENT
   ======================================================================== */

export default function DashboardLayout({ children }: ChildrenType) {
  return (
    <AuthGuard>
      <VerticalLayout
        navigation={<Navigation />}
        navbar={<Navbar />}
        footer={<Footer />}
      >
        <BreadcrumbBar />
        <EmailVerificationBanner />
        <CommandPalette />
        {children}
        <BottomNav />
      </VerticalLayout>
    </AuthGuard>
  );
}
