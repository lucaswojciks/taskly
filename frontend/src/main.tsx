import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import App from '@/App'
import { Toaster } from '@/components/ui/sonner'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      // 'always' so a failed request surfaces an error the user can retry,
      // instead of pausing silently when the browser thinks it is offline.
      networkMode: 'always',
      refetchOnWindowFocus: false,
      staleTime: 30_000,
    },
    mutations: {
      networkMode: 'always',
    },
  },
})

const rootElement = document.getElementById('root')
if (!rootElement) {
  throw new Error('Root element #root not found')
}

createRoot(rootElement).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
      <Toaster richColors position="top-right" />
    </QueryClientProvider>
  </StrictMode>,
)
