import { useParams } from 'react-router-dom'

import { SessionDashboardPanel } from '@/components/game/session-dashboard-panel'
import { AppHeader } from '@/components/layout/app-header'

const DashboardPage = () => {
    const { sessionId } = useParams()

    return (
        <div className="flex min-h-svh flex-col">
            <AppHeader />
            <main className="mx-auto flex w-full max-w-2xl flex-col gap-8 p-4">
                <SessionDashboardPanel sessionId={sessionId} />
            </main>
        </div>
    )
}

export { DashboardPage }
