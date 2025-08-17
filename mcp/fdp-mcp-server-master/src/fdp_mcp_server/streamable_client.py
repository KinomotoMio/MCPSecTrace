from typing import Any

from mcp import ClientSession, stdio_server
from mcp.client.streamable_http import streamablehttp_client

from fdp_mcp_server.proxy_server import create_proxy_server


async def run_streamable_http_client(url: str, headers: dict[str, Any] | None = None):
    async with (
        streamablehttp_client(url=url, headers=headers) as (read, write, _),
        ClientSession(read, write) as session,
    ):
        app = await create_proxy_server(session)
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream, write_stream, app.create_initialization_options()
            )
