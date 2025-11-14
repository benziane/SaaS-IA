/**
 * Auth Layout - Hybrid Approach (Sneat BlankLayout + MVP Auth)
 * Uses Sneat's BlankLayout for login/register pages - REFONTE
 */

// Type Imports
import type { ChildrenType } from '@core/types';

// Layout Imports
import BlankLayout from '@layouts/BlankLayout';

// Guard Imports (REFONTE)
import { GuestGuard } from '@/components/guards';

// Util Imports
import { getSystemMode } from '@core/utils/serverHelpers';

/* ========================================================================
   COMPONENT
   ======================================================================== */

export default async function AuthLayout({ children }: ChildrenType) {
  // Vars
  const systemMode = await getSystemMode();

  return (
    <GuestGuard>
      <BlankLayout systemMode={systemMode}>
        {children}
      </BlankLayout>
    </GuestGuard>
  );
}
