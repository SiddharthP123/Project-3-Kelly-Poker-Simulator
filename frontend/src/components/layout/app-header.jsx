import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { useAuth } from '@/hooks/use-auth'

const AppHeader = () => {
    const { user, logout } = useAuth()

    return (
        <header className="sticky top-0 z-20 flex items-center justify-between border-b border-white/10 bg-background/70 px-6 py-4 backdrop-blur-md">
            <Link to="/" className="text-xl font-bold">
                Kelly Poker Simulator
            </Link>
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <Link to="/how-to-play" className="hover:text-foreground">
                    How to Play
                </Link>
                <Link to="/kelly-criterion" className="hover:text-foreground">
                    Kelly Criterion
                </Link>
                {user && (
                    <>
                        <Link to="/stats" className="hover:text-foreground">
                            Stats
                        </Link>
                        <Link to="/profile" className="hover:text-foreground">
                            Profile
                        </Link>
                        <span>{user.display_name || user.email}</span>
                        <Button variant="outline" size="sm" onClick={logout}>
                            Log out
                        </Button>
                    </>
                )}
            </div>
        </header>
    )
}

export { AppHeader }
