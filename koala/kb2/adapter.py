import asyncio
import threading
import time
from http.client import OK

import requests

from koala.kb2 import env
from koala.kb2.log import logger


class AutherOAuthToken:
    """
    Auther OAuth Token Manager
    https://github.com/JayDwee/auther
    """
    _token: str
    expires_at: int = 0

    def request_token(self):
        logger.debug("Auther Token Request")
        response = requests.post(env.AUTHER_URL + "/token",
                                 data={"grant_type": "client_credentials", "scope": "owner"},
                                 auth=(env.AUTHER_CLIENT_ID, env.AUTHER_CLIENT_SECRET))
        response_json = response.json()
        logger.debug("Auther Token Response: %s", response_json)
        self._token = response_json.get("access_token")
        self.expires_at = response_json.get("expires_in") + int(time.time())

    def get_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    @property
    def token(self) -> str:
        if time.time() > self.expires_at:
            self.request_token()
        return self._token


class KB2Adapter:
    """
    Koala Bot v2 (KB2) Adapter
    https://github.com/KoalaBotUK/KB2
    """
    token: AutherOAuthToken = AutherOAuthToken()

    async def on_raw_interaction(self, raw_interaction: dict):
        try:
            logger.debug("Interact New Interaction: %s", raw_interaction)
            requests.post(env.KB2_URL + '/gateway-interactions',
                          json=raw_interaction,
                          headers={"X-INTERACT-TS": str(int(time.time() * 1000)),
                                   "Content-Type": "application/json"} | self.token.get_headers())
        except Exception as e:
            logger.error("Interact Failed to Process: %s", e, exc_info=True)


kb2_adapter = KB2Adapter()
