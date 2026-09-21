import { useEffect, useRef, useState } from 'react'

import { PlayStyleRadarChart } from '@/components/dashboard/play-style-radar-chart'
import { StatRadialGauge } from '@/components/dashboard/stat-radial-gauge'
import { AppHeader } from '@/components/layout/app-header'
import { AnimatedText } from '@/components/ui/animated-shiny-text'
import { BorderBeam, EDUCATION_BORDER_BEAM_PROPS } from '@/components/ui/border-beam'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useAuth } from '@/hooks/use-auth'
import { useUserStats } from '@/hooks/use-user-stats'
import { formatCurrency } from '@/lib/format'
import { STAT_DESCRIPTIONS } from '@/lib/stat-descriptions'

const ABOUT_YOU_GRADIENT =
    'linear-gradient(90deg, rgba(255,255,255,0.03), rgba(255,255,255,0.16), rgba(255,255,255,0.03))'

// Matches stat-tile.jsx's own good/critical/neutral tokens -- kept local
// (not reused from StatTile) since the "Player Snapshot" tiles need this
// page's translucent BorderBeam look, not StatTile's shared solid-card
// style still used on Dashboard/Stats.
const SNAPSHOT_VARIANT_CLASSES = {
    good: 'text-green-600',
    critical: 'text-red-600',
    neutral: 'text-foreground',
}

const SnapshotTile = ({ label, value, variant = 'neutral' }) => (
    <BorderBeam {...EDUCATION_BORDER_BEAM_PROPS}>
        <div className="flex flex-col items-center gap-1 rounded-lg border border-border bg-transparent p-4">
            <p className="text-sm text-muted-foreground">{label}</p>
            <p className={`text-xl font-semibold tabular-nums ${SNAPSHOT_VARIANT_CLASSES[variant]}`}>{value}</p>
        </div>
    </BorderBeam>
)

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
 * avatar_url may be a pasted image URL OR a data: URL produced by
 * compressImageFileToDataUrl below -- either way it's just a string this
 * component renders, so a broken/unreachable link is a real, expected
 * case, not just an edge case -- the onError fallback covers that, not
 * just the "no URL set at all" case.
 */
const AvatarPreview = ({ avatarUrl, fallbackLabel }) => {
    const [imageFailed, setImageFailed] = useState(false)

    useEffect(() => {
        setImageFailed(false)
    }, [avatarUrl])

    const content =
        avatarUrl && !imageFailed ? (
            <img
                src={avatarUrl}
                alt="Profile avatar"
                onError={() => setImageFailed(true)}
                className="h-20 w-20 rounded-full object-cover"
            />
        ) : (
            <div
                aria-hidden={Boolean(avatarUrl)}
                className="flex h-20 w-20 items-center justify-center rounded-full bg-muted text-xl font-semibold text-muted-foreground"
            >
                {initialsFrom(fallbackLabel)}
            </div>
        )

    return (
        <BorderBeam {...EDUCATION_BORDER_BEAM_PROPS} size="sm">
            {content}
        </BorderBeam>
    )
}

const AVATAR_THUMBNAIL_SIZE = 64
// Matches the backend's avatar_url column (String(2048) -- see
// backend/models/user.py). This project has no object storage, so an
// uploaded or captured photo has to actually fit in that text column as a
// data URL -- hence the aggressive downscale + step-down JPEG
// recompression below, not just a plain FileReader.readAsDataURL().
const MAX_AVATAR_URL_LENGTH = 2048

