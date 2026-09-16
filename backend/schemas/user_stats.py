from backend.schemas.base import ApiModel
from backend.schemas.game_session import BankrollHistoryPoint


class UserStatsResponse(ApiModel):
    """Account-wide aggregation across every one of the user's sessions
    (Part 12 Phase 7) -- built server-side from a plain dict, not
    model_validate()'d off an ORM row, so this is a plain ApiModel rather
    than an OrmResponseModel (matching HandActionLogEntry's own precedent
    for a response shape that isn't a 1:1 mirror of a single DB table).
    """

    total_sessions: int
    total_hands: int  # only hands that reached street == 'complete'

    win_count: int
    loss_count: int
    split_count: int
    fold_count: int
    win_rate: float
    loss_rate: float
    split_rate: float
    fold_rate: float

    # Sum of (current_bankroll - starting_bankroll) across every session --
    # not a re-derivation from individual hand deltas, since a session's
    # own persisted bankroll columns are already the authoritative source
    # (and remain correct even if a session still has a hand in progress).
    cumulative_bankroll_change: float

    # None (not 0) when there's no hand of that kind at all yet -- "you've
    # never won" and "you won exactly $0 once" are different facts.
    biggest_win: float | None
    biggest_loss: float | None

    # Part 13 Phase 4 -- play-style, computed empirically from hero's own
    # action log (see compute_user_stats) rather than a fixed threshold,
    # the same tight/loose and passive/aggressive axes poker/bots.py's
    # personas are built from.
    vpip_rate: float  # 0.0 when there's no data yet, like the *_rate fields above
    aggression_factor: float | None  # None (not 0/inf) until hero has made a real call

    # Part 14 Phase 4 -- position/sequence-aware preflop stats, computed
    # from the same per-hand action walk (see
    # compute_user_stats._hero_preflop_decisions). pfr_rate uses the same
    # 0.0-until-there's-data convention as vpip_rate; three_bet_rate/
    # ats_rate use aggression_factor's None-until-an-opportunity
    # convention, since both are ratios over a subset of hands, not all
    # of them.
    pfr_rate: float
    three_bet_rate: float | None
    ats_rate: float | None

    # Every BankrollLog row across every one of the user's sessions, in
    # chronological order -- unlike the per-session-only chart from Part
    # 10, a session boundary shows up here as a real jump back to that
    # session's own starting_bankroll, not something smoothed over.
    bankroll_history: list[BankrollHistoryPoint]
