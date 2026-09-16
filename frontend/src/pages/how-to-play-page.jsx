import { AppHeader } from '@/components/layout/app-header'
import { GlossaryEntry } from '@/components/education/glossary-entry'
import { HandRankings } from '@/components/education/hand-rankings'
import { StartingHandMatrix } from '@/components/education/starting-hand-matrix'
import { StreetProgression } from '@/components/education/street-progression'

/**
 * A public, no-login-required tutorial (Part 14 Phase 2) for a first-time
 * player -- registered outside ProtectedRoute in app.jsx so it renders
 * the same whether or not `user` is set. Pure static content, no backend
 * calls: plain-language explanations of hands/streets/actions/showdown,
 * plus a glossary reused (via GlossaryEntry) by the Kelly Criterion page.
 */
const HowToPlayPage = () => (
    <div className="dark flex min-h-svh flex-col bg-background text-foreground">
        <AppHeader />
        <main className="mx-auto flex w-full max-w-3xl flex-col gap-10 p-4 pb-16">
            <div className="flex flex-col gap-2 pt-4">
                <h1 className="text-3xl font-bold">How to Play</h1>
                <p className="text-muted-foreground">
                    A quick guide to Texas Hold'em -- the poker variant this simulator plays -- for
                    anyone picking it up for the first time.
                </p>
            </div>

            <section className="flex flex-col gap-3">
                <h2 className="text-xl font-semibold">Your hand</h2>
                <p>
                    At the start of every hand, you and each opponent are dealt two private cards --
                    your <strong>hole cards</strong>. Only you can see yours; everyone else's stay
                    hidden unless the hand goes all the way to showdown. Over the course of the hand,
                    five shared cards are also dealt face-up in the middle of the table -- the{' '}
                    <strong>community cards</strong>, or <strong>board</strong>. Your final hand is
                    the best 5-card combination you can make from your 2 hole cards and the 5
                    community cards together.
                </p>
            </section>

            <section className="flex flex-col gap-3">
                <h2 className="text-xl font-semibold">Hand rankings</h2>
                <p>
                    When a hand reaches showdown, these are the categories a 5-card hand can fall
                    into, from weakest to strongest -- a higher-ranked category always beats a
                    lower one, regardless of the actual card values involved.
                </p>
                <HandRankings />
            </section>

            <section className="flex flex-col gap-3">
                <h2 className="text-xl font-semibold">The four streets</h2>
                <p>Betting happens in four rounds, called streets, as more of the board is revealed:</p>
                <StreetProgression />
                <p>
                    A betting round happens after each street. A hand can end early on any street --
                    it doesn't need to reach the river if everyone but one player folds.
                </p>
            </section>

            <section className="flex flex-col gap-3">
                <h2 className="text-xl font-semibold">Starting hand strength</h2>
                <p>
                    Not all starting hands are equal. This chart scores all 169 possible starting
                    hand classes using the widely-cited "Chen Formula" -- pairs on the diagonal,
                    suited combos above it, offsuit combos below -- from strongest (green) to
                    weakest (red). <strong>7-2 offsuit</strong> famously scores among the very worst,
                    which is exactly why it's the poker community's go-to example of the worst hand
                    in Hold'em.
                </p>
                <StartingHandMatrix />
            </section>

            <section className="flex flex-col gap-3">
                <h2 className="text-xl font-semibold">Your options: check, call, fold, raise</h2>
                <ul className="flex flex-col gap-2 pl-5">
                    <li className="list-disc">
                        <strong>Check</strong> -- pass the action along without betting anything.
                        Only possible when nobody has bet yet on this street.
                    </li>
                    <li className="list-disc">
                        <strong>Call</strong> -- match the current bet to stay in the hand.
                    </li>
                    <li className="list-disc">
                        <strong>Fold</strong> -- give up the hand, forfeiting anything you've already
                        put in the pot. Costs nothing further, but you can't win this hand.
                    </li>
                    <li className="list-disc">
                        <strong>Raise</strong> -- increase the bet beyond what's needed to call,
                        putting pressure on everyone still in the hand.
                    </li>
                </ul>
            </section>

            <section className="flex flex-col gap-3">
                <h2 className="text-xl font-semibold">Showdown</h2>
                <p>
                    If more than one player is still in the hand after the river's betting round, all
                    remaining hands are revealed and compared -- the <strong>showdown</strong>. The
                    best 5-card hand wins the pot. If two or more hands tie exactly, the pot splits
                    evenly between them. If everyone but one player folds at any point before
                    showdown, that player wins the pot uncontested -- their cards are never revealed.
                </p>
            </section>

            <section className="flex flex-col gap-3">
                <h2 className="text-xl font-semibold">Glossary</h2>
                <dl className="flex flex-col gap-3">
                    <GlossaryEntry term="Blinds (small blind / big blind)">
                        Forced bets posted by the two players to the left of the dealer button before
                        any cards are dealt, to make sure there's always something in the pot worth
                        playing for.
                    </GlossaryEntry>
                    <GlossaryEntry term="Button">
                        The dealer position for the hand, marked with a "D" -- it rotates one seat to
                        the left every hand.
                    </GlossaryEntry>
                    <GlossaryEntry term="Pot">The total amount everyone has bet this hand, awarded to whoever wins it.</GlossaryEntry>
                    <GlossaryEntry term="Pot odds">
                        The ratio of the current bet to the pot, used to judge whether calling is
                        worth it given your chance of winning.
                    </GlossaryEntry>
                    <GlossaryEntry term="Equity">
                        Your estimated probability of winning the hand right now, given the cards
                        seen so far -- shown live in this simulator whenever you face a decision.
                    </GlossaryEntry>
                    <GlossaryEntry term="All-in">
                        Betting your entire remaining stack. You can't be forced to bet more than
                        you have.
                    </GlossaryEntry>
                    <GlossaryEntry term="Side pot">
                        A separate pot that forms when an all-in player can't match a later bet --
                        it's contested only by the players who put in enough to be eligible for it.
                    </GlossaryEntry>
                </dl>
            </section>
        </main>
    </div>
)

export { HowToPlayPage }
