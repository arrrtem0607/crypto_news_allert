import asyncio
import aiohttp
from aiohttp import web

from app.providers.newsdata import NewsdataProvider


def test_newsdata_params_building():
    async def inner():
        async with aiohttp.ClientSession() as session:
            provider = NewsdataProvider(session, {"api_key": "k"})
            req = provider._build_request()
            assert req["url"] == "https://newsdata.io/api/1/crypto"
            params = req["params"]
            assert params["apikey"] == "k"
            assert params["removeduplicate"] == "1"
            assert params["size"] == "50"

    asyncio.run(inner())


def test_newsdata_pagination():
    async def inner():
        async def handler(request):
            page = request.query.get("page")
            if page == "2":
                return web.json_response(
                    {"results": [{"link": "u2", "pubDate": "2024-01-01T00:00:00Z"}]}
                )
            return web.json_response(
                {
                    "results": [{"link": "u1", "pubDate": "2024-01-01T00:00:00Z"}],
                    "nextPage": "2",
                }
            )

        app = web.Application()
        app.router.add_get("/api/1/crypto", handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        port = site._server.sockets[0].getsockname()[1]
        base_url = f"http://127.0.0.1:{port}/api/1"
        try:
            async with aiohttp.ClientSession() as session:
                provider = NewsdataProvider(
                    session,
                    {"api_key": "k", "base_url": base_url},
                )
                items = await provider.poll()
        finally:
            await runner.cleanup()
        return items

    items = asyncio.run(inner())
    links = [i["link"] for i in items]
    assert links == ["u1", "u2"]
