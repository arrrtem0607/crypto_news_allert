from pydantic import SecretStr

from app.core.config import TelegramSettings
from app.core.telegram import TelegramPublisher


def test_config_channel_id_variants():
    s1 = TelegramSettings(bot_token=SecretStr("t"), channel_id="-100123")
    assert isinstance(s1.channel_id, int)
    s2 = TelegramSettings(bot_token=SecretStr("t"), channel_id=-100456)
    assert isinstance(s2.channel_id, int)
    s3 = TelegramSettings(bot_token=SecretStr("t"), channel_id="@alias")
    assert s3.channel_id == "@alias"


def test_secretstr_unwrap():
    pub = TelegramPublisher(SecretStr("abc123"), "-1001")
    assert pub.bot.token == "abc123"
    assert isinstance(pub.chat_id, int)
