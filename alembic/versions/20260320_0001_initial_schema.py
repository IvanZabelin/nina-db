"""create initial nina schema

Revision ID: 20260320_0001
Revises: 
Create Date: 2026-03-20 22:55:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260320_0001"
down_revision = None
branch_labels = None
depends_on = None


chat_type = sa.Enum("direct", "family", name="chat_type")
chat_member_role = sa.Enum("owner", "member", name="chat_member_role")
message_type = sa.Enum("text", "voice", "photo", "system", name="message_type")


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS trigger AS $$
        BEGIN
          NEW.updated_at = now();
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION touch_chat_updated_at()
        RETURNS trigger AS $$
        BEGIN
          UPDATE chats
          SET updated_at = now()
          WHERE id = NEW.chat_id;

          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    chat_type.create(op.get_bind(), checkfirst=True)
    chat_member_role.create(op.get_bind(), checkfirst=True)
    message_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("public_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("password_hash", sa.Text(), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("length(btrim(name)) > 0", name="users_name_not_blank"),
        sa.CheckConstraint("public_id > 0", name="users_public_id_positive"),
        sa.UniqueConstraint("public_id", name="uq_users_public_id"),
    )
    op.create_index("ux_users_email", "users", ["email"], unique=True, postgresql_where=sa.text("email is not null"))
    op.create_index("ux_users_phone", "users", ["phone"], unique=True, postgresql_where=sa.text("phone is not null"))

    op.create_table(
        "chats",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("type", chat_type, nullable=False),
        sa.Column("title", sa.String(length=150), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_chats_type", "chats", ["type"], unique=False)
    op.create_index("ix_chats_created_by", "chats", ["created_by"], unique=False)
    op.create_index("ix_chats_updated_at", "chats", [sa.text("updated_at desc")], unique=False)

    op.create_table(
        "chat_members",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("role", chat_member_role, nullable=False, server_default="member"),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("left_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("left_at is null or left_at >= joined_at", name="chat_members_left_after_joined"),
        sa.ForeignKeyConstraint(["chat_id"], ["chats.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ux_chat_members_active", "chat_members", ["chat_id", "user_id"], unique=True, postgresql_where=sa.text("left_at is null"))
    op.create_index("ix_chat_members_user_id", "chat_members", ["user_id"], unique=False)
    op.create_index("ix_chat_members_chat_id", "chat_members", ["chat_id"], unique=False)
    op.create_index("ix_chat_members_active_chat", "chat_members", ["chat_id"], unique=False, postgresql_where=sa.text("left_at is null"))
    op.create_index("ix_chat_members_active_user", "chat_members", ["user_id"], unique=False, postgresql_where=sa.text("left_at is null"))

    op.create_table(
        "messages",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("sender_id", sa.BigInteger(), nullable=True),
        sa.Column("message_type", message_type, nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("text is null or length(btrim(text)) > 0", name="messages_text_not_blank"),
        sa.ForeignKeyConstraint(["chat_id"], ["chats.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_messages_chat_id_created_at", "messages", ["chat_id", sa.text("created_at desc")], unique=False)
    op.create_index("ix_messages_sender_id", "messages", ["sender_id"], unique=False)
    op.create_index("ix_messages_active_by_chat", "messages", ["chat_id", sa.text("created_at desc")], unique=False, postgresql_where=sa.text("deleted_at is null"))

    op.execute(
        """
        CREATE TRIGGER trg_users_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_chats_updated_at
        BEFORE UPDATE ON chats
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_messages_updated_at
        BEFORE UPDATE ON messages
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_messages_touch_chat
        AFTER INSERT ON messages
        FOR EACH ROW
        EXECUTE FUNCTION touch_chat_updated_at();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_messages_touch_chat ON messages;")
    op.execute("DROP TRIGGER IF EXISTS trg_messages_updated_at ON messages;")
    op.execute("DROP TRIGGER IF EXISTS trg_chats_updated_at ON chats;")
    op.execute("DROP TRIGGER IF EXISTS trg_users_updated_at ON users;")

    op.drop_index("ix_messages_active_by_chat", table_name="messages")
    op.drop_index("ix_messages_sender_id", table_name="messages")
    op.drop_index("ix_messages_chat_id_created_at", table_name="messages")
    op.drop_table("messages")

    op.drop_index("ix_chat_members_active_user", table_name="chat_members")
    op.drop_index("ix_chat_members_active_chat", table_name="chat_members")
    op.drop_index("ix_chat_members_chat_id", table_name="chat_members")
    op.drop_index("ix_chat_members_user_id", table_name="chat_members")
    op.drop_index("ux_chat_members_active", table_name="chat_members")
    op.drop_table("chat_members")

    op.drop_index("ix_chats_updated_at", table_name="chats")
    op.drop_index("ix_chats_created_by", table_name="chats")
    op.drop_index("ix_chats_type", table_name="chats")
    op.drop_table("chats")

    op.drop_index("ux_users_phone", table_name="users")
    op.drop_index("ux_users_email", table_name="users")
    op.drop_table("users")

    message_type.drop(op.get_bind(), checkfirst=True)
    chat_member_role.drop(op.get_bind(), checkfirst=True)
    chat_type.drop(op.get_bind(), checkfirst=True)

    op.execute("DROP FUNCTION IF EXISTS touch_chat_updated_at();")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at();")
