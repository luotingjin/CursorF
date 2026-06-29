from __future__ import annotations

import json
import time
from typing import Any
import requests

from tapd_testcase.models import Story


class TapdAPIError(Exception):
    def __init__(self, message: str, status_code: int | None = None, payload: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class TapdClient:
    """TAPD Open API 客户端，支持 Basic Auth 与 Bearer Token。"""

    def __init__(
        self,
        api_base: str,
        client_id: str | None = None,
        client_secret: str | None = None,
        access_token: str | None = None,
        timeout: int = 60,
    ):
        self.api_base = api_base.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token = access_token
        self._token_expires_at = 0.0
        self.timeout = timeout
        self.session = requests.Session()

    def _get_access_token(self) -> str:
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token

        if self._access_token and self._token_expires_at == 0:
            return self._access_token

        if not self.client_id or not self.client_secret:
            raise TapdAPIError("未配置 access_token，且缺少 client_id/client_secret")

        url = f"{self.api_base}/tokens/request_token"
        resp = self.session.post(
            url,
            data={"grant_type": "client_credentials"},
            auth=(self.client_id, self.client_secret),
            timeout=self.timeout,
        )
        self._raise_for_response(resp)
        body = resp.json()
        if body.get("status") != 1:
            raise TapdAPIError(f"获取 access_token 失败: {body.get('info')}", payload=body)

        token_data = body["data"]
        self._access_token = token_data["access_token"]
        self._token_expires_at = time.time() + int(token_data.get("expires_in", 7200)) - 60
        return self._access_token

    def _auth_headers(self) -> dict[str, str]:
        if self.client_id and self.client_secret and not self._access_token:
            return {}
        token = self._get_access_token()
        return {"Authorization": f"Bearer {token}"}

    def _auth(self) -> tuple[str, str] | None:
        if self._access_token and self._token_expires_at == 0:
            return None
        if self.client_id and self.client_secret:
            return (self.client_id, self.client_secret)
        return None

    def _raise_for_response(self, resp: requests.Response) -> None:
        if resp.status_code >= 400:
            raise TapdAPIError(
                f"HTTP {resp.status_code}: {resp.text[:500]}",
                status_code=resp.status_code,
            )

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        data: Any = None,
        json_body: Any = None,
    ) -> Any:
        url = f"{self.api_base}/{path.lstrip('/')}"
        headers = self._auth_headers()
        if json_body is not None:
            headers["Content-Type"] = "application/json"

        resp = self.session.request(
            method=method,
            url=url,
            params=params,
            data=data,
            json=json_body,
            headers=headers,
            auth=self._auth(),
            timeout=self.timeout,
        )
        self._raise_for_response(resp)
        body = resp.json()
        if body.get("status") != 1:
            raise TapdAPIError(f"TAPD API 错误: {body.get('info')}", payload=body)
        return body.get("data")

    def get_stories(
        self,
        workspace_id: str,
        *,
        story_ids: list[str] | None = None,
        iteration_id: str | None = None,
        status: str | None = None,
        limit: int = 30,
        page: int = 1,
        fields: str | None = None,
    ) -> list[Story]:
        params: dict[str, Any] = {
            "workspace_id": workspace_id,
            "limit": min(limit, 200),
            "page": page,
        }
        if story_ids:
            params["id"] = ",".join(story_ids)
        if iteration_id:
            params["iteration_id"] = iteration_id
        if status:
            params["status"] = status
        if fields:
            params["fields"] = fields
        else:
            params["fields"] = "id,name,description,test_focus,status,priority,priority_label,owner,workspace_id"

        data = self._request("GET", "/stories", params=params)
        if not data:
            return []
        return [Story.from_tapd(item) for item in data]

    def iter_stories(
        self,
        workspace_id: str,
        *,
        story_ids: list[str] | None = None,
        iteration_id: str | None = None,
        status: str | None = None,
        limit: int = 30,
        max_pages: int = 10,
    ):
        if story_ids:
            for i in range(0, len(story_ids), 50):
                chunk = story_ids[i : i + 50]
                yield from self.get_stories(workspace_id, story_ids=chunk, limit=len(chunk))
            return

        for page in range(1, max_pages + 1):
            stories = self.get_stories(
                workspace_id,
                iteration_id=iteration_id,
                status=status,
                limit=limit,
                page=page,
            )
            if not stories:
                break
            yield from stories
            if len(stories) < limit:
                break

    def batch_create_tcases(self, cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not cases:
            return []
        data = self._request("POST", "/tcases/batch_save", json_body=cases)
        if not data:
            return []
        return [item.get("Tcase", item) for item in data]

    def create_tcase(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = self._request("POST", "/tcases", data=payload)
        return data.get("Tcase", data)

    def link_story_to_test_plan(
        self,
        workspace_id: str,
        test_plan_id: str,
        story_ids: list[str],
        creator: str,
    ) -> None:
        payload = {
            "workspace_id": workspace_id,
            "plan_id": test_plan_id,
            "story_ids": ",".join(story_ids[:10]),
            "creator": creator,
        }
        self._request("POST", "/test_plans/create_story_relation", data=payload)

    def link_tcases_to_test_plan(
        self,
        workspace_id: str,
        test_plan_id: str,
        tcase_ids: list[str],
        creator: str,
    ) -> None:
        for i in range(0, len(tcase_ids), 10):
            chunk = tcase_ids[i : i + 10]
            payload = {
                "workspace_id": workspace_id,
                "test_plan_id": test_plan_id,
                "tcase_ids": ",".join(chunk),
                "creator": creator,
            }
            self._request("POST", "/test_plans/create_tcase_relation", data=payload)

    def get_story_tcases(self, workspace_id: str, story_id: str) -> list[dict[str, Any]]:
        params = {"workspace_id": workspace_id, "story_id": story_id}
        data = self._request("GET", "/stories/get_story_tcase", params=params)
        if not data:
            return []
        return [item.get("TestPlanStoryTcaseRelation", item) for item in data]
