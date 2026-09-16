"""Account-wide statistics (Part 12 Phase 7) -- aggregates across every
session a user has ever played, not just the one currently open (that's
the per-session dashboard from Part 10, which stays unchanged).

Key insight: win/loss/split/fold can't be read off a single HandPlayer
row in isolation -- knowing hero won isn't enough to know whether it was
an outright win or a split, since that depends on how many OTHER seats in
the same hand also have is_winner=True. So this fetches every player row
for every one of the user's completed hands in two flat queries (not N+1
per hand) and groups them by hand_history_id in Python.

Part 13 Phase 4 adds play-style metrics (vpip_rate/aggression_factor) and
an account-wide bankroll_history, both empirical rather than re-deriving
anything from fixed thresholds -- see the play-style block below.

Part 14 Phase 4 adds three more, all needing to know how much action
already happened before hero's own preflop decision on that street --
a genuinely different (sequence/position-aware) computation from the
flat filters above, so it gets its own helper, _hero_preflop_decisions.
"""

from collections import defaultdict

from sqlalchemy.orm import Session

from backend.models import BankrollLog, GameSession, HandAction, HandHistory, HandPlayer, User


def _hero_preflop_decisions(actions_by_hand, button_seat_by_hand):
    """One record per complete hand, describing hero's FIRST preflop
    decision only (later preflop actions in the same hand, if the action
    reopens on hero, describe a 4-bet/5-bet/etc. -- out of scope here):

    - 'action': hero's own action string ('fold' | 'match' | 'raise_to').
    - 'entries_before': how many real entries (a raise_to, or a match
      with amount > 0 -- i.e. NOT a forced blind or a free check) any
      OTHER seat made on this street before hero's decision.
    - 'raises_before': the subset of entries_before that were raises.
    - 'is_button': whether hero held the button this hand.

    Reused by PFR (action == 'raise_to'), 3-bet% (raises_before >= 1 is
    the "opportunity"), and ATS% (is_button and entries_before == 0 is
    the "opportunity") -- three different slices of the same walk,
    rather than three near-duplicate loops over the action log.
    """
    decisions = {}
    for hand_id, actions in actions_by_hand.items():
        entries_before = 0
        raises_before = 0
        for action in sorted(actions, key=lambda a: a.seq):
            if action.street != 'preflop':
                continue
            if action.seat_index == 0:
                decisions[hand_id] = {
                    'action': action.action,
                    'entries_before': entries_before,
                    'raises_before': raises_before,
                    'is_button': button_seat_by_hand.get(hand_id) == 0,
                }
                break
            is_entry = action.action == 'raise_to' or (action.action == 'match' and action.amount > 0)
            if is_entry:
                entries_before += 1
            if action.action == 'raise_to':
                raises_before += 1
    return decisions


def compute_user_stats(user: User, db: Session) -> dict:
    sessions = db.query(GameSession).filter_by(user_id=user.id).all()
    cumulative_bankroll_change = sum(s.current_bankroll - s.starting_bankroll for s in sessions)

    empty_hand_stats = {
        'total_hands': 0,
        'win_count': 0, 'loss_count': 0, 'split_count': 0, 'fold_count': 0,
        'win_rate': 0.0, 'loss_rate': 0.0, 'split_rate': 0.0, 'fold_rate': 0.0,
        'biggest_win': None, 'biggest_loss': None,
        'vpip_rate': 0.0, 'aggression_factor': None,
        'pfr_rate': 0.0, 'three_bet_rate': None, 'ats_rate': None,
    }

    if not sessions:
        return {
            'total_sessions': 0, 'cumulative_bankroll_change': 0.0,
            'bankroll_history': [], **empty_hand_stats,
        }

    session_ids = [s.id for s in sessions]

    # Every session's own log rows, chronologically -- a session resetting
    # to its own starting_bankroll shows up as a real jump in this series,
    # not a bug to smooth over (each session genuinely is its own scoped
    # bankroll, per this project's Kelly-Criterion premise).
    bankroll_history = [
        {'bankroll_after': row.bankroll_after, 'logged_at': row.logged_at}
        for row in
        db.query(BankrollLog)
        .filter(BankrollLog.game_session_id.in_(session_ids))
        .order_by(BankrollLog.logged_at)
        .all()
    ]

    complete_hands = (
        db.query(HandHistory.id, HandHistory.button_seat)
        .filter(HandHistory.game_session_id.in_(session_ids), HandHistory.street == 'complete')
        .all()
    )
    complete_hand_ids = [row.id for row in complete_hands]
    button_seat_by_hand = {row.id: row.button_seat for row in complete_hands}

    if not complete_hand_ids:
        return {
            'total_sessions': len(sessions),
            'cumulative_bankroll_change': cumulative_bankroll_change,
            'bankroll_history': bankroll_history,
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

    # Play-style: the same tight/loose and passive/aggressive axes
    # poker/bots.py's personas are built from (fold_below/raise_above),
    # computed empirically from hero's own action log rather than a fixed
    # threshold. Hero always occupies seat_index 0 (poker/hand_flow.py
    # hardcodes hero_seat=0), so no join to HandPlayer is needed here.
    hero_actions = (
        db.query(HandAction)
        .filter(HandAction.hand_history_id.in_(complete_hand_ids), HandAction.seat_index == 0)
        .all()
    )

    # VPIP ("voluntarily put money in pot"): the fraction of hands where
    # hero called or raised preflop, as opposed to folding or only ever
    # checking a free option (a forced blind isn't voluntary, and a
    # zero-amount preflop 'match' is a free check -- e.g. the big blind
    # facing no raise -- so neither counts).
    vpip_hand_ids = {
        action.hand_history_id for action in hero_actions
        if action.street == 'preflop'
        and (action.action == 'raise_to' or (action.action == 'match' and action.amount > 0))
    }
    vpip_rate = rate(len(vpip_hand_ids))

    # Aggression factor: raises-to-calls ratio across every street (the
    # standard poker HUD definition) -- a check ('match' with amount 0) is
    # excluded from the denominator entirely, since it's neither an
    # aggressive action nor a passive call. None (not 0, not infinity)
    # when hero has never made a real call yet -- not enough data for a
    # ratio, same "no data" convention as biggest_win/biggest_loss above.
    raise_count = sum(1 for action in hero_actions if action.action == 'raise_to')
    call_count = sum(1 for action in hero_actions if action.action == 'match' and action.amount > 0)
    aggression_factor = raise_count / call_count if call_count > 0 else None

    # PFR/3-bet%/ATS%: all three need to know how much action already
    # happened before hero's own preflop decision -- see
    # _hero_preflop_decisions for the single shared walk they're derived
    # from. This needs every seat's actions, not just hero's own (unlike
    # vpip_rate/aggression_factor above), so it's a separate query.
    all_actions = db.query(HandAction).filter(HandAction.hand_history_id.in_(complete_hand_ids)).all()
    actions_by_hand = defaultdict(list)
    for action in all_actions:
        actions_by_hand[action.hand_history_id].append(action)
    preflop_decisions = _hero_preflop_decisions(actions_by_hand, button_seat_by_hand)

    # PFR (preflop raise %): fraction of hands where hero's first preflop
    # entry was itself a raise -- a strict subset of vpip_rate's hand set.
    pfr_rate = rate(sum(1 for d in preflop_decisions.values() if d['action'] == 'raise_to'))

    # 3-bet%: of hands where hero faced at least one existing preflop
    # raise before acting (an "opportunity"), the fraction hero re-raised.
    three_bet_opportunities = [d for d in preflop_decisions.values() if d['raises_before'] >= 1]
    three_bet_rate = (
        sum(1 for d in three_bet_opportunities if d['action'] == 'raise_to') / len(three_bet_opportunities)
        if three_bet_opportunities else None
    )

    # ATS% (attempt to steal): hero on the button, folded to before
    # hero's turn (0 real entries preflop) -- an "opportunity"; of those,
    # the fraction hero raised. Only meaningful for num_opponents >= 2 (a
    # real button-vs-blinds distinction), not special-cased for heads-up.
    ats_opportunities = [d for d in preflop_decisions.values() if d['is_button'] and d['entries_before'] == 0]
    ats_rate = (
        sum(1 for d in ats_opportunities if d['action'] == 'raise_to') / len(ats_opportunities)
        if ats_opportunities else None
    )

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
        'vpip_rate': vpip_rate,
        'aggression_factor': aggression_factor,
        'pfr_rate': pfr_rate,
        'three_bet_rate': three_bet_rate,
        'ats_rate': ats_rate,
        'bankroll_history': bankroll_history,
    }
