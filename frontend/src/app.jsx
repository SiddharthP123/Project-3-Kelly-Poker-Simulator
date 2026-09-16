import { Navigate, Route, Routes } from 'react-router-dom'

import { ProtectedRoute } from '@/components/layout/protected-route'
import { DashboardPage } from '@/pages/dashboard-page'
import { GamePage } from '@/pages/game-page'
import { HowToPlayPage } from '@/pages/how-to-play-page'
import { KellyCriterionPage } from '@/pages/kelly-criterion-page'
import { LobbyPage } from '@/pages/lobby-page'
import { LoginPage } from '@/pages/login-page'
import { ProfilePage } from '@/pages/profile-page'
import { SignupPage } from '@/pages/signup-page'
import { StatsPage } from '@/pages/stats-page'

const App = () => (
    <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/how-to-play" element={<HowToPlayPage />} />
        <Route path="/kelly-criterion" element={<KellyCriterionPage />} />

        <Route element={<ProtectedRoute />}>
            <Route path="/" element={<LobbyPage />} />
            <Route path="/sessions/:sessionId/play" element={<GamePage />} />
            <Route path="/sessions/:sessionId/dashboard" element={<DashboardPage />} />
            <Route path="/stats" element={<StatsPage />} />
            <Route path="/profile" element={<ProfilePage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
)

export { App }
