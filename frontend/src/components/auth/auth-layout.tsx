import type { ReactNode } from 'react'
import { SquareCheckBigIcon } from 'lucide-react'
import { AuthBrandPanel } from '@/components/auth/auth-brand-panel'

/** Two-column auth shell: brand panel (lg+) on the left, form slot on the right. */
export function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="grid min-h-svh lg:grid-cols-2">
      <AuthBrandPanel />

      <div className="flex items-center justify-center bg-background px-6 py-12">
        <div className="w-full max-w-sm">
          <div className="mb-8 flex items-center gap-2 text-navy-900 lg:hidden">
            <span className="flex size-8 items-center justify-center rounded-lg bg-navy-900 text-white">
              <SquareCheckBigIcon className="size-4" />
            </span>
            <span className="text-lg font-bold">Taskly</span>
          </div>
          {children}
        </div>
      </div>
    </div>
  )
}
