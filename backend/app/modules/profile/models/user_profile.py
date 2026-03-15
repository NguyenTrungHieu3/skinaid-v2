from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UUID
from typing import Optional, TYPE_CHECKING
from datetime import date, datetime, timezone
import uuid

if TYPE_CHECKING:
    from app.modules.auth.models.user import User

class UserProfile(SQLModel, table=True):
    __tablename__ = "user_profiles"  # type: ignore

    user_id: uuid.UUID = Field(primary_key=True, foreign_key="users.user_id")
    full_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None  # Enum(male, female, other)
    address: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    user: Optional["User"] = Relationship(back_populates="profile")

    @property
    def age(self) -> Optional[int]:
        if not self.date_of_birth:
            return None
        from datetime import date as date_type
        today = date_type.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def gender_display(self) -> str:
        gender_map = {
            "male": "Nam",
            "female": "Nữ",
            "other": "Khác"
        }
        return gender_map.get(self.gender.lower() if self.gender else "", "Chưa xác định")

    @property
    def has_complete_profile(self) -> bool:
        return bool(
            self.full_name and
            self.phone and
            self.date_of_birth and
            self.gender
        )

    @property
    def profile_completion_percentage(self) -> int:
        fields = [self.full_name, self.phone, self.date_of_birth, self.gender, self.address, self.avatar_url]
        completed_fields = sum(1 for field in fields if field is not None)
        return int((completed_fields / len(fields)) * 100)

    @classmethod
    def create_profile(
        cls,
        user_id: uuid.UUID,
        full_name: Optional[str] = None,
        phone: Optional[str] = None,
        date_of_birth: Optional[date] = None,
        gender: Optional[str] = None,
        address: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> "UserProfile":
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)
        return cls(
            user_id=user_id,
            full_name=full_name,
            phone=phone,
            date_of_birth=date_of_birth,
            gender=gender,
            address=address,
            avatar_url=avatar_url,
            created_at=current_time,
            updated_at=current_time
        )

    def update_profile(
        self,
        full_name: Optional[str] = None,
        phone: Optional[str] = None,
        date_of_birth: Optional[date] = None,
        gender: Optional[str] = None,
        address: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> None:
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)

        if full_name is not None:
            self.full_name = full_name
        if phone is not None:
            self.phone = phone
        if date_of_birth is not None:
            self.date_of_birth = date_of_birth
        if gender is not None:
            self.gender = gender
        if address is not None:
            self.address = address
        if avatar_url is not None:
            self.avatar_url = avatar_url

        self.updated_at = current_time

    def to_response_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "full_name": self.full_name,
            "phone": self.phone,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "gender": self.gender,
            "gender_display": self.gender_display,
            "address": self.address,
            "avatar_url": self.avatar_url,
            "age": self.age,
            "has_complete_profile": self.has_complete_profile,
            "profile_completion_percentage": self.profile_completion_percentage,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }