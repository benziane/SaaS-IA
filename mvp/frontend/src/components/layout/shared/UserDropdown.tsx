'use client'

// Next Imports
import { useRouter } from 'next/navigation'

// Lucide Imports
import { User, Settings, DollarSign, HelpCircle, LogOut } from 'lucide-react'

// Design Hub Imports
import { Avatar, AvatarImage, AvatarFallback } from '@/lib/design-hub/components/Avatar'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from '@/lib/design-hub/components/DropdownMenu'

// Hook Imports
import { useAuth } from '@/contexts/AuthContext'

const UserDropdown = () => {
  // Hooks
  const router = useRouter()
  const { user, logout } = useAuth()

  // Derive display values from auth context with fallbacks
  const displayName = user?.email?.split('@')[0] || 'User'
  const displayEmail = user?.email || 'Not signed in'

  const handleDropdownClose = (url?: string) => {
    if (url) {
      router.push(url)
    }
  }

  const handleUserLogout = async () => {
    logout()
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className='relative ms-2.5 cursor-pointer rounded-full focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:outline-none'>
          <Avatar className='h-10 w-10'>
            <AvatarImage src='/images/avatars/1.png' alt={displayName} />
            <AvatarFallback>{displayName.charAt(0).toUpperCase()}</AvatarFallback>
          </Avatar>
          <span className='absolute bottom-0 right-0 h-2 w-2 rounded-full bg-[var(--success,#22c55e)] ring-2 ring-[var(--bg-surface)]' />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align='end' className='min-w-[240px]'>
        <div className='flex items-center gap-2 px-3 py-2'>
          <Avatar className='h-10 w-10'>
            <AvatarImage src='/images/avatars/1.png' alt={displayName} />
            <AvatarFallback>{displayName.charAt(0).toUpperCase()}</AvatarFallback>
          </Avatar>
          <div className='flex flex-col'>
            <span className='text-sm font-semibold text-[var(--text-high)]'>{displayName}</span>
            <span className='text-xs text-[var(--text-low)]'>{displayEmail}</span>
          </div>
        </div>
        <DropdownMenuSeparator />
        <DropdownMenuItem className='gap-3' onClick={() => handleDropdownClose()}>
          <User className='h-4 w-4' />
          My Profile
        </DropdownMenuItem>
        <DropdownMenuItem className='gap-3' onClick={() => handleDropdownClose()}>
          <Settings className='h-4 w-4' />
          Settings
        </DropdownMenuItem>
        <DropdownMenuItem className='gap-3' onClick={() => handleDropdownClose()}>
          <DollarSign className='h-4 w-4' />
          Pricing
        </DropdownMenuItem>
        <DropdownMenuItem className='gap-3' onClick={() => handleDropdownClose()}>
          <HelpCircle className='h-4 w-4' />
          FAQ
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem className='gap-3' onClick={handleUserLogout}>
          <LogOut className='h-4 w-4' />
          Logout
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

export default UserDropdown
