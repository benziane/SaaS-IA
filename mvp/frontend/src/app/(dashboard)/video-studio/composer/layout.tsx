'use client';

import type { ReactNode } from 'react';
import { Box } from '@mui/material';

export default function ComposerLayout({ children }: { children: ReactNode }) {
  return (
    <Box
      sx={{
        height: 'calc(100vh - 64px)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        bgcolor: '#0a0a0f',
      }}
    >
      {children}
    </Box>
  );
}
