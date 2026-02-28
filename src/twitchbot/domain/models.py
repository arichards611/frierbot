from __future__ import annotations
from dataclasses import dataclass, field

@dataclass(frozen=True, slots=True)
class IrcMessage:
    """A parsed IRC message from Twitch. This is the format that Twitch sends messages in, and is used for parsing incoming messages from Twitch."""
    
    tags: dict[str, str] = field(default_factory=dict)
    prefix: str | None = None
    command: str
    params: list[str] = field(default_factory=list)
    trailing_message: str | None = None
    
    @property
    def nick(self) -> str | None:
        """The nickname of the user who sent the message, if available."""
        if self.prefix is None:
            return None
        return self.prefix.split('!',1)[0]
    
    def to_chat_message(self) -> TwitchChatMessage | None:
        """Convert this IrcMessage to a TwitchChatMessage, which is the format that the bot will use for processing chat messages."""
        if self.command != 'PRIVMSG' or not self.params:
            return None
        
        roles=self._parse_badges_to_roles(self.tags.get('badges', ''))

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
    """A Twitch chat message, parsed from an IrcMessage. This is the format that the bot will use for processing chat messages."""
    
    channel: str
    user: str
    message: str
    roles: set[str] = field(default_factory=set)
    raw: IrcMessage | None = None

@dataclass(frozen=True, slots=True)
class OutgoingMessage:
    """A message to be sent to Twitch. This is the format that the bot will use for sending messages to Twitch."""
    
    channel: str
    text: str

@dataclass(frozen=True, slots=True)
class TwitchCommand:
    """A command that the bot can execute. This is the format that the bot will use for processing commands."""
    
    message: TwitchChatMessage
    command: str
    args: list[str] = field(default_factory=list)