import pytest
from sqlalchemy.exc import IntegrityError

from backend.models import BankrollLog, GameSession, HandHistory, User


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
