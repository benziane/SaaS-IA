'use client'

// Third-party Imports
import classnames from 'classnames'

// MUI Imports
import { Box, Chip, Typography } from '@mui/material'

// Component Imports
import NavToggle from './NavToggle'
import ModeDropdown from '@components/layout/shared/ModeDropdown'
import UserDropdown from '@components/layout/shared/UserDropdown'

// Util Imports
import { verticalLayoutClasses } from '@layouts/utils/layoutClasses'

const NavbarContent = () => {
  return (
    <div className={classnames(verticalLayoutClasses.navbarContent, 'flex items-center justify-between gap-4 is-full')}>
      <div className='flex items-center gap-4'>
        <NavToggle />
        <ModeDropdown />
      </div>
      <Box
        onClick={() => {
          const event = new KeyboardEvent('keydown', { key: 'k', ctrlKey: true, bubbles: true });
          window.dispatchEvent(event);
        }}
        sx={{
          display: { xs: 'none', md: 'flex' },
          alignItems: 'center',
          gap: 1,
          px: 2,
          py: 0.75,
          borderRadius: 2,
          border: '1px solid',
          borderColor: 'divider',
          cursor: 'pointer',
          color: 'text.secondary',
          '&:hover': { bgcolor: 'action.hover' },
          minWidth: 200,
        }}
      >
        <i className="tabler-search" style={{ fontSize: 18 }} />
        <Typography variant="body2" color="text.secondary" sx={{ flex: 1 }}>
          Search...
        </Typography>
        <Chip label="Ctrl+K" size="small" variant="outlined" sx={{ height: 20, fontSize: '0.65rem' }} />
      </Box>
      <div className='flex items-center'>
        <UserDropdown />
      </div>
    </div>
  )
}

export default NavbarContent
