from twitchbot.domain.irc import parse_irc_line
from twitchbot.domain.models import OutgoingMessage, TwitchChatMessage, TwitchCommand


class TestIrcMessageToChatMessage:
    def test_privmsg_converts_to_chat_message(self):
        raw = (
            "@badges=moderator/1,subscriber/0;display-name=CoolUser "
            ":cooluser!cooluser@cooluser.tmi.twitch.tv PRIVMSG #mychannel :!ping"
        )
        msg = parse_irc_line(raw)
        chat = msg.to_chat_message()

        assert chat is not None
        assert chat.channel == "#mychannel"
        assert chat.user == "CoolUser"
        assert chat.message == "!ping"
        assert "moderator" in chat.roles
        assert "subscriber" in chat.roles
        assert chat.raw is msg

    def test_non_privmsg_returns_none(self):
        msg = parse_irc_line("PING :tmi.twitch.tv")
        assert msg.to_chat_message() is None

    def test_join_returns_none(self):
        msg = parse_irc_line(":user!user@user.tmi.twitch.tv JOIN #channel")
        assert msg.to_chat_message() is None

    def test_privmsg_no_badges(self):
        raw = (
            "@display-name=Guest "
            ":guest!guest@guest.tmi.twitch.tv PRIVMSG #chan :hello"
        )
        chat = parse_irc_line(raw).to_chat_message()
        assert chat is not None
        assert chat.roles == set()
        assert chat.user == "Guest"

    def test_privmsg_falls_back_to_nick(self):
        raw = ":someone!someone@someone.tmi.twitch.tv PRIVMSG #chan :hi"
        chat = parse_irc_line(raw).to_chat_message()
        assert chat is not None
        assert chat.user == "someone"

    def test_broadcaster_badge(self):
        raw = (
            "@badges=broadcaster/1 "
            ":streamer!streamer@streamer.tmi.twitch.tv PRIVMSG #streamer :test"
        )
        chat = parse_irc_line(raw).to_chat_message()
        assert chat is not None
        assert "broadcaster" in chat.roles

    def test_vip_badge(self):
        raw = (
            "@badges=vip/1 "
            ":vipuser!vipuser@vipuser.tmi.twitch.tv PRIVMSG #chan :yo"
        )
        chat = parse_irc_line(raw).to_chat_message()
        assert chat is not None
        assert "vip" in chat.roles

    def test_multiple_badges(self):
        raw = (
            "@badges=moderator/1,vip/1,subscriber/12 "
            ":user!user@user.tmi.twitch.tv PRIVMSG #chan :hi"
        )
        chat = parse_irc_line(raw).to_chat_message()
        assert chat is not None
        assert chat.roles == {"moderator", "vip", "subscriber"}


class TestDataclasses:
    def test_outgoing_message(self):
        msg = OutgoingMessage(channel="#test", text="hello")
        assert msg.channel == "#test"
        assert msg.text == "hello"

    def test_twitch_command(self):
        chat = TwitchChatMessage(channel="#ch", user="u", message="!echo hi there")
        ctx = TwitchCommand(message=chat, command="echo", args=["hi", "there"])
        assert ctx.command == "echo"
        assert ctx.args == ["hi", "there"]
        assert ctx.message.user == "u"

    def test_twitch_command_default_args(self):
        chat = TwitchChatMessage(channel="#ch", user="u", message="!ping")
        ctx = TwitchCommand(message=chat, command="ping")
        assert ctx.args == []

    def test_twitch_chat_message_default_roles(self):
        chat = TwitchChatMessage(channel="#ch", user="u", message="hi")
        assert chat.roles == set()
        assert chat.raw is None
