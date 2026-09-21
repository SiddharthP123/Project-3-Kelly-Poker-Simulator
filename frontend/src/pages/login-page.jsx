import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { AppFooter } from '@/components/layout/app-footer'
import { AnimatedText } from '@/components/ui/animated-shiny-text'
import { BorderBeam, EDUCATION_BORDER_BEAM_PROPS } from '@/components/ui/border-beam'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAuth } from '@/hooks/use-auth'

const WELCOME_GRADIENT = 'linear-gradient(90deg, rgba(255,255,255,0.03), rgba(255,255,255,0.16), rgba(255,255,255,0.03))'

const LoginPage = () => {
    const { login } = useAuth()
    const navigate = useNavigate()

    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [errorMessage, setErrorMessage] = useState('')
    const [isSubmitting, setIsSubmitting] = useState(false)

    const handleSubmit = async (event) => {
        event.preventDefault()
        setErrorMessage('')
        setIsSubmitting(true)

        try {
            await login(email, password)
            navigate('/')
        } catch (error) {
            setErrorMessage(error.detail || 'Login failed')
        } finally {
            setIsSubmitting(false)
        }
    }

    return (
        <div className="relative flex min-h-svh flex-col overflow-hidden">
            <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
                <AnimatedText
                    text="WELCOME"
                    gradientColors={WELCOME_GRADIENT}
                    gradientAnimationDuration={2.5}
                    textClassName="font-black tracking-wide text-[14vw] sm:text-[14vw] md:text-[14vw] lg:text-[14vw] xl:text-[14vw] leading-none whitespace-nowrap"
                />
            </div>
            <div className="relative z-10 flex flex-1 items-center justify-center p-4">
                <BorderBeam {...EDUCATION_BORDER_BEAM_PROPS} className="w-full max-w-sm">
                <Card className="w-full border-border bg-transparent ring-0">
                    <CardHeader>
                        <CardTitle>Log In:</CardTitle>
                        <CardDescription>
                            Welcome back to Sid's Kelly Criterion Poker Simulator!
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                            <div className="flex flex-col gap-2">
                                <Label htmlFor="email">Email:</Label>
                                <Input
                                    id="email"
                                    type="email"
                                    value={email}
                                    onChange={(event) => setEmail(event.target.value)}
                                    required
                                />
                            </div>
                            <div className="flex flex-col gap-2">
                                <Label htmlFor="password">Password:</Label>
                                <Input
                                    id="password"
                                    type="password"
                                    value={password}
                                    onChange={(event) => setPassword(event.target.value)}
                                    required
                                />
                            </div>
                            {errorMessage && <p className="text-sm text-destructive">{errorMessage}</p>}
                            <Button type="submit" disabled={isSubmitting}>
                                {isSubmitting ? 'Logging In...' : 'Log In'}
                            </Button>
                            <p className="text-center text-sm text-muted-foreground">
                                No Account?{' '}
                                <Link to="/signup" className="underline">
                                    Sign Up Here
                                </Link>
                            </p>
                            <p className="text-center text-sm text-muted-foreground">
                                New To Poker?{' '}
                                <Link to="/how-to-play" className="underline">
                                    Learn How To Play
                                </Link>
                            </p>
                        </form>
                    </CardContent>
                </Card>
                </BorderBeam>
            </div>
            <AppFooter />
        </div>
    )
}

export { LoginPage }
