"""Account-wide statistics (Part 12 Phase 7) -- aggregates across every
session a user has ever played, not just the one currently open (that's
the per-session dashboard from Part 10, which stays unchanged).

Key insight: win/loss/split/fold can't be read off a single HandPlayer
row in isolation -- knowing hero won isn't enough to know whether it was
an outright win or a split, since that depends on how many OTHER seats in
the same hand also have is_winner=True. So this fetches every player row
for every one of the user's completed hands in two flat queries (not N+1
per hand) and groups them by hand_history_id in Python.
"""

from collections import defaultdict

from sqlalchemy.orm import Session

from backend.models import GameSession, HandHistory, HandPlayer, User


def compute_user_stats(user: User, db: Session) -> dict:
    sessions = db.query(GameSession).filter_by(user_id=user.id).all()
    cumulative_bankroll_change = sum(s.current_bankroll - s.starting_bankroll for s in sessions)

    empty_hand_stats = {
        'total_hands': 0,
        'win_count': 0, 'loss_count': 0, 'split_count': 0, 'fold_count': 0,
        'win_rate': 0.0, 'loss_rate': 0.0, 'split_rate': 0.0, 'fold_rate': 0.0,
        'biggest_win': None, 'biggest_loss': None,
    }

    if not sessions:
        return {'total_sessions': 0, 'cumulative_bankroll_change': 0.0, **empty_hand_stats}

    session_ids = [s.id for s in sessions]
    complete_hand_ids = [
        row.id for row in
        db.query(HandHistory.id)
        .filter(HandHistory.game_session_id.in_(session_ids), HandHistory.street == 'complete')
        .all()
    ]

    if not complete_hand_ids:
        return {
            'total_sessions': len(sessions),
            'cumulative_bankroll_change': cumulative_bankroll_change,
            **empty_hand_stats,
        }

    all_players = db.query(HandPlayer).filter(HandPlayer.hand_history_id.in_(complete_hand_ids)).all()

    winner_counts_by_hand = defaultdict(int)
    hero_by_hand = {}
    for player in all_players:
        if player.is_winner:
            winner_counts_by_hand[player.hand_history_id] += 1
        if player.is_hero:
            hero_by_hand[player.hand_history_id] = player

    win_count = loss_count = split_count = fold_count = 0
    net_results = []

    for hand_id, hero in hero_by_hand.items():
        net_results.append(hero.net_result or 0.0)

        if hero.folded:
            fold_count += 1
        elif hero.is_winner:
            if winner_counts_by_hand[hand_id] > 1:
                split_count += 1
            else:
                win_count += 1
        else:
            loss_count += 1

    total_hands = len(hero_by_hand)

    def rate(count):
        return count / total_hands if total_hands else 0.0

    wins = [r for r in net_results if r > 0]
    losses = [r for r in net_results if r < 0]

    return {
        'total_sessions': len(sessions),
        'total_hands': total_hands,
        'win_count': win_count, 'loss_count': loss_count,
        'split_count': split_count, 'fold_count': fold_count,
        'win_rate': rate(win_count), 'loss_rate': rate(loss_count),
        'split_rate': rate(split_count), 'fold_rate': rate(fold_count),
        'cumulative_bankroll_change': cumulative_bankroll_change,
        'biggest_win': max(wins) if wins else None,
        'biggest_loss': min(losses) if losses else None,
    }
