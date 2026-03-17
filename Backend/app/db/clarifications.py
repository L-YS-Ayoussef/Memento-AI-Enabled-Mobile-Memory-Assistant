# from sqlalchemy.orm import Session
# from ..models.models import Clarification
# from .business_db import get_db

# def add_clarification(
#     db: Session,
#     *,
#     id: int,
#     user_id: int,
#     type: str,
#     query: str,
#     progress: str,
#     current_datetime: str,
#     email: dict | None = None
# ) -> Clarification:
#     """Create and persist a new Clarification record."""
#     clar = Clarification(
#         id=id,
#         user_id=user_id,
#         type=type,
#         query=query,
#         progress=progress,
#         current_datetime=current_datetime,
#         email=email,
#     )
#     db.add(clar)
#     db.commit()
#     db.refresh(clar)
#     return clar

# def get_clarification_by_id(db: Session, *, id: int) -> Clarification | None:
#     """Fetch a single Clarification by its primary key."""
#     return db.query(Clarification).filter(Clarification.id == id).first()

# def get_clarifications_by_user(db: Session, *, user_id: int) -> list[Clarification]:
#     """Fetch all Clarifications for a given user."""
#     return db.query(Clarification).filter(Clarification.user_id == user_id).all()

# def update_clarification(
#     db: Session,
#     *,
#     id: int,
#     **fields_to_update
# ) -> Clarification | None:
#     """
#     Update fields on an existing Clarification.
#     Pass only the columns you want to change as keyword args.
#     """
#     clar = db.query(Clarification).filter(Clarification.id == id).first()
#     if not clar:
#         return None
#     for field, value in fields_to_update.items():
#         setattr(clar, field, value)
#     db.commit()
#     db.refresh(clar)
#     return clar

# def delete_clarification(db: Session, *, id: int) -> bool:
#     """Delete a Clarification by id. Returns True if deleted."""
#     clar = db.query(Clarification).filter(Clarification.id == id).first()
#     if not clar:
#         return False
#     db.delete(clar)
#     db.commit()
#     return True

# def delete_clarifications_by_user(db: Session, *, user_id: int) -> int:
#     """
#     Delete all Clarifications for a given user.
#     Returns the number of rows deleted.
#     """
#     deleted = db.query(Clarification).filter(Clarification.user_id == user_id).delete(synchronize_session=False)
#     db.commit()
#     return deleted



# if __name__ == "__main__":

#     db = next(get_db())

#     # Example usage
#     new_clar = add_clarification(
#         db=db,
#         id=99999999999999999,
#         user_id=123,
#         type="schedule",
#         query="What is the schedule for next week?",
#         progress="Pending",
#         current_datetime="2023-10-01T12:00:00Z",
#         email=None
#     )