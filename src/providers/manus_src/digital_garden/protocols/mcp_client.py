"""
🔌 MCP Client — Клиент Model Context Protocol
===============================================
Позволяет Management Core вызывать внешние инструменты
через стандартизированный протокол MCP.

MCP-серверы — это «исполнители», которые:
- Предоставляют список своих инструментов (tools)
- Принимают вызовы инструментов с параметрами
- Возвращают результат в унифицированном формате

Поддерживаемые транспорты:
- stdio (локальный процесс)
- HTTP/SSE (удалённый сервер)
- WebSocket (реалтайм)
"""

import asyncio
import json
import logging
import subprocess
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field

logger = logging.getLogger("garden.mcp")


@dataclass
class MCPTool:
    """Описание инструмента MCP-сервера."""
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)  # JSON Schema
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


@dataclass
class MCPServer:
    """Описание подключённого MCP-сервера."""
    id: str
    name: str
    transport: str  # "stdio" | "http" | "websocket"
    command: Optional[str] = None  # Для stdio: команда запуска
    url: Optional[str] = None  # Для http/ws: URL сервера
    tools: List[MCPTool] = field(default_factory=list)
    is_connected: bool = False
    _process: Optional[subprocess.Popen] = field(default=None, repr=False)


class MCPClient:
    """
    Клиент для взаимодействия с MCP-серверами.
    
    Использование:
        client = MCPClient()
        
        # Подключить сервер
        await client.connect_server(MCPServer(
            id="browser",
            name="Browser Use",
            transport="http",
            url="http://localhost:8001/mcp",
        ))
        
        # Вызвать инструмент
        result = await client.call_tool("browser", "navigate", {"url": "https://hh.ru"})
    """
    
    def __init__(self):
        self.servers: Dict[str, MCPServer] = {}
        self._sessions: Dict[str, Any] = {}  # Активные сессии по server_id
    
    async def connect_server(self, server: MCPServer) -> bool:
        """
        Подключается к MCP-серверу и получает список инструментов.
        
        Returns:
            True если подключение успешно
        """
        try:
            if server.transport == "stdio":
                return await self._connect_stdio(server)
            elif server.transport == "http":
                return await self._connect_http(server)
            elif server.transport == "websocket":
                return await self._connect_websocket(server)
            else:
                logger.error(f"❌ Неизвестный транспорт: {server.transport}")
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к {server.name}: {e}")
            return False
    
    async def disconnect_server(self, server_id: str):
        """Отключает MCP-сервер."""
        server = self.servers.get(server_id)
        if not server:
            return
        
        if server.transport == "stdio" and server._process:
            server._process.terminate()
            server._process = None
        
        server.is_connected = False
        logger.info(f"🔌 Отключён: {server.name}")
    
    async def call_tool(self, server_id: str, tool_name: str, 
                        arguments: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Вызывает инструмент на MCP-сервере.
        
        Args:
            server_id: ID сервера
            tool_name: Имя инструмента
            arguments: Параметры вызова
        
        Returns:
            {"success": bool, "result": Any, "error": Optional[str]}
        """
        server = self.servers.get(server_id)
        if not server or not server.is_connected:
            return {"success": False, "result": None, "error": f"Сервер {server_id} не подключён"}
        
        # Проверяем что инструмент существует
        tool = next((t for t in server.tools if t.name == tool_name), None)
        if not tool:
            available = [t.name for t in server.tools]
            return {
                "success": False, 
                "result": None, 
                "error": f"Инструмент '{tool_name}' не найден. Доступны: {available}"
            }
        
        # Формируем MCP-запрос
        request = {
            "jsonrpc": "2.0",
            "id": f"{server_id}_{tool_name}_{int(asyncio.get_event_loop().time())}",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {},
            }
        }
        
        try:
            if server.transport == "stdio":
                response = await self._call_stdio(server, request)
            elif server.transport == "http":
                response = await self._call_http(server, request)
            else:
                response = await self._call_websocket(server, request)
            
            if "error" in response:
                return {"success": False, "result": None, "error": response["error"]}
            
            return {"success": True, "result": response.get("result"), "error": None}
            
        except Exception as e:
            logger.error(f"❌ Ошибка вызова {tool_name}@{server.name}: {e}")
            return {"success": False, "result": None, "error": str(e)}
    
    def list_tools(self, server_id: Optional[str] = None) -> List[Dict]:
        """Список всех доступных инструментов (или для конкретного сервера)."""
        tools = []
        
        servers = [self.servers[server_id]] if server_id else self.servers.values()
        
        for server in servers:
            if not server.is_connected:
                continue
            for tool in server.tools:
                tools.append({
                    "server": server.name,
                    "server_id": server.id,
                    **tool.to_dict(),
                })
        
        return tools
    
    def find_tool(self, query: str) -> Optional[Dict]:
        """Ищет инструмент по описанию (семантический поиск)."""
        query_lower = query.lower()
        
        best_match = None
        best_score = 0
        
        for tool_info in self.list_tools():
            # Простой scoring по совпадению слов
            desc = (tool_info["name"] + " " + tool_info["description"]).lower()
            score = sum(1 for word in query_lower.split() if word in desc)
            
            if score > best_score:
                best_score = score
                best_match = tool_info
        
        return best_match
    
    # ═══════════════════════════════════════════════════════════════
    # ТРАНСПОРТЫ
    # ═══════════════════════════════════════════════════════════════
    
    async def _connect_stdio(self, server: MCPServer) -> bool:
        """Подключение через stdio (запуск локального процесса)."""
        if not server.command:
            logger.error(f"❌ Не указана команда для stdio-сервера {server.name}")
            return False
        
        # Запускаем процесс
        process = subprocess.Popen(
            server.command.split(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        server._process = process
        
        # Отправляем initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": "init",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "digital-garden", "version": "1.0.0"},
            }
        }
        
        response = await self._call_stdio(server, init_request)
        
        if response:
            # Получаем список инструментов
            tools_request = {
                "jsonrpc": "2.0",
                "id": "tools",
                "method": "tools/list",
                "params": {},
            }
            tools_response = await self._call_stdio(server, tools_request)
            
            if tools_response and "result" in tools_response:
                server.tools = [
                    MCPTool(
                        name=t["name"],
                        description=t.get("description", ""),
                        parameters=t.get("inputSchema", {}),
                    )
                    for t in tools_response["result"].get("tools", [])
                ]
            
            server.is_connected = True
            self.servers[server.id] = server
            logger.info(f"✅ Подключён (stdio): {server.name} — {len(server.tools)} инструментов")
            return True
        
        return False
    
    async def _connect_http(self, server: MCPServer) -> bool:
        """Подключение через HTTP/SSE."""
        import aiohttp
        
        if not server.url:
            logger.error(f"❌ Не указан URL для http-сервера {server.name}")
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                # Пробуем получить список инструментов
                request = {
                    "jsonrpc": "2.0",
                    "id": "tools",
                    "method": "tools/list",
                    "params": {},
                }
                
                async with session.post(
                    server.url,
                    json=request,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if "result" in data:
                            server.tools = [
                                MCPTool(
                                    name=t["name"],
                                    description=t.get("description", ""),
                                    parameters=t.get("inputSchema", {}),
                                )
                                for t in data["result"].get("tools", [])
                            ]
                        
                        server.is_connected = True
                        self.servers[server.id] = server
                        logger.info(f"✅ Подключён (http): {server.name} — {len(server.tools)} инструментов")
                        return True
                    else:
                        logger.error(f"❌ HTTP {resp.status} от {server.name}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Не удалось подключиться к {server.name}: {e}")
            return False
    
    async def _connect_websocket(self, server: MCPServer) -> bool:
        """Подключение через WebSocket."""
        # TODO: WebSocket транспорт
        logger.warning(f"⚠️ WebSocket транспорт пока не реализован для {server.name}")
        return False
    
    async def _call_stdio(self, server: MCPServer, request: Dict) -> Dict:
        """Отправка запроса через stdio."""
        if not server._process or server._process.poll() is not None:
            return {"error": "Процесс не запущен"}
        
        # Отправляем JSON + newline
        request_bytes = (json.dumps(request) + "\n").encode()
        server._process.stdin.write(request_bytes)
        server._process.stdin.flush()
        
        # Читаем ответ (с таймаутом)
        try:
            loop = asyncio.get_event_loop()
            response_line = await asyncio.wait_for(
                loop.run_in_executor(None, server._process.stdout.readline),
                timeout=30.0,
            )
            return json.loads(response_line.decode())
        except asyncio.TimeoutError:
            return {"error": "Таймаут ожидания ответа"}
        except json.JSONDecodeError:
            return {"error": "Невалидный JSON в ответе"}
    
    async def _call_http(self, server: MCPServer, request: Dict) -> Dict:
        """Отправка запроса через HTTP."""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    server.url,
                    json=request,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        error_text = await resp.text()
                        return {"error": f"HTTP {resp.status}: {error_text[:200]}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def _call_websocket(self, server: MCPServer, request: Dict) -> Dict:
        """Отправка запроса через WebSocket."""
        return {"error": "WebSocket не реализован"}
