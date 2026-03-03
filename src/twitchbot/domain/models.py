from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class IrcMessage:
    """A parsed IRC message from Twitch."""

    command: str
    tags: dict[str, str] = field(default_factory=dict)
    prefix: str | None = None
    params: list[str] = field(default_factory=list)
    trailing_message: str | None = None

    @property
    def nick(self) -> str | None:
        """The nickname of the user who sent the message, if available."""
        if self.prefix is None:
            return None
        return self.prefix.split('!',1)[0]

    def to_chat_message(self) -> TwitchChatMessage | None:
        """Convert this IrcMessage to a TwitchChatMessage, if it's a PRIVMSG."""
        if self.command != 'PRIVMSG' or not self.params:
            return None

        roles = _parse_badges_to_roles(self.tags.get('badges', ''))

        return TwitchChatMessage(
            roles=roles,
            channel=self.params[0],
            user=self.tags.get('display-name', self.nick or ''),
            message=self.trailing_message or '',
            raw=self
        )

def _parse_badges_to_roles(badges: str) -> set[str]:
    """Extract role names from a Twitch badges tag value (e.g. 'moderator/1,subscriber/0')."""
    roles = set()
    for badge in badges.split(','):
        if '/' in badge:
            role, _ = badge.split('/', 1)
            roles.add(role)
    return roles

@dataclass(frozen=True, slots=True)
class TwitchChatMessage:
    """A normalized Twitch chat message, parsed from an IrcMessage."""

    channel: str
    user: str
    message: str
    roles: set[str] = field(default_factory=set)
    raw: IrcMessage | None = None

@dataclass(frozen=True, slots=True)
class OutgoingMessage:
    """A message to be sent to a Twitch channel."""

    channel: str
    text: str

@dataclass(frozen=True, slots=True)
class TwitchCommand:
    """Parsed command context passed to a handler."""

    message: TwitchChatMessage
    command: str
    args: list[str] = field(default_factory=list)
