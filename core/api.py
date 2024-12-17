import asyncio
import aiohttp
import numpy as np
from typing import List, Dict, Any, Optional
from config.settings import API_NODES_ENDPOINT


class ApiManager:
    def __init__(self, auth_manager):
        self.auth_manager = auth_manager
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        await self.get_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_session()

    async def get_session(self) -> aiohttp.ClientSession:
        try:
            if self._session is None or self._session.closed:
                self._session = aiohttp.ClientSession(
                    connector=aiohttp.TCPConnector(force_close=True))
            return self._session
        except Exception:
            raise

    async def close_session(self):
        try:
            if self._session and not self._session.closed:
                await self._session.close()
                self._session = None
        except Exception:
            raise

    async def get_node_attributes(self) -> Dict[str, Any]:
        async with self:  # Используем контекстный менеджер
            api_key = await self.auth_manager.get_api_key()
            if not api_key:
                return None

            url = f"{self.auth_manager.server}{API_NODES_ENDPOINT}?getAttributes=True"
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }

            try:
                session = await self.get_session()
                async with session.get(url, headers=headers) as response:
                    response.raise_for_status()
                    return await response.json()
            except Exception:
                return None

    async def get_sources_names(self) -> List[str]:
        data = await self.get_node_attributes()
        source_names = []
        if data is not None:
            for node in data['nodes']:
                if node['attributes'] is not None:
                    for attr in node['attributes']:
                        if attr['code'] == 'sourceName':
                            source_names.append(attr['value'])
        source_names = list(dict.fromkeys(source_names))
        source_names.sort()
        return source_names

    async def filter_node_attributes(self, labels: List[str]) -> List[List[str]]:
        data = await self.get_node_attributes()
        if not data:
            return []

        values = []
        node_ids = []
        for node in data['nodes']:
            if node['attributes'] is not None:
                for attr in node['attributes']:
                    if attr['value'] in labels:
                        node_ids.append(attr['nodeId'])
                        values.append(attr['value'])
        return np.column_stack((values, node_ids)).tolist()

    async def push_temperature_data(self, data: List[Dict[str, Any]]) -> bool:
        api_key = await self.auth_manager.get_api_key()
        if not api_key:
            return False

        headers = {
            'Content-Type': 'application/json-patch+json',
            'Authorization': f'Bearer {api_key}'
        }

        session = await self.get_session()
        tasks = []

        # Создаем задачи для каждого элемента данных
        for item in data:
            task = asyncio.create_task(
                self._push_single_temperature(session, headers, item)
            )
            tasks.append(task)

        # Ждем выполнения всех задач
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Проверяем результаты
        return all(isinstance(r, bool) and r for r in results)

    async def _push_single_temperature(
        self,
        session: aiohttp.ClientSession,
        headers: Dict[str, str],
        item: Dict[str, Any]
    ) -> bool:
        try:
            node_id = item["nodeid"]
            tcw = float(item["tcw"])
            push = [
                {
                    "op": "replace",
                    "value": tcw,
                    "path": "coldWaterSummerTemp"
                },
                {
                    "op": "replace",
                    "value": tcw,
                    "path": "coldWaterWinterTemp"
                }
            ]
            url = f"{self.auth_manager.server}{API_NODES_ENDPOINT}/{node_id}"

            async with session.patch(url, headers=headers, json=push) as response:
                response.raise_for_status()
                return True
        except Exception:
            return False

    @staticmethod
    def merge_data(node_data: List[Dict[str, Any]], temp_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {"nodeid": item1["nodeid"], "tcw": item2["tcw"]}
            for item1 in node_data
            for item2 in temp_data
            if item1["src"] == item2["src"]
        ]
