from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

import pytest
import pytest_asyncio
from dishka import make_async_container
from sqlalchemy.ext.asyncio import AsyncSession

from char_core.models import (
    Challenge,
    Space,
    SpaceMember,
    User,
    Achievement,
    SelectionFnEnum, AggregationStrategy, ChallengeStateEnum, ChallengeResult,
    ChallengeMember,
)
from char_rest_api.infrastructure import InfrastructureProvider


@pytest_asyncio.fixture
async def app_container():
    async_container = make_async_container(InfrastructureProvider())
    async with async_container() as container:
        yield container


@pytest_asyncio.fixture
async def session_container(
        app_container
):
    async with app_container() as container:
        yield container


@pytest_asyncio.fixture
async def request_container(
        session_container,
):
    async with session_container() as container:
        yield container


@pytest_asyncio.fixture
async def session(
        request_container,
):
    async with await request_container.get(AsyncSession) as session:
        session.commit = Mock(side_effect=NotImplementedError)
        yield session
        await session.rollback()


@pytest.mark.asyncio
async def test_challenge(
        request_container,
        session: AsyncSession,
):
    # ========= some random setup and random tests.
    # ========= some of the models will be reused in following tests

    user = User(
        email="test@gmail.com",
        phone_number=88888888888,
        password_hash="123",
        full_name="123",
        description="de",
    )
    space = Space(
        name="Test",
        description="d",
    )
    space_member = SpaceMember(
        is_administrator=True,
        space=space,
        user=user,
    )
    achievement = Achievement(
        name="Ach",
        space=space,
    )
    challenge = Challenge(
        space=space,
        name="Test ch",
        description="d",
        prize="p",
        achievement_id=achievement.id,
        is_verification_required=False,
        is_estimation_required=False,
        results_aggregation_strategy=AggregationStrategy.MAX,
        starts_at=datetime.now() + timedelta(hours=1),
        ends_at_const=datetime.now() + timedelta(hours=2),
        prize_determination_fn=SelectionFnEnum.HEAD,
        prize_determination_argument=1,
    )
    challenge_member = ChallengeMember(
        challenge=challenge,
        user=user,
        is_referee=True,
        is_administrator=True,
        is_participant=True,
    )
    session.add_all((
        user,
        space,
        space_member,
        achievement,
        challenge,
        challenge_member,
    ))
    await session.flush()

    assert ChallengeStateEnum(challenge.state) == ChallengeStateEnum.SCHEDULED
    challenge.starts_at -= timedelta(hours=1, minutes=1)
    assert ChallengeStateEnum(challenge.state) is ChallengeStateEnum.ACTIVE
    await session.refresh(challenge)
    assert challenge.cached_current_progress == 0
    await challenge.update_lifecycle_state(session)
    assert challenge.cached_current_progress == 0
    some_result = ChallengeResult(
        member=challenge_member,
        submitted_value=10,
    )
    session.add(some_result)
    await session.flush()
    # note: refreshing after some result submission is required!
    await session.refresh(challenge)

    challenge.starts_at = datetime.now() - timedelta(hours=2)
    challenge.ends_at_const = datetime.now() - timedelta(hours=1)
    await session.flush()

    # note: event may be finished only directly via lifecycle update fn
    assert ChallengeStateEnum(challenge.state) is ChallengeStateEnum.ACTIVE
    session.commit = AsyncMock()
    assert challenge.finalized_at is None
    assert not challenge_member.is_winner
    await challenge.update_lifecycle_state(session)
    assert ChallengeStateEnum(challenge.state) is ChallengeStateEnum.FINISHED
    assert challenge.cached_current_progress == 100
    session.commit.assert_awaited()
    assert challenge.finalized_at is not None
    assert challenge_member.is_winner

    # ======== test some common challange setups in progress ======
    # ======== 1. setup with variable time

    challenge = Challenge(
        space=space,
        name="Make 100 result in average",
        description="d",
        prize="p",
        achievement_id=achievement.id,
        is_verification_required=False,
        is_estimation_required=False,
        results_aggregation_strategy=AggregationStrategy.AVG,
        starts_at=datetime.now() - timedelta(hours=1),
        ends_at_determination_fn=SelectionFnEnum.HIGHER_THAN,
        ends_at_determination_argument=200,
        prize_determination_fn=SelectionFnEnum.HEAD,
        prize_determination_argument=1,
    )
    user_participant = User(
        email="test123@gmail.com",
        phone_number=88888888888,
        password_hash="123",
        full_name="123",
        description="de",
    )
    member_participant = ChallengeMember(
        challenge=challenge,
        user=user_participant,
        is_referee=False,
        is_administrator=False,
        is_participant=True,
    )
    user_admin = User(
        email="testadmin@gmail.com",
        phone_number=88888888881,
        password_hash="123",
        full_name="123 adm",
        description="de",
    )
    member_admin = ChallengeMember(
        challenge=challenge,
        user=user_admin,
        is_referee=False,
        is_administrator=False,
        is_participant=True,
    )
    session.add_all((
        user_participant,
        challenge,
        challenge_member,
        member_participant,
        user_admin,
        member_admin,
    ))
    await session.flush()
    await session.refresh(challenge)

    # ======== currently no results is submitted.
    # ======== lets check it

    def checkpoint_1():
        assert len(challenge.results) == 0
        assert len(challenge.active_results) == 0
        assert challenge.cached_current_progress == 0
        assert ChallengeStateEnum(challenge.state) is ChallengeStateEnum.ACTIVE

    checkpoint_1()

    # ======== lifecycle call must have no impact

    await challenge.update_lifecycle_state(session)
    checkpoint_1()

    # ======== lets create some results for admin now

    admin_results = []
    admin_results.append(ChallengeResult(
        member=member_admin,
        submitted_value=10,
    ))
    session.add_all(admin_results)
    await session.flush()
    await session.refresh(challenge)

    # ======== current avg of admin is 10, it is 5 percents from target
    # ======== lifecycle must must indicate the progress

    assert challenge.cached_current_progress == 0
    await challenge.update_lifecycle_state(session)
    assert challenge.cached_current_progress == 5
    assert member_admin.cached_aggregated_result == 10
    assert member_participant.cached_aggregated_result == 0

    # ======== add more results and check that all ok

    session.add_all((
        ChallengeResult(
            member=member_admin,
            submitted_value=380,  # avg must be 195 now => 97% from 200
        ),
        ChallengeResult(),
    ))

    # and so on... the time... :(
