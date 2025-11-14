/**
 * Auth Layout - Hybrid Approach (Sneat BlankLayout + MVP Auth)
 * Uses Sneat's BlankLayout for login/register pages
 */

// Type Imports
import type { ChildrenType } from '@core/types';

// Layout Imports
import BlankLayout from '@layouts/BlankLayout';

// HOC Imports
import GuestOnlyRoute from '@/hocs/GuestOnlyRoute';

/* ========================================================================
   COMPONENT
   ======================================================================== */

export default function AuthLayout({ children }: ChildrenType) {
  return (
    <GuestOnlyRoute>
      <BlankLayout>
        {children}
      </BlankLayout>
    </GuestOnlyRoute>
  );
}
