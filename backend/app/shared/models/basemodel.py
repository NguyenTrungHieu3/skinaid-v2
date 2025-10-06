from sqlmodel import SQLModel, Field
from datetime import datetime, timezone


class TimestampMixin(SQLModel):
<<<<<<< HEAD
    """
    Mixin để tự động thêm cột timestamp cho các bảng.

    - created_at: Thời điểm record được tạo (default = now UTC)
    - updated_at: Thời điểm record được cập nhật (default = now UTC, 
                  thường sẽ được update mỗi khi có thay đổi)

    Dùng bằng cách kế thừa trong model:
        class User(TimestampMixin, table=True):
            id: int = Field(default=None, primary_key=True)
            name: str
    """

=======
>>>>>>> 68dbfc37ac2c720bc4aa0055dd7229ec2ed3fe36
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )
