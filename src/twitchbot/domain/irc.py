"""Parse and build Twitch IRC protocol lines.

Reference: https://datatracker.ietf.org/doc/html/rfc1459#section-2.3.1
Twitch extensions: https://dev.twitch.tv/docs/irc/
"""

from __future__ import annotations

from twitchbot.domain.models import IrcMessage


def parse_irc_line(raw: str) -> IrcMessage:
    """Parse a raw IRC line into an IrcMessage.

    Format: [@tags] [:prefix] COMMAND [params...] [:trailing]
    """
    line = raw.strip()
    if not line:
        raise ValueError("Empty IRC line")

    tags: dict[str, str] = {}
    prefix: str | None = None

    # Parse tags (@key=value;key2=value2)
    if line.startswith("@"):
        tag_part, line = line.split(" ", 1)
        tags = _parse_tags(tag_part[1:])

    # Parse prefix (:nick!user@host)
    if line.startswith(":"):
        prefix_part, line = line.split(" ", 1)
        prefix = prefix_part[1:]

    # Split trailing (after " :")
    trailing: str | None = None
    if " :" in line:
        line, trailing = line.split(" :", 1)

    parts = line.split()
    command = parts[0].upper()
    params = parts[1:]

    return IrcMessage(
        command=command,
        params=params,
        prefix=prefix,
        tags=tags,
        trailing=trailing,
    )


def _parse_tags(raw: str) -> dict[str, str]:
    """Parse IRC tags string into a dict."""
    return dict(
        kv.split("=", 1) if "=" in kv else (kv, "")
        for kv in raw.split(";")
        if kv
    )


def build_privmsg(channel: str, text: str) -> str:
    return f"PRIVMSG {channel} :{text}"


def build_pong(payload: str) -> str:
    return f"PONG :{payload}"


def build_join(channel: str) -> str:
    return f"JOIN {channel}"


def build_pass_nick(token: str, nick: str) -> list[str]:
    return [f"PASS oauth:{token}", f"NICK {nick}"]
