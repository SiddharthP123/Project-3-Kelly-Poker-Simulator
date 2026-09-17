import { BorderBeam } from 'border-beam'

export { BorderBeam }
export default BorderBeam

/**
 * border-beam's rotation/hue animation is driven by a single shared
 * requestAnimationFrame loop keyed off page-navigation time, not a
 * per-instance timer -- so any two instances with identical size/
 * colorVariant/theme/duration are mathematically in phase on every frame,
 * with no randomness in the library to fight. The only way to get
 * `education` pages' many BorderBeam-wrapped boxes to visibly move in
 * sync is to make sure every single instance is handed the exact same
 * props -- hence this one shared object instead of retyping (and risking
 * drift on) the same 4 values at every call site.
 */
const EDUCATION_BORDER_BEAM_PROPS = { size: 'md', colorVariant: 'colorful', theme: 'dark', duration: 2.5 }

export { EDUCATION_BORDER_BEAM_PROPS }
