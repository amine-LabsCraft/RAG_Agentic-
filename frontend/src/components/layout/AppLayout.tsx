import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Menu, X } from 'lucide-react'
import { UserMenu } from '@/components/UserMenu'
import { useAuth } from '@/hooks/useAuth'
import { cn } from '@/lib/utils'
import logoSvg from '/logo.svg'

interface AppLayoutProps {
  children?: React.ReactNode
  sidebar?: React.ReactNode
}

export function AppLayout({ children, sidebar }: AppLayoutProps) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const { user, signOut, isAdmin } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const handleSignOut = async () => {
    try {
      await signOut()
    } catch (error) {
      console.error('Failed to sign out:', error)
    }
  }

  const isActive = (path: string) => location.pathname === path

  const nav = (
    <div className="flex gap-1">
      <button
        onClick={() => {
          navigate('/')
          setMobileOpen(false)
        }}
        className={cn(
          'flex-1 rounded-md px-3 py-1.5 text-sm transition-colors hover:bg-muted',
          isActive('/') && 'bg-muted font-medium'
        )}
      >
        Chat
      </button>
      <button
        onClick={() => {
          navigate('/documents')
          setMobileOpen(false)
        }}
        className={cn(
          'flex-1 rounded-md px-3 py-1.5 text-sm transition-colors hover:bg-muted',
          isActive('/documents') && 'bg-muted font-medium'
        )}
      >
        Documents
      </button>
    </div>
  )

  return (
    <div className="flex h-screen">
      {/* Desktop sidebar */}
      <div className="hidden w-64 shrink-0 flex-col border-r bg-muted/30 md:flex">
        <div className="border-b p-4">
          <img src={logoSvg} alt="RAG Masterclass" className="h-8" />
        </div>
        <nav className="border-b p-2">{nav}</nav>
        {sidebar ? (
          <div className="flex min-h-0 flex-1 flex-col">{sidebar}</div>
        ) : (
          <div className="flex-1" />
        )}
        <div className="border-t p-2">
          {user?.email && (
            <UserMenu email={user.email} onSignOut={handleSignOut} isAdmin={isAdmin} />
          )}
        </div>
      </div>

      {/* Mobile top bar */}
      <div className="flex min-w-0 flex-1 flex-col md:hidden">
        <div className="flex items-center justify-between border-b p-3">
          <div className="flex items-center gap-2">
            <button
              type="button"
              aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
              onClick={() => setMobileOpen((v) => !v)}
              className="rounded-md p-2 hover:bg-muted"
            >
              {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
            <img src={logoSvg} alt="RAG Masterclass" className="h-7" />
          </div>
          {user?.email && (
            <UserMenu email={user.email} onSignOut={handleSignOut} isAdmin={isAdmin} />
          )}
        </div>
        {mobileOpen && (
          <div className="space-y-2 border-b p-3">
            <nav>{nav}</nav>
            {sidebar && <div className="max-h-64 overflow-y-auto">{sidebar}</div>}
          </div>
        )}
        <div className="min-h-0 flex-1">{children}</div>
      </div>

      {/* Desktop main */}
      <div className="hidden min-w-0 flex-1 md:block">{children}</div>
    </div>
  )
}
