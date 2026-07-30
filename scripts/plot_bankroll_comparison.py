"""Generate the Part 6 comparison plots: bankroll growth curves and risk
of ruin across staking strategies, holding the edge (win_probability,
odds) and number of hands constant so the only thing that differs
between panels is how much of the bankroll gets staked each hand.

Run from the project root:
    source venv/bin/activate
    PYTHONPATH=. python3 scripts/plot_bankroll_comparison.py

Writes PNGs to docs/part-6-plots/.
"""

import os

import matplotlib.pyplot as plt

from poker.bankroll import (
    all_in_strategy,
    fixed_stake_strategy,
    kelly_strategy,
    simulate_many_sessions,
)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'docs', 'part-6-plots')

# A modest, realistic edge -- strong enough to be worth taking, not so
# strong that even reckless staking looks fine.
WIN_PROBABILITY = 0.55
ODDS = 1
INITIAL_BANKROLL = 1000
NUM_HANDS = 200
SEED = 42

STRATEGIES = {
    'Fixed Stake (5% of initial)': fixed_stake_strategy(0.05),
    'Half Kelly': kelly_strategy(0.5),
    'Full Kelly': kelly_strategy(1.0),
    'All-In': all_in_strategy(),
}


def plot_growth_curves():
    """One subplot per strategy, overlaying a sample of individual
    session trajectories on a log-scaled y-axis -- log scale because
    that's the scale on which Kelly-style geometric growth looks like a
    straight line, and it's also what makes all-in's near-instant
    collapse to zero visually obvious (everything else flatlines at the
    bottom of the chart).
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True)

    for ax, (name, strategy) in zip(axes.flat, STRATEGIES.items()):
        result = simulate_many_sessions(
            strategy, INITIAL_BANKROLL, WIN_PROBABILITY, ODDS, NUM_HANDS,
            num_sessions=200, seed=SEED,
        )

        for session in result.sessions[:40]:  # a readable sample, not all 200
            # A ruined bankroll is exactly 0, which log-scale can't plot --
            # floor it at 1 for display only, purely so the collapse to
            # ruin is visible on the chart rather than silently dropped.
            displayed = [max(value, 1) for value in session.bankroll_history]
            ax.plot(displayed, linewidth=0.7, alpha=0.5)

        ax.set_yscale('log')
        ax.set_title(f'{name}\nrisk of ruin = {result.risk_of_ruin:.1%}')
        ax.set_xlabel('Hand number')
        ax.set_ylabel('Bankroll (log scale)')
        ax.axhline(INITIAL_BANKROLL, color='black', linewidth=0.8, linestyle='--')

    fig.suptitle(
        f'Bankroll growth curves by staking strategy\n'
        f'(win probability={WIN_PROBABILITY:.0%}, odds={ODDS}:1, {NUM_HANDS} hands, '
        f'40 sample sessions each)'
    )
    fig.tight_layout()

    path = os.path.join(OUTPUT_DIR, 'bankroll_growth_curves.png')
    fig.savefig(path, dpi=150)
    print(f'Wrote {path}')


def plot_risk_of_ruin_and_median_bankroll():
    """Bar charts summarising many more sessions than the growth-curve
    plot uses (2000 vs. 200) -- risk of ruin and median final bankroll
    are single numbers, so they converge with less visual clutter than
    trying to overlay thousands of individual lines.
    """
    names = list(STRATEGIES.keys())
    results = [
        simulate_many_sessions(
            strategy, INITIAL_BANKROLL, WIN_PROBABILITY, ODDS, NUM_HANDS,
            num_sessions=2000, seed=SEED,
        )
        for strategy in STRATEGIES.values()
    ]

    fig, (risk_ax, median_ax) = plt.subplots(1, 2, figsize=(12, 5))

    risk_ax.bar(names, [result.risk_of_ruin for result in results], color='firebrick')
    risk_ax.set_ylabel('Risk of ruin')
    risk_ax.set_title('Risk of ruin by strategy')
    risk_ax.tick_params(axis='x', rotation=20)

    median_ax.bar(names, [result.median_final_bankroll for result in results], color='seagreen')
    median_ax.set_ylabel('Median final bankroll')
    median_ax.set_title('Median final bankroll by strategy')
    median_ax.axhline(INITIAL_BANKROLL, color='black', linewidth=0.8, linestyle='--')
    median_ax.tick_params(axis='x', rotation=20)

    fig.suptitle(
        f'Risk of ruin and median outcome after {NUM_HANDS} hands '
        f'(2000 sessions per strategy)'
    )
    fig.tight_layout()

    path = os.path.join(OUTPUT_DIR, 'risk_of_ruin_comparison.png')
    fig.savefig(path, dpi=150)
    print(f'Wrote {path}')


if __name__ == '__main__':
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    plot_growth_curves()
    plot_risk_of_ruin_and_median_bankroll()
