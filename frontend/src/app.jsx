import { Navigate, Route, Routes } from 'react-router-dom'

import { ProtectedRoute } from '@/components/layout/protected-route'
import { DashboardPage } from '@/pages/dashboard-page'
import { GamePage } from '@/pages/game-page'
import { LobbyPage } from '@/pages/lobby-page'
import { LoginPage } from '@/pages/login-page'
import { SignupPage } from '@/pages/signup-page'

const App = () => (
    <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />

        <Route element={<ProtectedRoute />}>
            <Route path="/" element={<LobbyPage />} />
            <Route path="/sessions/:sessionId/play" element={<GamePage />} />
            <Route path="/sessions/:sessionId/dashboard" element={<DashboardPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
)

export { App }
