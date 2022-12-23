import datetime

import pytest
import mock

from koala import transformers


@pytest.mark.asyncio
async def test_extension_empty_choices():
    transformer = transformers.ExtensionTransformer()
    choices = await transformer.choices()
    assert [] == choices


@mock.patch("koala.db.get_all_available_guild_extensions", mock.MagicMock(return_value=['Cog1', 'Cog2']))
@pytest.mark.asyncio
async def test_extension_choices():
    transformer = transformers.ExtensionTransformer()
    choices = await transformer.choices()
    assert 2 == len(choices)


@pytest.mark.asyncio
async def test_datetime_transform_error(mock_interaction):
    transformer = transformers.DatetimeTransformer()
    with pytest.raises(ValueError,
                       match='Invalid ISO format "1234", instead use the format "2020-01-01 00:00:00"'):
        time = await transformer.transform(mock_interaction, "1234")


@pytest.mark.asyncio
async def test_datetime_transform(mock_interaction):
    transformer = transformers.DatetimeTransformer()
    time = await transformer.transform(mock_interaction, "2000-01-01 00:00:00")
    assert "2000-01-01 00:00:00" == str(time)
