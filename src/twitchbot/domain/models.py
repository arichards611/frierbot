from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class IrcMessage:
    """A parsed IRC protocol message."""

    command: str
    params: list[str] = field(default_factory=list)
    prefix: str | None = None
    tags: dict[str, str] = field(default_factory=dict)
    trailing: str | None = None

    @property
    def nick(self) -> str | None:
        """Extract nickname from prefix (nick!user@host)."""
        if self.prefix and "!" in self.prefix:
            return self.prefix.split("!", 1)[0]
        return self.prefix

    def to_chat_message(self) -> ChatMessage | None:
        """Convert PRIVMSG IrcMessage to a ChatMessage. Returns None for non-PRIVMSG."""
        if self.command != "PRIVMSG" or not self.params:
            return None
        badges_raw = self.tags.get("badges", "")
        roles = _parse_badges_to_roles(badges_raw)
        return ChatMessage(
            channel=self.params[0],
            user=self.tags.get("display-name", self.nick or ""),
            text=self.trailing or "",
            roles=roles,
            raw=self,
        )


def _parse_badges_to_roles(badges: str) -> set[str]:
    """Extract role names from a Twitch badges tag value (e.g. 'moderator/1,subscriber/0')."""
    if not badges:
        return set()
    return {badge.split("/", 1)[0] for badge in badges.split(",") if "/" in badge}


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """A normalized chat message with user info and roles."""

    channel: str
    user: str
    text: str
    roles: set[str] = field(default_factory=set)
    raw: IrcMessage | None = None


@dataclass(frozen=True, slots=True)
class OutgoingMessage:
    """A message to send to a channel."""

    channel: str
    text: str


@dataclass(frozen=True, slots=True)
class CommandContext:
    """Context passed to a command handler."""

    message: ChatMessage
    command: str
    args: list[str] = field(default_factory=list)
