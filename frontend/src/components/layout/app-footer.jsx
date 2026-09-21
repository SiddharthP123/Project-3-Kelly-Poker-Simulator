import { ExternalLinkIcon, MailIcon } from 'lucide-react'
import { motion, useReducedMotion } from 'framer-motion'

// Adapted from the 21st.dev "Footer Section" bookmark (efferd/footer-section)
// -- kept its fade-in-on-mount treatment, but collapsed the original's
// multi-column SaaS link layout into a single thin row (this app only
// ever needs one author's own details, not whole link sections) with the
// columns replaced by this app's own author/contact details.
const GITHUB_URL = 'https://github.com/SiddharthP123'
const LINKEDIN_URL = 'https://www.linkedin.com/in/siddharth-premanand-71a995253/'
const PRIMARY_EMAIL = 'sp1025@ic.ac.uk'
const SECONDARY_EMAIL = 'ppremanand2017@gmail.com'

const CONNECT_LINKS = [
    { title: 'GitHub', href: GITHUB_URL, icon: ExternalLinkIcon },
    { title: 'LinkedIn', href: LINKEDIN_URL, icon: ExternalLinkIcon },
]

const CONTACT_LINKS = [
    { title: PRIMARY_EMAIL, href: `mailto:${PRIMARY_EMAIL}`, icon: MailIcon },
    { title: SECONDARY_EMAIL, href: `mailto:${SECONDARY_EMAIL}`, icon: MailIcon },
]

const AppFooter = () => {
    const shouldReduceMotion = useReducedMotion()

    const content = (
        <div className="flex w-full flex-nowrap items-center justify-between gap-4 overflow-x-auto whitespace-nowrap">
            <p className="text-sm text-white">
                <span className="font-medium">Siddharth Premanand</span>{' '}
                <span className="text-muted-foreground">
                    &mdash; Imperial College London, MEng Design Engineering Y1
                </span>
            </p>

            <div className="flex flex-nowrap items-center gap-x-4 text-sm">
                <span className="text-white/70">Connect:</span>
                {CONNECT_LINKS.map((link) => (
                    <a
                        key={link.title}
                        href={link.href}
                        target="_blank"
                        rel="noreferrer"
                        className="text-muted-foreground inline-flex items-center gap-1 transition-colors hover:text-foreground"
                    >
                        <link.icon className="size-3.5" />
                        {link.title}
                    </a>
                ))}
                <span className="text-white/70">Contact:</span>
                {CONTACT_LINKS.map((link) => (
                    <a
                        key={link.title}
                        href={link.href}
                        className="text-muted-foreground inline-flex items-center gap-1 transition-colors hover:text-foreground"
                    >
                        <link.icon className="size-3.5" />
                        {link.title}
                    </a>
                ))}
            </div>
        </div>
    )

    return (
        <footer className="w-full shrink-0 border-t border-white/10 px-6 py-5">
            {shouldReduceMotion ? (
                content
            ) : (
                <motion.div
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                >
                    {content}
                </motion.div>
            )}
        </footer>
    )
}

export { AppFooter }
