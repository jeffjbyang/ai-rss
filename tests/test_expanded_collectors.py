from pathlib import Path

from ai_rss.arxiv import collect_arxiv_query, parse_arxiv_atom
from ai_rss.config import Source
from ai_rss.config import load_sources
from ai_rss.default_sources import DEFAULT_SOURCES
from ai_rss.webpage import parse_web_page
from ai_rss.github import collect_github_releases, collect_github_repositories
from ai_rss.hn import collect_hn_feed, parse_hn_feed


class FakeGitHubClient:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get_json(self, url, params=None):
        self.calls.append((url, params))
        return self.payload


class FakeTextClient:
    def __init__(self, text):
        self.text = text
        self.calls = []

    def get_text(self, url):
        self.calls.append(url)
        return self.text


def test_github_repository_search_payload_becomes_candidates() -> None:
    source = Source(
        name="GitHub AI Agent Repos",
        type="github-search",
        priority="P0",
        url="https://api.github.com/search/repositories?q=topic:ai-agent language:Python",
        tags=["github", "ai-coding"],
    )
    client = FakeGitHubClient(
        {
            "items": [
                {
                    "full_name": "example/open-agent",
                    "html_url": "https://github.com/example/open-agent",
                    "description": "AI coding agent for pull request repair",
                    "stargazers_count": 1234,
                    "pushed_at": "2026-05-12T10:00:00Z",
                    "topics": ["ai-agent", "developer-tools"],
                }
            ]
        }
    )

    items = collect_github_repositories(source, client=client)

    assert client.calls == [
        (
            "https://api.github.com/search/repositories",
            {"q": "topic:ai-agent language:Python", "sort": "updated", "order": "desc", "per_page": 25},
        )
    ]
    assert len(items) == 1
    item = items[0]
    assert item.title == "example/open-agent"
    assert item.url == "https://github.com/example/open-agent"
    assert item.published_at == "2026-05-12T10:00:00+00:00"
    assert item.summary == "AI coding agent for pull request repair\nStars: 1234"
    assert item.score == 1234
    assert item.tags == ["github", "ai-coding", "ai-agent", "developer-tools"]


def test_github_release_payload_becomes_candidates_for_configured_repo() -> None:
    source = Source(
        name="OpenHands Releases",
        type="github-releases",
        priority="P0",
        url="https://github.com/All-Hands-AI/OpenHands",
        tags=["github", "ai-coding", "software-delivery"],
    )
    client = FakeGitHubClient(
        [
            {
                "name": "OpenHands 1.2",
                "tag_name": "v1.2.0",
                "html_url": "https://github.com/All-Hands-AI/OpenHands/releases/tag/v1.2.0",
                "published_at": "2026-05-11T18:30:00Z",
                "body": "Improves agent task execution and CI repair.",
            }
        ]
    )

    items = collect_github_releases(source, client=client)

    assert client.calls == [
        (
            "https://api.github.com/repos/All-Hands-AI/OpenHands/releases",
            {"per_page": 10},
        )
    ]
    assert len(items) == 1
    item = items[0]
    assert item.title == "All-Hands-AI/OpenHands release OpenHands 1.2"
    assert item.url == "https://github.com/All-Hands-AI/OpenHands/releases/tag/v1.2.0"
    assert item.published_at == "2026-05-11T18:30:00+00:00"
    assert item.summary == "Improves agent task execution and CI repair."
    assert item.tags == ["github", "ai-coding", "software-delivery", "release"]


def test_arxiv_atom_query_payload_becomes_paper_candidates() -> None:
    source = Source(
        name="arXiv AI Software Engineering",
        type="arxiv",
        priority="P0",
        url="https://export.arxiv.org/api/query?search_query=all:agentic%20coding",
        tags=["research", "ai-coding"],
    )
    atom = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2605.12345v1</id>
    <updated>2026-05-12T14:00:00Z</updated>
    <published>2026-05-12T14:00:00Z</published>
    <title>Agentic Coding Systems for Software Delivery</title>
    <summary>We study code agents that repair CI failures and create pull requests.</summary>
    <author><name>A. Researcher</name></author>
    <link href="http://arxiv.org/abs/2605.12345v1" rel="alternate" type="text/html"/>
    <arxiv:primary_category term="cs.SE" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.AI" scheme="http://arxiv.org/schemas/atom"/>
  </entry>
</feed>
"""

    items = parse_arxiv_atom(source, atom)

    assert len(items) == 1
    item = items[0]
    assert item.title == "Agentic Coding Systems for Software Delivery"
    assert item.url == "http://arxiv.org/abs/2605.12345v1"
    assert item.canonical_url == "http://arxiv.org/abs/2605.12345v1"
    assert item.published_at == "2026-05-12T14:00:00+00:00"
    assert item.summary == "We study code agents that repair CI failures and create pull requests."
    assert item.tags == ["research", "ai-coding", "paper", "cs.SE", "cs.AI"]


def test_arxiv_query_collector_uses_injected_text_client() -> None:
    source = Source(
        name="arXiv AI Software Engineering",
        type="arxiv",
        priority="P0",
        url="https://export.arxiv.org/api/query?search_query=all:agentic%20coding",
        tags=["research"],
    )
    atom = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2605.00001v1</id>
    <published>2026-05-12T14:00:00Z</published>
    <title>Agentic Coding</title>
    <summary>Short summary.</summary>
  </entry>
</feed>
"""
    client = FakeTextClient(atom)

    items = collect_arxiv_query(source, client=client)

    assert client.calls == [source.url]
    assert [item.title for item in items] == ["Agentic Coding"]


