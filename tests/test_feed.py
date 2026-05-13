import responses

from ai_rss.config import Source
from ai_rss.feed import collect_feed


def test_collect_feed_sends_browser_like_user_agent() -> None:
    source = Source(
        name="Microsoft AI Blog",
        type="rss",
        priority="P0",
        url="https://blogs.microsoft.com/ai/feed/",
        tags=["official"],
    )

    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            source.url,
            body="""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><item><title>AI update</title><link>https://example.com/ai</link></item></channel></rss>
""",
            status=200,
        )

        items = collect_feed(source)
        request = rsps.calls[0].request

    assert "Mozilla/5.0" in request.headers["User-Agent"]
    assert items[0].title == "AI update"
