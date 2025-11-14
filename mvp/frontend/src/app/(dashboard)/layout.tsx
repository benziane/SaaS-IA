/**
 * Dashboard Layout - Hybrid Approach (Sneat VerticalLayout + MVP Auth)
 * Uses Sneat's VerticalLayout with MVP JWT authentication - REFONTE
 */

// Type Imports
import type { ChildrenType } from '@core/types';

// Layout Imports
import LayoutWrapper from '@layouts/LayoutWrapper';

// Guard Imports (REFONTE)
import { AuthGuard } from '@/components/guards';

/* ========================================================================
   COMPONENT
   ======================================================================== */

export default function DashboardLayout({ children }: ChildrenType) {
  return (
    <AuthGuard>
      <LayoutWrapper verticalLayout={true}>
        {children}
      </LayoutWrapper>
    </AuthGuard>
  );
}
