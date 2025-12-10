"""
Article model for SQLAlchemy.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class Article(Base, TimestampMixin):
    """Article model representing blog posts or content articles."""

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default="draft", nullable=False, index=True
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    # Relationships
    author: Mapped["User"] = relationship("User", back_populates="articles")

    # Table arguments for additional indexes and constraints
    __table_args__ = (
        Index("idx_articles_status", "status"),
        Index(
            "idx_articles_title_content_search",
            text("to_tsvector('english', title || ' ' || content)"),
            postgresql_using="gin",
        ),
    )

    def __repr__(self) -> str:
        return f"<Article(id={self.id}, title='{self.title}', status='{self.status}')>"

    @property
    def is_published(self) -> bool:
        """Check if the article is published."""
        return self.status == "published"

    def publish(self) -> None:
        """Publish the article."""
        if self.status != "published":
            self.status = "published"
            if not self.published_at:
                self.published_at = datetime.now()

    def archive(self) -> None:
        """Archive the article."""
        self.status = "archived"

    def draft(self) -> None:
        """Set article back to draft."""
        self.status = "draft"
