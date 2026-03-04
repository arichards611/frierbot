import pytest

from twitchbot.domain.irc import (
    build_join,
    build_pass_nick,
    build_pong,
    build_privmsg,
    parse_irc_line,
)


class TestParseIrcLine:
    def test_parse_privmsg_with_tags(self):
        raw = (
            "@badges=moderator/1,subscriber/0;display-name=TestUser "
            ":testuser!testuser@testuser.tmi.twitch.tv PRIVMSG #channel :hello world"
        )
        msg = parse_irc_line(raw)

        assert msg.command == "PRIVMSG"
        assert msg.prefix == "testuser!testuser@testuser.tmi.twitch.tv"
        assert msg.nick == "testuser"
        assert msg.params == ["#channel"]
        assert msg.trailing_message == "hello world"
        assert msg.tags["display-name"] == "TestUser"
        assert msg.tags["badges"] == "moderator/1,subscriber/0"

    def test_parse_ping(self):
        msg = parse_irc_line("PING :tmi.twitch.tv")
        assert msg.command == "PING"
        assert msg.trailing_message == "tmi.twitch.tv"
        assert msg.params == []

    def test_parse_join(self):
        msg = parse_irc_line(":testuser!testuser@testuser.tmi.twitch.tv JOIN #channel")
        assert msg.command == "JOIN"
        assert msg.params == ["#channel"]
        assert msg.nick == "testuser"

    def test_parse_part(self):
        msg = parse_irc_line(":testuser!testuser@testuser.tmi.twitch.tv PART #channel")
        assert msg.command == "PART"
        assert msg.params == ["#channel"]

    def test_parse_numeric_command(self):
        msg = parse_irc_line(":tmi.twitch.tv 001 botname :Welcome, GLHF!")
        assert msg.command == "001"
        assert msg.params == ["botname"]
        assert msg.trailing_message == "Welcome, GLHF!"

    def test_parse_empty_line_raises(self):
        with pytest.raises(ValueError, match="Empty"):
            parse_irc_line("")

    def test_parse_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="Empty"):
            parse_irc_line("   \n")

    def test_parse_no_prefix_no_tags(self):
        msg = parse_irc_line("CAP REQ :twitch.tv/tags")
        assert msg.command == "CAP"
        assert msg.params == ["REQ"]
        assert msg.trailing_message == "twitch.tv/tags"
        assert msg.prefix is None
        assert msg.tags == {}

    def test_parse_tags_without_values(self):
        msg = parse_irc_line("@emote-only;slow :tmi.twitch.tv ROOMSTATE #channel")
        assert msg.tags["emote-only"] == ""
        assert msg.tags["slow"] == ""

    def test_command_is_uppercased(self):
        msg = parse_irc_line("ping :test")
        assert msg.command == "PING"

    def test_nick_without_bang(self):
        msg = parse_irc_line(":servername NOTICE * :message")
        assert msg.nick == "servername"

    def test_nick_is_none_when_no_prefix(self):
        msg = parse_irc_line("PING :test")
        assert msg.nick is None


class TestBuildLines:
    def test_build_privmsg(self):
        assert build_privmsg("#channel", "hello") == "PRIVMSG #channel :hello"

    def test_build_pong(self):
        assert build_pong("tmi.twitch.tv") == "PONG :tmi.twitch.tv"

    def test_build_join(self):
        assert build_join("#channel") == "JOIN #channel"

    def test_build_pass_nick(self):
        lines = build_pass_nick("mytoken123", "botname")
        assert lines == ["PASS oauth:mytoken123", "NICK botname"]


class TestRoundTrip:
    def test_privmsg_round_trip(self):
        original = build_privmsg("#test", "hello world")
        parsed = parse_irc_line(original)
        assert parsed.command == "PRIVMSG"
        assert parsed.params == ["#test"]
        assert parsed.trailing_message == "hello world"

    def test_pong_round_trip(self):
        original = build_pong("tmi.twitch.tv")
        parsed = parse_irc_line(original)
        assert parsed.command == "PONG"
        assert parsed.trailing_message == "tmi.twitch.tv"
