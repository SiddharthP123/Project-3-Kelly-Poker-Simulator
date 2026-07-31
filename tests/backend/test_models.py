import pytest
from sqlalchemy.exc import IntegrityError

from backend.models import (
    BankrollLog,
    GameSession,
    GameSessionOpponent,
    HandAction,
    HandHistory,
    HandPlayer,
    User,
)


def test_game_session_can_be_created_without_a_user(db_session):
    # user_id is nullable -- there's no auth yet (Part 9), so sessions
    # must be creatable without a real signed-up user.
    session = GameSession(starting_bankroll=1000.0, current_bankroll=1000.0, bot_persona='Tight-Aggressive')
    db_session.add(session)
    db_session.commit()

    assert session.id is not None
    assert session.user_id is None
    assert session.status == 'active'


def test_game_session_relates_to_a_user_when_provided(db_session):
    user = User(email='test@example.com')
    db_session.add(user)
    db_session.commit()

    session = GameSession(
        user_id=user.id, starting_bankroll=1000.0, current_bankroll=1000.0,
        bot_persona='Kelly-Optimal',
    )
    db_session.add(session)
    db_session.commit()

    assert session.user.email == 'test@example.com'
    assert user.game_sessions == [session]


def test_hand_history_and_bankroll_log_relate_to_their_session(db_session):
    session = GameSession(starting_bankroll=1000.0, current_bankroll=950.0, bot_persona='Random')
    db_session.add(session)
    db_session.commit()

    hand = HandHistory(
        game_session_id=session.id, hand_number=1, hero_hole_cards='Ah,Ac',
        board_cards='Ks,Qd,2c,7h,9s', pot_size=100.0, hero_action='call',
        hero_bankroll_delta=-50.0,
    )
    db_session.add(hand)
    db_session.commit()

    log = BankrollLog(game_session_id=session.id, hand_history_id=hand.id, bankroll_after=950.0)
    db_session.add(log)
    db_session.commit()

    assert session.hands == [hand]
    assert session.bankroll_logs == [log]
    assert log.hand_history is hand
    assert hand.bankroll_logs == [log]


def test_deleting_session_cascades_to_hands(db_session):
    session = GameSession(starting_bankroll=1000.0, current_bankroll=1000.0, bot_persona='Random')
    db_session.add(session)
    db_session.commit()

    hand = HandHistory(
        game_session_id=session.id, hand_number=1, hero_hole_cards='Ah,Ac', pot_size=10.0,
        hero_action='fold', hero_bankroll_delta=0.0,
    )
    db_session.add(hand)
    db_session.commit()

    db_session.delete(session)
    db_session.commit()

    assert db_session.query(HandHistory).count() == 0


def test_user_email_must_be_unique(db_session):
    db_session.add(User(email='dup@example.com'))
    db_session.commit()

    db_session.add(User(email='dup@example.com'))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_user_has_default_starting_bankroll(db_session):
    user = User(email='defaults@example.com')
    db_session.add(user)
    db_session.commit()

    assert user.starting_bankroll == pytest.approx(1000.0)


# --- Part 12: multi-opponent schema ---------------------------------------


def test_game_session_new_columns_default_to_null(db_session):
    # num_opponents/small_blind/big_blind are nullable specifically so
    # pre-Part-12 session rows (which never set them) stay valid.
    session = GameSession(starting_bankroll=1000.0, current_bankroll=1000.0, bot_persona='placeholder')
    db_session.add(session)
    db_session.commit()

    assert session.num_opponents is None
    assert session.small_blind is None
    assert session.big_blind is None


def test_game_session_opponents_relate_to_their_session(db_session):
    session = GameSession(
        starting_bankroll=1000.0, current_bankroll=1000.0, bot_persona='placeholder',
        num_opponents=2, small_blind=1.0, big_blind=2.0,
    )
    db_session.add(session)
    db_session.commit()

    opponent_1 = GameSessionOpponent(game_session_id=session.id, seat_index=1, persona='tight-aggressive')
    opponent_2 = GameSessionOpponent(game_session_id=session.id, seat_index=2, persona='loose-passive')
    db_session.add_all([opponent_1, opponent_2])
    db_session.commit()

    assert {o.persona for o in session.opponents} == {'tight-aggressive', 'loose-passive'}
    assert opponent_1.game_session is session


def test_game_session_opponent_seat_index_is_unique_per_session(db_session):
    session = GameSession(starting_bankroll=1000.0, current_bankroll=1000.0, bot_persona='placeholder')
    db_session.add(session)
    db_session.commit()

    db_session.add(GameSessionOpponent(game_session_id=session.id, seat_index=1, persona='random'))
    db_session.commit()

    db_session.add(GameSessionOpponent(game_session_id=session.id, seat_index=1, persona='balanced'))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_deleting_session_cascades_to_opponents(db_session):
    session = GameSession(starting_bankroll=1000.0, current_bankroll=1000.0, bot_persona='placeholder')
    db_session.add(session)
    db_session.commit()

    db_session.add(GameSessionOpponent(game_session_id=session.id, seat_index=1, persona='random'))
    db_session.commit()

    db_session.delete(session)
    db_session.commit()

    assert db_session.query(GameSessionOpponent).count() == 0