def test_hn_rss_style_feed_becomes_community_candidates() -> None:
    source = Source(
        name="Hacker News AI Search",
        type="hn-feed",
        priority="P0",
        url="https://hnrss.org/newest?q=agentic+coding",
        tags=["community", "ai-coding"],
    )
    feed = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Show HN: Agent reviews CI failures</title>
      <link>https://news.ycombinator.com/item?id=123</link>
      <pubDate>Tue, 12 May 2026 16:20:00 GMT</pubDate>
      <description>123 points by builder | 45 comments | https://example.com/agent-ci</description>
    </item>
  </channel>
</rss>
"""

    items = parse_hn_feed(source, feed)

    assert len(items) == 1
    item = items[0]
    assert item.title == "Show HN: Agent reviews CI failures"
    assert item.url == "https://news.ycombinator.com/item?id=123"
    assert item.published_at == "2026-05-12T16:20:00+00:00"
    assert item.summary == "123 points by builder | 45 comments | https://example.com/agent-ci"
    assert item.score == 123
    assert item.tags == ["community", "ai-coding", "hn"]


def test_hn_feed_collector_uses_injected_text_client() -> None:
    source = Source(
        name="Hacker News AI Search",
        type="hn-feed",
        priority="P0",
        url="https://hnrss.org/newest?q=agentic+coding",
        tags=["community"],
    )
    feed = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Agent tools</title>
      <link>https://news.ycombinator.com/item?id=456</link>
      <description>5 points by builder</description>
    </item>
  </channel>
</rss>
"""
    client = FakeTextClient(feed)

    items = collect_hn_feed(source, client=client)

    assert client.calls == [source.url]
    assert [item.title for item in items] == ["Agent tools"]


def test_web_page_collector_extracts_engineering_article_links() -> None:
    source = Source(
        name="OpenAI Engineering",
        type="web",
        priority="P0",
        url="https://openai.com/news/engineering/",
        tags=["official", "engineering-practice", "software-delivery"],
    )
    html = """
    <html>
      <body>
        <nav><a href="/news/">News</a><a href="/careers/">Careers</a></nav>
        <main>
          <a href="/news/scaling-code-review/">
            Scaling code review with agentic coding systems Engineering May 12, 2026
          </a>
          <a href="https://platform.openai.com/docs">Developer docs</a>
          <a href="/news/reliability-for-agents/">
            Reliability lessons from production AI agents Engineering May 11, 2026
          </a>
        </main>
      </body>
    </html>
    """

    items = parse_web_page(source, html)

    assert [item.title for item in items] == [
        "Scaling code review with agentic coding systems",
        "Reliability lessons from production AI agents",
    ]
    assert items[0].url == "https://openai.com/news/scaling-code-review"
    assert items[0].published_at == "2026-05-12T00:00:00+00:00"
    assert items[0].tags == ["official", "engineering-practice", "software-delivery"]


def test_default_sources_cover_p0_official_and_ai_coding_sources() -> None:
    expected_names = {
        "OpenAI News",
        "OpenAI Engineering",
        "Anthropic News",
        "Anthropic Engineering",
        "Google DeepMind Blog",
        "Meta AI Blog",
        "Microsoft AI Blog",
        "NVIDIA AI Blog",
        "AWS Machine Learning Blog",
        "Hugging Face Blog",
        "GitHub Changelog",
        "GitHub Copilot Blog",
        "OpenAI Codex",
        "Anthropic Claude Code",
        "Cursor Blog",
        "Windsurf Blog",
        "Sourcegraph Blog",
        "JetBrains AI Blog",
        "GitLab AI Blog",
        "Harness Blog",
        "CodeRabbit Blog",
        "Cognition Devin Blog",
        "Factory Blog",
        "OpenHands Releases",
        "SWE-agent Releases",
        "Continue Releases",
        "Cline Releases",
        "Roo Code Releases",
        "SWE-bench Releases",
        "Terminal-Bench Releases",
        "arXiv AI Software Engineering",
        "Hacker News AI Search",
    }

    by_name = {source.name: source for source in DEFAULT_SOURCES}

    assert expected_names <= set(by_name)
    assert {by_name[name].priority for name in expected_names - {"arXiv AI Software Engineering"}} == {"P0"}
    assert by_name["arXiv AI Software Engineering"].priority == "P1"
    assert by_name["OpenAI News"].type == "rss"
    assert by_name["OpenAI Engineering"].type == "web"
    assert by_name["Anthropic Engineering"].type == "web"
    assert by_name["OpenHands Releases"].type == "github-releases"
    assert by_name["arXiv AI Software Engineering"].type == "arxiv"
    assert by_name["Hacker News AI Search"].type == "hn-feed"
    assert "software-delivery" in by_name["Harness Blog"].tags


def test_sources_example_yaml_matches_default_source_shape() -> None:
    path = Path(__file__).resolve().parents[1] / "sources.example.yaml"

    sources = load_sources(path)

    assert len(sources) >= len(DEFAULT_SOURCES)
    assert all(source.name and source.url for source in sources)
    assert {"rss", "github-releases", "github-search", "arxiv", "hn-feed"} <= {
        source.type for source in sources
    }
