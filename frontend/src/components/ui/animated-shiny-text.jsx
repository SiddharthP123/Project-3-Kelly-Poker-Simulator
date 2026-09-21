import { motion } from 'framer-motion'
import { forwardRef, useState } from 'react'

import { cn } from '@/lib/utils'

const textVariants = {
    initial: { backgroundPosition: '0 0' },
    animate: {
        backgroundPosition: '100% 0',
    },
}

/**
 * A large heading whose gradient fill sweeps back and forth across the
 * letters (background-clip:text + an animated backgroundPosition), from
 * the 21st.dev "Animated Shiny Text" bookmark -- converted from its TSX
 * source to this project's JSX, framer-motion `Variants` type dropped
 * since JS has no type imports.
 */
const AnimatedText = forwardRef(
    (
        {
            text,
            gradientColors = 'linear-gradient(90deg, #000, #fff, #000)',
            gradientAnimationDuration = 1,
            hoverEffect = false,
            className,
            textClassName,
            ...props
        },
        ref,
    ) => {
        const [isHovered, setIsHovered] = useState(false)

        return (
            <div ref={ref} className={cn('flex items-center justify-center py-8', className)} {...props}>
                <motion.h1
                    className={cn(
                        'text-[2.5rem] leading-normal sm:text-[3.5rem] md:text-[4rem] lg:text-[5rem] xl:text-[6rem]',
                        textClassName,
                    )}
                    style={{
                        background: gradientColors,
                        backgroundSize: '200% auto',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        textShadow: isHovered ? '0 0 8px rgba(255,255,255,0.3)' : 'none',
                    }}
                    variants={textVariants}
                    initial="initial"
                    animate="animate"
                    transition={{
                        duration: gradientAnimationDuration,
                        repeat: Infinity,
                        repeatType: 'reverse',
                    }}
                    onHoverStart={() => hoverEffect && setIsHovered(true)}
                    onHoverEnd={() => hoverEffect && setIsHovered(false)}
                >
                    {text}
                </motion.h1>
            </div>
        )
    },
)
AnimatedText.displayName = 'AnimatedText'

export { AnimatedText }
