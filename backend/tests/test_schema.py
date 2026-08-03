import pytest
from sqlalchemy.exc import IntegrityError

from app.models.schema import CategoryInsight, Strategy, User


def test_tables_create_and_insert(db):
    db.add(User(email="a@b.c", password_hash="x"))
    db.add(
        CategoryInsight(
            category="food_restaurants",
            agent="customer_insight",
            payload={"positive_pct": 61.0},
            dataset="Yelp Open Dataset (sampled)",
            sample_size=200000,
        )
    )
    db.commit()
    row = db.query(CategoryInsight).filter_by(category="food_restaurants").one()
    assert row.payload["positive_pct"] == 61.0


def test_category_insight_unique_constraint_on_category_and_agent(db):
    """A second row with the same (category, agent) pair must be rejected.

    This would pass falsely if UniqueConstraint("category", "agent") were
    missing or misspelled from CategoryInsight.__table_args__: without it,
    both inserts commit cleanly and no IntegrityError is ever raised.
    """
    db.add(
        CategoryInsight(
            category="grocery",
            agent="market_sizing",
            payload={"tam": 1},
            dataset="World Bank",
            sample_size=100,
        )
    )
    db.commit()

    db.add(
        CategoryInsight(
            category="grocery",
            agent="market_sizing",
            payload={"tam": 2},
            dataset="World Bank",
            sample_size=200,
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_strategy_user_id_is_nullable_for_guests(db):
    """Guest-generated strategies must persist with user_id=None.

    This would fail if Strategy.user_id were declared NOT NULL (e.g. missing
    `nullable=True` / `str | None`): the commit would raise IntegrityError
    instead of succeeding.
    """
    strategy = Strategy(
        user_id=None,
        idea_text="A subscription box for artisan coffee",
        category="food_restaurants",
        report_json={},
    )
    db.add(strategy)
    db.commit()

    row = db.query(Strategy).filter_by(idea_text="A subscription box for artisan coffee").one()
    assert row.user_id is None
    assert row.id is not None


def test_json_column_round_trips_nested_structure(db):
    """payload/report_json must survive a real DB round-trip unchanged.

    We expire the session and re-query so SQLAlchemy is forced to
    deserialize the JSON column from SQLite rather than returning the same
    Python object still held in memory. If the column were declared as
    String instead of JSON, this would come back as a raw JSON string (or
    fail the equality check / dict access) instead of a dict.
    """
    nested = {
        "scores": [1, 2, 3],
        "meta": {"nested": {"a": 1, "b": [True, False, None]}},
    }
    db.add(
        CategoryInsight(
            category="electronics",
            agent="pricing",
            payload=nested,
            dataset="Amazon (sampled)",
            sample_size=500,
        )
    )
    db.commit()

    db.expire_all()
    row = db.query(CategoryInsight).filter_by(category="electronics").one()
    assert row.payload == nested
    assert isinstance(row.payload["scores"], list)
    assert isinstance(row.payload["meta"]["nested"], dict)
