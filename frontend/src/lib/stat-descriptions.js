/**
 * Full name + one-sentence plain-language definition for every abbreviated
 * stat shown on the Stats page -- nothing like this existed anywhere in
 * the app before Part 15 Phase 5, so these are authored here rather than
 * reused from elsewhere. Keyed by the same short label the page already
 * renders (StatTile/StatRadialGauge `label` props), so a tooltip can be
 * looked up directly from the label already on screen.
 */
const STAT_DESCRIPTIONS = {
    'Sessions played': 'The total number of poker sessions you have started.',
    'Sessions won': 'Ended sessions where your bankroll finished higher than it started -- in-progress sessions are not counted either way yet.',
    'Hands played': 'The total number of individual hands you have been dealt, across every session.',
    'Hands won': 'Hands you won outright or split with another player at showdown.',
    'All-time winnings': 'Your total bankroll change across every session, added together.',
    'Biggest win': 'The largest single-hand amount you have won.',
    'Biggest loss': 'The largest single-hand amount you have lost.',
    VPIP: 'Voluntarily Put money In Pot -- the percentage of hands where you called or raised preflop, rather than folding or only posting a forced blind. A high VPIP means you are playing a lot of hands.',
    PFR: 'Preflop Raise -- the percentage of hands where your first preflop action was a raise, rather than just calling. Comparing PFR to VPIP shows how often you raise versus just call when you play a hand.',
    '3-bet': 'The percentage of hands, among those where you faced an existing preflop raise, where you re-raised (the third bet of the round, after the blind and the first raise).',
    ATS: 'Attempt To Steal -- of the hands where you were on the button and everyone folded to you preflop, the percentage where you raised to try to win the blinds uncontested.',
    WTSD: 'Went To ShowDown -- the percentage of all hands that reached a genuine showdown (more than one player still in at the river), rather than ending early when everyone but one player folded.',
    'W$SD': 'Won money at ShowDown -- of the hands that reached a real showdown, the percentage you won.',
    WWSF: 'Won When Saw Flop -- of the hands where you did not fold preflop and a flop was actually dealt, the percentage you went on to win.',
    'Aggression factor': 'The ratio of your raises to your calls across every street -- higher means you tend to raise rather than just call when you get involved in a pot.',
    'Win %': 'The percentage of your hands that you won outright.',
    'Loss %': 'The percentage of your hands that you lost at showdown.',
    'Split %': 'The percentage of your hands that ended in a split pot (a tie at showdown).',
    'Fold %': 'The percentage of your hands where you folded before showdown.',
}

export { STAT_DESCRIPTIONS }
