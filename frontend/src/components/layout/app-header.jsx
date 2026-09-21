import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { RainbowText } from '@/components/ui/rainbow-text'
import { useAuth } from '@/hooks/use-auth'

const AppHeader = () => {
    const { user, logout } = useAuth()

    return (
        <header className="sticky top-0 z-20 flex items-center justify-between border-b border-white/10 bg-background/70 px-6 py-6 backdrop-blur-md">
            <Link to="/" className="text-xl font-bold">
                <RainbowText>Sid's Kelly Criterion Poker Simulator</RainbowText>
            </Link>
            <div className="flex items-center gap-6 text-sm text-muted-foreground">
                <Link to="/how-to-play" className="hover:text-foreground">
                    Beginner's Guide
                </Link>
                <Link to="/kelly-criterion" className="hover:text-foreground">
                    The Kelly Criterion
                </Link>
                {user && (
                    <>
                        <Link to="/stats" className="hover:text-foreground">
                            Statistics
                        </Link>
                        <Link to="/profile" className="hover:text-foreground">
                            Profile
                        </Link>
                        <span>{user.display_name || user.email}</span>
                        <Button variant="outline" size="sm" onClick={logout}>
                            Log Out
                        </Button>
                    </>
                )}
            </div>
        </header>
    )
}

export { AppHeader }
