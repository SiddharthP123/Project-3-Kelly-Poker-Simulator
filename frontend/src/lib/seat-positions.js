/**
 * Absolute-position layouts (percentages within a relative container) for
 * an oval table, one per opponent count. Hero (seat 0) always sits at the
 * bottom-center -- these arrays cover seats 1..num_opponents only, indexed
 * by (seat_index - 1), arranged in a symmetric arc around the top so the
 * table reads clearly regardless of how many opponents are seated.
 */
const HERO_POSITION = { top: '86%', left: '50%' }

const OPPONENT_LAYOUTS = {
    // top: '14%' mirrors HERO_POSITION's own 86% across the table's
    // center (50%) -- not an arbitrary '10%', which left too little
    // clearance above the seat and let its hole cards clip the table's
    // top edge instead of sitting fully on the felt.
    1: [{ top: '14%', left: '50%' }],
    2: [
        { top: '22%', left: '18%' },
        { top: '22%', left: '82%' },
    ],
    3: [
        { top: '50%', left: '10%' },
        { top: '14%', left: '50%' },
        { top: '50%', left: '90%' },
    ],
    4: [
        { top: '50%', left: '10%' },
        { top: '14%', left: '28%' },
        { top: '14%', left: '72%' },
        { top: '50%', left: '90%' },
    ],
}

/** seatIndex: 0 for hero, 1..4 for opponents. numOpponents: 1-4. */
const getSeatPosition = (seatIndex, numOpponents) => {
    if (seatIndex === 0) {
        return HERO_POSITION
    }

    const layout = OPPONENT_LAYOUTS[numOpponents] || OPPONENT_LAYOUTS[4]
    return layout[seatIndex - 1] || layout[layout.length - 1]
}

export { getSeatPosition }
