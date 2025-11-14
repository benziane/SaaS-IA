/**
 * Dashboard Layout - Hybrid Approach (Sneat VerticalLayout + MVP Auth)
 * Uses Sneat's VerticalLayout with MVP JWT authentication
 */

// Type Imports
import type { ChildrenType } from '@core/types';

// Layout Imports
import LayoutWrapper from '@layouts/LayoutWrapper';

// HOC Imports
import AuthGuard from '@/hocs/AuthGuard';

/* ========================================================================
   COMPONENT
   ======================================================================== */

export default function DashboardLayout({ children }: ChildrenType) {
  return (
    <AuthGuard>
      <LayoutWrapper verticalLayout>
        {children}
      </LayoutWrapper>
    </AuthGuard>
  );
}