const compressImageFileToDataUrl = (file) =>
    new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onerror = () => reject(new Error('Could not read that file.'))
        reader.onload = () => {
            const img = new Image()
            img.onerror = () => reject(new Error('That file is not a valid image.'))
            img.onload = () => {
                const canvas = document.createElement('canvas')
                canvas.width = AVATAR_THUMBNAIL_SIZE
                canvas.height = AVATAR_THUMBNAIL_SIZE
                const ctx = canvas.getContext('2d')
                // Center-crop to a square from the image's shorter side
                // before scaling down, so the thumbnail isn't stretched.
                const side = Math.min(img.width, img.height)
                ctx.drawImage(
                    img,
                    (img.width - side) / 2,
                    (img.height - side) / 2,
                    side,
                    side,
                    0,
                    0,
                    AVATAR_THUMBNAIL_SIZE,
                    AVATAR_THUMBNAIL_SIZE,
                )

                let quality = 0.7
                let dataUrl = canvas.toDataURL('image/jpeg', quality)
                while (dataUrl.length > MAX_AVATAR_URL_LENGTH && quality > 0.1) {
                    quality -= 0.1
                    dataUrl = canvas.toDataURL('image/jpeg', quality)
                }
                if (dataUrl.length > MAX_AVATAR_URL_LENGTH) {
                    reject(new Error('That photo is still too large even compressed -- try a simpler image.'))
                    return
                }
                resolve(dataUrl)
            }
            img.src = reader.result
        }
        reader.readAsDataURL(file)
    })

/**
 * Edits display_name/bio/avatar_url (PATCH /auth/me, via useAuth's
 * updateProfile) and shows a read-only snapshot of the account-wide stats
 * Part 12 Phase 7 already computes (GET /users/me/stats) -- reusing that
 * endpoint rather than duplicating its aggregation logic. A full-form
 * save, not a partial patch: every field is sent on every submit, and an
 * emptied field clears that column server-side (see UpdateProfileRequest).
 *
 * The avatar picker offers three ways to set avatar_url -- paste a web
 * URL, upload a file, or capture a photo -- rather than one always-visible
 * URL field, but all three still resolve to that same single string
 * column; there's no separate image-storage path on the backend.
 */