def _make_hand(db_session, **overrides):
    session = GameSession(starting_bankroll=1000.0, current_bankroll=1000.0, bot_persona='placeholder')
    db_session.add(session)
    db_session.commit()

    hand_kwargs = dict(
        game_session_id=session.id, hand_number=1, hero_hole_cards='Ah,Ac', pot_size=10.0,
    )
    hand_kwargs.update(overrides)
    hand = HandHistory(**hand_kwargs)
    db_session.add(hand)
    db_session.commit()
    return hand


def test_hand_history_new_columns_default_to_null(db_session):
    hand = _make_hand(db_session)
    assert hand.button_seat is None
    assert hand.street is None


def test_hand_players_hold_real_cards_for_every_seat_regardless_of_fold_status(db_session):
    # The redaction mechanism changes with this table (Part 12 plan): every
    # seat's real hole cards are always stored, even a folded seat's --
    # hiding happens at the response-schema layer, not by leaving this
    # column empty until a seat "earns" the right to be seen.
    hand = _make_hand(db_session)

    hero = HandPlayer(
        hand_history_id=hand.id, seat_index=0, is_hero=True,
        starting_stack=200.0, hole_cards='Ah,Ac',
    )
    folded_opponent = HandPlayer(
        hand_history_id=hand.id, seat_index=1, is_hero=False, persona='tight-aggressive',
        starting_stack=200.0, hole_cards='2c,7d', folded=True,
    )
    db_session.add_all([hero, folded_opponent])
    db_session.commit()

    assert hand.players == [hero, folded_opponent]
    assert folded_opponent.folded is True
    assert folded_opponent.hole_cards == '2c,7d'  # stored real despite folding
    assert hero.persona is None
    assert hero.final_stack is None  # not yet resolved


def test_hand_player_seat_index_is_unique_per_hand(db_session):
    hand = _make_hand(db_session)
    db_session.add(HandPlayer(hand_history_id=hand.id, seat_index=0, is_hero=True, starting_stack=100.0, hole_cards='Ah,Ac'))
    db_session.commit()

    db_session.add(HandPlayer(hand_history_id=hand.id, seat_index=0, is_hero=False, starting_stack=100.0, hole_cards='2c,7d'))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_hand_actions_are_ordered_by_seq(db_session):
    hand = _make_hand(db_session)

    # Insert out of order to prove the relationship's order_by, not
    # insertion order, determines .actions' ordering.
    db_session.add(HandAction(
        hand_history_id=hand.id, seq=1, street='preflop', seat_index=1,
        action='match', amount=2.0, pot_size_after=4.0,
    ))
    db_session.add(HandAction(
        hand_history_id=hand.id, seq=0, street='preflop', seat_index=0,
        action='post_blind', amount=2.0, pot_size_after=2.0,
    ))
    db_session.commit()

    assert [action.seq for action in hand.actions] == [0, 1]


def test_hand_action_equity_fields_are_optional_and_only_meaningful_for_hero(db_session):
    hand = _make_hand(db_session)

    bot_action = HandAction(
        hand_history_id=hand.id, seq=0, street='preflop', seat_index=1,
        action='fold', amount=0.0, pot_size_after=3.0,
    )
    hero_action = HandAction(
        hand_history_id=hand.id, seq=1, street='preflop', seat_index=0,
        action='raise_to', amount=8.0, pot_size_after=11.0,
        equity_at_decision=0.72, kelly_recommended_stake=15.0,
    )
    db_session.add_all([bot_action, hero_action])
    db_session.commit()

    assert bot_action.equity_at_decision is None
    assert hero_action.equity_at_decision == pytest.approx(0.72)
    assert hero_action.kelly_recommended_stake == pytest.approx(15.0)


def test_hand_action_seq_is_unique_per_hand(db_session):
    hand = _make_hand(db_session)
    db_session.add(HandAction(
        hand_history_id=hand.id, seq=0, street='preflop', seat_index=0,
        action='post_blind', amount=1.0, pot_size_after=1.0,
    ))
    db_session.commit()

    db_session.add(HandAction(
        hand_history_id=hand.id, seq=0, street='preflop', seat_index=1,
        action='post_blind', amount=2.0, pot_size_after=3.0,
    ))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_deleting_hand_cascades_to_players_and_actions(db_session):
    hand = _make_hand(db_session)
    db_session.add(HandPlayer(
        hand_history_id=hand.id, seat_index=0, is_hero=True, starting_stack=100.0, hole_cards='Ah,Ac',
    ))
    db_session.add(HandAction(
        hand_history_id=hand.id, seq=0, street='preflop', seat_index=0,
        action='post_blind', amount=1.0, pot_size_after=1.0,
    ))
    db_session.commit()

    db_session.delete(hand)
    db_session.commit()

    assert db_session.query(HandPlayer).count() == 0
    assert db_session.query(HandAction).count() == 0
