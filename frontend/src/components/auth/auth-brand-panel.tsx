import { CheckIcon, SquareCheckBigIcon } from 'lucide-react'

const HIGHLIGHTS = [
  'Projetos e tarefas ilimitados',
  'Visualização em lista e Kanban',
  'Colaboração em equipe em breve',
]

/**
 * Left-hand marketing panel shared by the login and register screens.
 * Hidden below the `lg` breakpoint — on mobile only the form is shown.
 */
export function AuthBrandPanel() {
  return (
    <div className="relative hidden overflow-hidden bg-gradient-to-br from-navy-950 via-navy-900 to-brand-800 p-12 text-white lg:flex lg:flex-col lg:justify-center xl:p-16">
      <div className="pointer-events-none absolute -right-24 top-1/4 size-96 rounded-full bg-brand-400/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-24 -left-16 size-80 rounded-full bg-brand-500/10 blur-3xl" />

      <div className="relative max-w-md">
        <div className="flex items-center gap-3">
          <span className="flex size-10 items-center justify-center rounded-xl bg-white/10 ring-1 ring-white/15">
            <SquareCheckBigIcon className="size-5" />
          </span>
          <span className="text-xl font-bold tracking-tight">Taskly</span>
        </div>

        <h1 className="mt-14 text-4xl font-bold leading-[1.15] tracking-tight">
          Organize o que importa de verdade.
        </h1>
        <p className="mt-5 text-base leading-relaxed text-white/70">
          Gerencie projetos, acompanhe tarefas e mantenha o foco — tudo em um lugar
          simples e bonito.
        </p>

        <ul className="mt-10 space-y-3.5">
          {HIGHLIGHTS.map((item) => (
            <li key={item} className="flex items-center gap-3 text-sm text-white/85">
              <span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-emerald-400/20 text-emerald-300">
                <CheckIcon className="size-3" />
              </span>
              {item}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