const ProfilePage = () => {
    const { user, updateProfile } = useAuth()
    const { getMyStats } = useUserStats()

    const [displayName, setDisplayName] = useState('')
    const [bio, setBio] = useState('')
    const [avatarUrl, setAvatarUrl] = useState('')
    const [avatarSource, setAvatarSource] = useState(null)
    const [avatarError, setAvatarError] = useState('')
    const [stats, setStats] = useState(null)
    const [isSaving, setIsSaving] = useState(false)
    const [errorMessage, setErrorMessage] = useState('')
    const [savedMessage, setSavedMessage] = useState('')

    const fileInputRef = useRef(null)
    const cameraInputRef = useRef(null)

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

    const handleAvatarFile = async (event) => {
        const file = event.target.files?.[0]
        event.target.value = ''
        if (!file) {
            return
        }

        setAvatarError('')
        try {
            setAvatarUrl(await compressImageFileToDataUrl(file))
        } catch (error) {
            setAvatarError(error.message)
        }
    }

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
        <div className="relative flex min-h-svh flex-col overflow-hidden">
            <AppHeader />
            <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
                <AnimatedText
                    text="ABOUT YOU"
                    gradientColors={ABOUT_YOU_GRADIENT}
                    gradientAnimationDuration={2.5}
                    textClassName="font-black tracking-wide text-[14vw] sm:text-[14vw] md:text-[14vw] lg:text-[14vw] xl:text-[14vw] leading-none whitespace-nowrap"
                />
            </div>
            <main className="relative z-10 mx-auto mt-8 flex w-full max-w-2xl flex-col gap-8 rounded-xl border-2 border-white/25 p-6 pb-16 sm:mt-12 sm:p-10">
                <h1 className="text-xl font-semibold">Your Profile:</h1>

                <div className="flex items-center gap-4">
                    <AvatarPreview avatarUrl={avatarUrl} fallbackLabel={displayName || user.email} />
                    <div>
                        <p className="font-medium">{displayName || user.email}</p>
                        <p className="text-sm text-muted-foreground">{user.email}</p>
                    </div>
                </div>

                <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                    <BorderBeam {...EDUCATION_BORDER_BEAM_PROPS}>
                        <div className="flex flex-col gap-3 rounded-lg border border-border bg-transparent p-4">
                            <Label>Profile Photo:</Label>
                            <div className="flex flex-wrap gap-2">
                                <Button
                                    type="button"
                                    variant="outline"
                                    size="sm"
                                    onClick={() => setAvatarSource(avatarSource === 'web' ? null : 'web')}
                                >
                                    From The Web
                                </Button>
                                <Button
                                    type="button"
                                    variant="outline"
                                    size="sm"
                                    onClick={() => fileInputRef.current?.click()}
                                >
                                    Upload A Photo
                                </Button>
                                <Button
                                    type="button"
                                    variant="outline"
                                    size="sm"
                                    onClick={() => cameraInputRef.current?.click()}
                                >
                                    Take A Photo
                                </Button>
                            </div>
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept="image/*"
                                className="hidden"
                                onChange={handleAvatarFile}
                            />
                            <input
                                ref={cameraInputRef}
                                type="file"
                                accept="image/*"
                                capture="user"
                                className="hidden"
                                onChange={handleAvatarFile}
                            />
                            {avatarSource === 'web' && (
                                <Input
                                    type="url"
                                    placeholder="https://..."
                                    value={avatarUrl}
                                    onChange={(event) => setAvatarUrl(event.target.value)}
                                    maxLength={2048}
                                />
                            )}
                            {avatarError && <p className="text-sm text-destructive">{avatarError}</p>}
                        </div>
                    </BorderBeam>

                    <BorderBeam {...EDUCATION_BORDER_BEAM_PROPS}>
                        <div className="flex flex-col gap-2 rounded-lg border border-border bg-transparent p-4">
                            <Label htmlFor="display-name">Display Name:</Label>
                            <Input
                                id="display-name"
                                value={displayName}
                                onChange={(event) => setDisplayName(event.target.value)}
                                maxLength={100}
                            />
                        </div>
                    </BorderBeam>

                    <BorderBeam {...EDUCATION_BORDER_BEAM_PROPS}>
                        <div className="flex flex-col gap-2 rounded-lg border border-border bg-transparent p-4">
                            <Label htmlFor="bio">Bio/About:</Label>
                            <Textarea id="bio" value={bio} onChange={(event) => setBio(event.target.value)} maxLength={500} />
                        </div>
                    </BorderBeam>

                    <Card>
                        <CardContent className="flex flex-col gap-4 pt-6">
                            {errorMessage && <p className="text-sm text-destructive">{errorMessage}</p>}
                            {savedMessage && <p className="text-sm text-green-600">{savedMessage}</p>}
                            <Button type="submit" disabled={isSaving}>
                                {isSaving ? 'Saving...' : 'Save Profile:'}
                            </Button>
                        </CardContent>
                    </Card>
                </form>

                {stats && stats.total_sessions > 0 && (
                    <section className="flex flex-col gap-3">
                        <h2 className="text-lg font-semibold">Player Snapshot:</h2>
                        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                            <SnapshotTile label="Sessions Played:" value={stats.total_sessions} />
                            <SnapshotTile label="Hands Played:" value={stats.total_hands} />
                            <SnapshotTile
                                label="Cumulative Change:"
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

                {stats && stats.total_hands > 0 && (
                    <section className="flex flex-col gap-3">
                        <h2 className="text-lg font-semibold">Play Style:</h2>
                        <div className="flex justify-center gap-16">
                            <StatRadialGauge
                                label="VPIP"
                                value={stats.vpip_rate}
                                statKey="vpip"
                                tooltip={STAT_DESCRIPTIONS.VPIP}
                            />
                            <StatRadialGauge
                                label="WTSD"
                                value={stats.wtsd_rate}
                                statKey="wtsd"
                                tooltip={STAT_DESCRIPTIONS.WTSD}
                            />
                        </div>
                        <PlayStyleRadarChart stats={stats} />
                    </section>
                )}
            </main>
        </div>
    )
}

export { ProfilePage }
