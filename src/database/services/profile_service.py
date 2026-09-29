from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models import Profile


def create_profile(
    db: Session,
    user_id: UUID,
    full_name: str | None = None,
) -> Profile:
    """
    Create a new user profile.
    """

    profile = Profile(
        id=user_id,
        full_name=full_name,
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile


def get_profile_by_id(
    db: Session,
    user_id: UUID,
) -> Profile | None:
    """
    Find a profile using its user ID.
    """

    statement = select(Profile).where(
        Profile.id == user_id
    )

    return db.execute(statement).scalar_one_or_none()


def delete_profile(
    db: Session,
    profile: Profile,
) -> None:
    """
    Delete a user profile.
    """

    db.delete(profile)
    db.commit()


if __name__ == "__main__":

    from uuid import uuid4

    from src.database.connection import SessionLocal

    db = SessionLocal()

    try:
        test_user_id = uuid4()

        profile = create_profile(
            db=db,
            user_id=test_user_id,
            full_name="Test User",
        )

        print("Profile created successfully!")
        print("ID:", profile.id)
        print("Name:", profile.full_name)

        found_profile = get_profile_by_id(
            db=db,
            user_id=test_user_id,
        )

        print("\nProfile lookup:")

        if found_profile:
            print("Found:", found_profile.full_name)
        else:
            print("Profile not found.")

    finally:
        db.close()