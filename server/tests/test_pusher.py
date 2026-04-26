# server/tests/test_pusher.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import pusher


@pytest.mark.asyncio
async def test_push_posts_to_pi_url():
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()

    with patch("pusher.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value.__aenter__ = AsyncMock(
            return_value=MockClient.return_value
        )
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)
        MockClient.return_value.post = AsyncMock(return_value=mock_resp)

        await pusher.push_to_display(b"fake-png-bytes")

        MockClient.return_value.post.assert_called_once()
        url_arg = MockClient.return_value.post.call_args[0][0]
        assert url_arg == pusher.PI_CLIENT_URL


@pytest.mark.asyncio
async def test_push_raises_on_http_error():
    with patch("pusher.httpx.AsyncClient") as MockClient:
        MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("connection refused")
        MockClient.return_value.post = AsyncMock(return_value=mock_resp)

        with pytest.raises(Exception, match="connection refused"):
            await pusher.push_to_display(b"fake-png-bytes")
