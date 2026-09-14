import { useEffect, useState } from 'react'

import { StatTile } from '@/components/dashboard/stat-tile'
import { AppHeader } from '@/components/layout/app-header'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useAuth } from '@/hooks/use-auth'
import { useUserStats } from '@/hooks/use-user-stats'
import { formatCurrency } from '@/lib/format'

const initialsFrom = (label) => {
    const trimmed = (label || '').trim()
    if (!trimmed) {
        return '?'
    }
    const parts = trimmed.split(/\s+/)
    const initials = parts.length > 1 ? `${parts[0][0]}${parts[parts.length - 1][0]}` : trimmed.slice(0, 2)
    return initials.toUpperCase()
}

/**
 * avatar_url is a pasted image URL (Part 13 Phase 3 -- no file upload,
 * this project has no object storage), so a broken/unreachable link is a
 * real, expected case, not just an edge case -- the onError fallback
 * covers that, not just the "no URL set at all" case.
 */
const AvatarPreview = ({ avatarUrl, fallbackLabel }) => {
    const [imageFailed, setImageFailed] = useState(false)

    useEffect(() => {
        setImageFailed(false)
    }, [avatarUrl])

    if (avatarUrl && !imageFailed) {
        return (
            <img
                src={avatarUrl}
                alt="Profile avatar"
                onError={() => setImageFailed(true)}
                className="h-20 w-20 rounded-full object-cover"
            />
        )
    }

    return (
        <div
            aria-hidden={Boolean(avatarUrl)}
            className="flex h-20 w-20 items-center justify-center rounded-full bg-muted text-xl font-semibold text-muted-foreground"
        >
            {initialsFrom(fallbackLabel)}
        </div>
    )
}

/**
 * Edits display_name/bio/avatar_url (PATCH /auth/me, via useAuth's
 * updateProfile) and shows a read-only snapshot of the account-wide stats
 * Part 12 Phase 7 already computes (GET /users/me/stats) -- reusing that
 * endpoint rather than duplicating its aggregation logic. A full-form
 * save, not a partial patch: every field is sent on every submit, and an
 * emptied field clears that column server-side (see UpdateProfileRequest).
 */
const ProfilePage = () => {
    const { user, updateProfile } = useAuth()
    const { getMyStats } = useUserStats()

    const [displayName, setDisplayName] = useState('')
    const [bio, setBio] = useState('')
    const [avatarUrl, setAvatarUrl] = useState('')
    const [stats, setStats] = useState(null)
    const [isSaving, setIsSaving] = useState(false)
    const [errorMessage, setErrorMessage] = useState('')
    const [savedMessage, setSavedMessage] = useState('')

    useEffect(() => {
        if (user) {
            setDisplayName(user.display_name || '')
            setBio(user.bio || '')
            setAvatarUrl(user.avatar_url || '')
        }
    }, [user])

    useEffect(() => {
        // The stats snapshot is a nice-to-have on this page (the full
        // breakdown already lives at /stats) -- a failed fetch here
        // shouldn't block editing the profile form itself.
        getMyStats()
            .then(setStats)
            .catch(() => {})
    }, [getMyStats])

    const handleSubmit = async (event) => {
        event.preventDefault()
        setErrorMessage('')
        setSavedMessage('')
        setIsSaving(true)

        try {
            await updateProfile({ display_name: displayName, bio, avatar_url: avatarUrl })
            setSavedMessage('Profile saved.')
        } catch (error) {
            setErrorMessage(error.detail || 'Could not save your profile')
        } finally {
            setIsSaving(false)
        }
    }

    if (!user) {
        return (
            <div className="flex min-h-svh flex-col">
                <AppHeader />
                <p className="p-4 text-center text-muted-foreground">Loading...</p>
            </div>
        )
    }

    return (
        <div className="flex min-h-svh flex-col">
            <AppHeader />
            <main className="mx-auto flex w-full max-w-2xl flex-col gap-8 p-4">
                <h1 className="text-xl font-semibold">Your profile</h1>

                <div className="flex items-center gap-4">
                    <AvatarPreview avatarUrl={avatarUrl} fallbackLabel={displayName || user.email} />
                    <div>
                        <p className="font-medium">{displayName || user.email}</p>
                        <p className="text-sm text-muted-foreground">{user.email}</p>
                    </div>
                </div>

                <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                    <div className="flex flex-col gap-2">
                        <Label htmlFor="display-name">Display name</Label>
                        <Input
                            id="display-name"
                            value={displayName}
                            onChange={(event) => setDisplayName(event.target.value)}
                            maxLength={100}
                        />
                    </div>

                    <div className="flex flex-col gap-2">
                        <Label htmlFor="avatar-url">Avatar URL</Label>
                        <Input
                            id="avatar-url"
                            type="url"
                            placeholder="https://..."
                            value={avatarUrl}
                            onChange={(event) => setAvatarUrl(event.target.value)}
                            maxLength={2048}
                        />
                    </div>

                    <div className="flex flex-col gap-2">
                        <Label htmlFor="bio">Bio</Label>
                        <Textarea
                            id="bio"
                            value={bio}
                            onChange={(event) => setBio(event.target.value)}
                            maxLength={500}
                        />
                    </div>

                    {errorMessage && <p className="text-sm text-destructive">{errorMessage}</p>}
                    {savedMessage && <p className="text-sm text-green-600">{savedMessage}</p>}

                    <Button type="submit" disabled={isSaving}>
                        {isSaving ? 'Saving...' : 'Save profile'}
                    </Button>
                </form>

                {stats && stats.total_sessions > 0 && (
                    <section className="flex flex-col gap-3">
                        <h2 className="text-lg font-semibold">Snapshot</h2>
                        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                            <StatTile label="Sessions played" value={stats.total_sessions} />
                            <StatTile label="Hands played" value={stats.total_hands} />
                            <StatTile
                                label="Cumulative change"
                                value={`${stats.cumulative_bankroll_change >= 0 ? '+' : ''}${formatCurrency(
                                    stats.cumulative_bankroll_change,
                                )}`}
                                variant={
                                    stats.cumulative_bankroll_change > 0
                                        ? 'good'
                                        : stats.cumulative_bankroll_change < 0
                                          ? 'critical'
                                          : 'neutral'
                                }
                            />
                        </div>
                    </section>
                )}
            </main>
        </div>
    )
}

export { ProfilePage }
