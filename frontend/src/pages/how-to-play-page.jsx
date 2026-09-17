import { AppHeader } from '@/components/layout/app-header'
import { GlossaryEntry } from '@/components/education/glossary-entry'
import { HandRankings } from '@/components/education/hand-rankings'
import { StartingHandMatrix } from '@/components/education/starting-hand-matrix'
import { StreetProgression } from '@/components/education/street-progression'

/**
 * A public, no-login-required tutorial (Part 14 Phase 2) for a first-time
 * player, registered outside ProtectedRoute in app.jsx so it renders
 * the same whether or not `user` is set. Pure static content, no backend
 * calls: plain-language explanations of hands/streets/actions/showdown,
 * plus a glossary reused (via GlossaryEntry) by the Kelly Criterion page.
 */
const HowToPlayPage = () => (
    <div className="flex min-h-svh flex-col">
        <AppHeader />
        <main className="mx-auto mt-8 flex w-full max-w-3xl flex-col gap-10 rounded-xl border-2 border-white/25 p-6 pb-16 sm:mt-12 sm:p-10">
            <div className="flex flex-col gap-2 pt-4">
                <h1 className="text-3xl font-bold">
                    Sid's Beginner's Guide to Texas Hold'em Poker:
                </h1>
                <p className="text-muted-foreground">
                    Hey guys! My name's Siddharth and I'm a first-year engineering student at
                    Imperial College London. Being a poker enthusiast myself (although not a very
                    good player), I wanted to share my love for the game with you all. I hope this
                    guide helps anyone picking up the game for the first time, and serves as
                    refresher for those who play often. Enjoy!
                </p>
            </div>

            <section className="flex flex-col gap-3">
                <h2 className="text-xl font-semibold">Your Hand:</h2>
                <p>
                    At the start of every hand, you and your opponent(s) are dealt two cards - your{' '}
                    <strong>hole cards</strong>. Only you can see your hole cards, and everyone
                    else's stay hidden unless the hand goes all the way to the showdown. Over the
                    course of the hand, five shared cards are dealt face-up in the middle of the
                    table, which are known as the <strong>community cards</strong>, or the{' '}
                    <strong>board</strong>. Your final hand is the best 5-card combination you can
                    make from your 2 hole cards and the 5 community cards. You can use both, one, or
                    none of your hole cards to make your final hand.
                </p>
            </section>

            <section className="flex flex-col gap-3">
                <h2 className="text-xl font-semibold">Hand Rankings:</h2>
                <p>
                    When a hand reaches showdown, a 5-card hand can fall into 10 categories, listed
                    below from weakest to strongest. A higher-ranked category always beats a
                    lower-ranked one, regardless of the actual card values involved.
                </p>
                <HandRankings />
            </section>

            <section className="flex flex-col gap-3">
                <h2 className="text-xl font-semibold">The Four Stages (Streets):</h2>
                <p>
                    Betting happens in four stages, called streets, as more of the board is
                    revealed. Typically, a card is <strong>burned</strong> (discarded) before each
                    street, done in case the deck has been marked or tampered with. In this
                    simulator,cards are not burned to keep the interface simple.
                </p>
                <StreetProgression />
                <p>
                    A betting round happens after each street. A hand can end early on any street,
                    it doesn't need to reach the river if everyone but one player folds, who ends up
                    winning the pot uncontested.
                </p>
            </section>

            <section className="flex flex-col gap-3">
                <h2 className="text-xl font-semibold">
                    Your Options: Checking, Calling, Folding, and Raising:
                </h2>
                <ul className="flex flex-col gap-2 pl-5">
                    <li className="list-disc">
                        <strong>Check</strong> : you choose to pass the action along without betting
                        anything. This is only possible when nobody has bet yet on this street.
                    </li>
                    <li className="list-disc">
                        <strong>Call</strong> : you choose to match the current bet to stay in the
                        hand.
                    </li>
                    <li className="list-disc">
                        <strong>Fold</strong> : you choose to give up the hand, forfeiting anything
                        you've already put in the pot. Costs nothing further, but you can't win this
                        hand.
                    </li>
                    <li className="list-disc">
                        <strong>Raise</strong> : you choose to increase the bet beyond what's needed
                        to call, putting pressure on everyone still in the hand.
                    </li>
                </ul>
            </section>

            <section className="flex flex-col gap-3">
                <h2 className="text-xl font-semibold">Showdown:</h2>
                <p>
                    If more than one player is still in the hand after the river's betting round,
                    all remaining hands are revealed and compared, known as the{' '}
                    <strong>showdown</strong>. The best 5-card hand wins the pot. If two or more
                    hands tie exactly, the pot splits evenly between them. If everyone but one
                    player folds at any point before the showdown, that player wins the pot
                    uncontested as mentioned earlier, and their cards are never revealed.
                </p>
            </section>

            <section className="flex flex-col gap-3">
                <h2 className="text-xl font-semibold">Common Tactics:</h2>
                <p>
                    Knowing the four options is one thing -- knowing when to reach for each one is
                    the actual game. Here's how beginners generally think about each of them:
                </p>
                <ul className="flex flex-col gap-2 pl-5">
                    <li className="list-disc">
                        <strong>Checking</strong> is your default with a weak or marginal hand when
                        nobody's bet yet -- it costs nothing and lets you see the next card for
                        free instead of putting money in with a hand that isn't ahead.
                    </li>
                    <li className="list-disc">
                        <strong>Calling</strong> makes sense when your hand has a reasonable chance
                        of winning, but not a strong enough one to raise -- you're paying to see
                        more cards or reach showdown without committing extra chips.
                    </li>
                    <li className="list-disc">
                        <strong>Folding</strong> is correct whenever the math below says you're not
                        getting paid enough to call -- giving up a weak hand cheaply beats losing
                        more chips chasing a card that's unlikely to arrive.
                    </li>
                    <li className="list-disc">
                        <strong>Raising</strong> has two very different jobs: raising for{' '}
                        <strong>value</strong> (you likely have the best hand, so you want more
                        money in the pot) and raising as a <strong>bluff</strong> (you probably
                        don't, but betting big enough can convince a better hand to fold).
                    </li>
                </ul>
                <p>
                    The decision between calling and folding usually comes down to two numbers:{' '}
                    <strong>pot odds</strong> and <strong>equity</strong>.
                </p>
                <p>
                    Pot odds are the price you're being offered to call, expressed as a percentage:
                    the amount you'd have to call, divided by the total pot after you call. Say the
                    pot is $100 and an opponent bets $50 -- the pot is now $150, and calling costs
                    $50 to win a total of $200. That's pot odds of 50 / 200 = <strong>25%</strong>.
                </p>
                <p>
                    Equity is simply your estimated chance of winning the hand right now, given the
                    cards you've seen (this simulator shows it to you live whenever you face a
                    decision). Compare the two: if your equity is above the pot odds you're being
                    offered -- say 35% equity against 25% pot odds -- calling is profitable in the
                    long run, even though you'll still lose plenty of individual hands. If your
                    equity is below the pot odds -- say 15% equity against that same 25% -- folding
                    is the better play, since you'd be paying more than your actual chance of
                    winning justifies.
                </p>
            </section>

            <section className="flex flex-col gap-3">
                <h2 className="text-xl font-semibold">Starting Hand Strength Matrix:</h2>
                <p>
                    Not all starting hands are equal. This matrix scores all 169 possible starting
                    hand classes using the widely-cited "Chen Formula", where pairs are on the
                    diagonal, suited combos above it, offsuit combos below it, organised from
                    strongest (green) to weakest (red). <strong>7-2 offsuit</strong> famously scores
                    among the very worst, which is exactly why it's the poker community's example of
                    the worst hand in Texas Hold'em.
                </p>
                <StartingHandMatrix />
            </section>

            <section className="flex flex-col gap-3">
                <h2 className="text-xl font-semibold">Glossary:</h2>
                <dl className="flex flex-col gap-3">
                    <GlossaryEntry term="Blinds (Small Blind / Big Blind):">
                        Forced bets posted by the two players to the left of the dealer button
                        before any cards are dealt, to make sure there's always something in the pot
                        worth playing for.
                    </GlossaryEntry>
                    <GlossaryEntry term="Button:">
                        The dealer position for the hand, marked with a "D" in this simulator, it
                        rotates one seat to the left every hand.
                    </GlossaryEntry>
                    <GlossaryEntry term="Pot">
                        The total amount everyone has bet this hand, awarded to whoever wins it.
                    </GlossaryEntry>
                    <GlossaryEntry term="Pot Odds:">
                        The ratio of the current bet to the pot, used to judge whether calling is
                        worth it given your chance of winning.
                    </GlossaryEntry>
                    <GlossaryEntry term="Equity:">
                        Your estimated probability of winning the hand right now, given the cards
                        seen so far, shown live in this simulator whenever you face a decision.
                    </GlossaryEntry>
                    <GlossaryEntry term="All-In:">
                        Betting your entire remaining stack. You can't be forced to bet more than
                        you have.
                    </GlossaryEntry>
                    <GlossaryEntry term="Side Pot:">
                        A separate pot that forms when an all-in player can't match a later bet,
                        this is contested only by the players who put in enough to be eligible for
                        it.
                    </GlossaryEntry>
                </dl>
            </section>
        </main>
    </div>
)

export { HowToPlayPage }
