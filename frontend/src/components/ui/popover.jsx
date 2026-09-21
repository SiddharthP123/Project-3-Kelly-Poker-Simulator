'use client'

import { Popover as PopoverPrimitive } from 'radix-ui'

import { cn } from '@/lib/utils'

function Popover({ ...props }) {
    return <PopoverPrimitive.Root data-slot="popover" {...props} />
}

function PopoverTrigger({ ...props }) {
    return <PopoverPrimitive.Trigger data-slot="popover-trigger" {...props} />
}

function PopoverContent({ className, align = 'center', sideOffset = 8, ...props }) {
    return (
        <PopoverPrimitive.Portal>
            <PopoverPrimitive.Content
                data-slot="popover-content"
                align={align}
                sideOffset={sideOffset}
                className={cn(
                    'z-50 rounded-lg border border-border bg-popover p-2 text-popover-foreground shadow-md outline-none data-open:animate-in data-open:fade-in-0 data-open:zoom-in-95 data-closed:animate-out data-closed:fade-out-0 data-closed:zoom-out-95',
                    className,
                )}
                {...props}
            />
        </PopoverPrimitive.Portal>
    )
}

export { Popover, PopoverTrigger, PopoverContent }
