from backend.schemas.base import ApiModel


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
