import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'

import { ProtectedRoute } from '@/components/layout/protected-route'
import { KineticGrid } from '@/components/ui/kinetic-grid'

// Lazy-loaded per route so the initial bundle only ships the code the
// first page actually needs -- recharts/framer-motion-heavy pages like
// StatsPage and GamePage load on demand instead of up front (this took
// the single production JS chunk from ~1.06 MB to a small shared chunk
// plus one chunk per page).
const DashboardPage = lazy(() => import('@/pages/dashboard-page').then((m) => ({ default: m.DashboardPage })))
const GamePage = lazy(() => import('@/pages/game-page').then((m) => ({ default: m.GamePage })))
const HowToPlayPage = lazy(() => import('@/pages/how-to-play-page').then((m) => ({ default: m.HowToPlayPage })))
const KellyCriterionPage = lazy(() =>
    import('@/pages/kelly-criterion-page').then((m) => ({ default: m.KellyCriterionPage })),
)
const LobbyPage = lazy(() => import('@/pages/lobby-page').then((m) => ({ default: m.LobbyPage })))
const LoginPage = lazy(() => import('@/pages/login-page').then((m) => ({ default: m.LoginPage })))
const ProfilePage = lazy(() => import('@/pages/profile-page').then((m) => ({ default: m.ProfilePage })))
const SignupPage = lazy(() => import('@/pages/signup-page').then((m) => ({ default: m.SignupPage })))
const StatsPage = lazy(() => import('@/pages/stats-page').then((m) => ({ default: m.StatsPage })))

const RouteFallback = () => <p className="p-4 text-center text-muted-foreground">Loading...</p>

// A single app-wide KineticGrid instance (not one per page) -- mounted
// here, above the router, so it's one persistent canvas + one
// mousemove/click listener for the whole session instead of tearing
// down and recreating the RAF loop on every navigation. Individual pages
// no longer paint their own opaque background (see e.g. lobby-page.jsx's
// removed "dark bg-background" wrapper) so this shows through everywhere.
const App = () => (
    <KineticGrid globalColor="monochrome" className="dark text-foreground">
        <Suspense fallback={<RouteFallback />}>
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
        </Suspense>
    </KineticGrid>
)

export { App }
