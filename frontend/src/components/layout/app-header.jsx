import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { useAuth } from '@/hooks/use-auth'

const AppHeader = () => {
    const { user, logout } = useAuth()

    return (
        <header className="flex items-center justify-between border-b px-6 py-4">
            <Link to="/" className="text-xl font-bold">
                Kelly Poker Simulator
            </Link>
            {user && (
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
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
                </div>
            )}
        </header>
    )
}

export { AppHeader }
