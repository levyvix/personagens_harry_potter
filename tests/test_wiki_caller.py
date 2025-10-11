"""Tests for WikiCaller classes."""

from unittest.mock import Mock, patch

import pytest
from bs4 import BeautifulSoup
from selectolax.lexbor import LexborHTMLParser as HTMLParser

from src.scrapers import WikiCallerAsync, WikiCallerMultiprocessing, WikiCallerSync


class TestWikiCallerSync:
    """Tests for synchronous WikiCaller."""

    def test_init(self):
        """Test WikiCaller initialization."""
        wiki = WikiCallerSync()
        assert wiki.url_personagem_base == "https://harrypotter.fandom.com"
        assert len(wiki.url_livros) == 7
        assert wiki.href_personagens == []
        assert wiki.cache == {}

    def test_have_banner_with_banner(self, sample_html_with_banner):
        """Test have_banner returns True when banner exists."""
        wiki = WikiCallerSync()
        soup = BeautifulSoup(sample_html_with_banner, "html.parser")
        assert wiki.have_banner(soup) is True

    def test_have_banner_without_banner(self, sample_html_without_banner):
        """Test have_banner returns False when banner doesn't exist."""
        wiki = WikiCallerSync()
        soup = BeautifulSoup(sample_html_without_banner, "html.parser")
        assert wiki.have_banner(soup) is False

    def test_have_informacoes_bibliograficas(self, sample_html_with_bio_info):
        """Test biographical information detection."""
        wiki = WikiCallerSync()
        soup = BeautifulSoup(sample_html_with_bio_info, "html.parser")
        assert wiki.have_informacoes_bibliograficas(soup) is True

    def test_have_informacoes_bibliograficas_false(
        self, sample_html_without_banner
    ):
        """Test biographical information returns False when absent."""
        wiki = WikiCallerSync()
        soup = BeautifulSoup(sample_html_without_banner, "html.parser")
        assert wiki.have_informacoes_bibliograficas(soup) is False

    @patch("src.scrapers.wiki_caller_sync.requests.get")
    def test_verify_href_with_banner(
        self, mock_get, sample_html_with_banner
    ):
        """Test verify_href returns href when character has banner."""
        wiki = WikiCallerSync()
        mock_response = Mock()
        mock_response.text = sample_html_with_banner
        mock_get.return_value = mock_response

        result = wiki.verify_href("https://example.com/harry")
        assert result == "https://example.com/harry"

    @patch("src.scrapers.wiki_caller_sync.requests.get")
    def test_verify_href_without_info(
        self, mock_get, sample_html_without_banner
    ):
        """Test verify_href returns None when character has no info."""
        wiki = WikiCallerSync()
        mock_response = Mock()
        mock_response.text = sample_html_without_banner
        mock_get.return_value = mock_response

        result = wiki.verify_href("https://example.com/spell")
        assert result is None


class TestWikiCallerMultiprocessing:
    """Tests for multiprocessing WikiCaller."""

    def test_init(self):
        """Test WikiCaller initialization."""
        wiki = WikiCallerMultiprocessing()
        assert wiki.url_personagem_base == "https://harrypotter.fandom.com"
        assert len(wiki.url_livros) == 7
        assert wiki.href_personagens == []
        assert wiki.cache == {}
        assert wiki.verified_characters == []

    def test_remove_accents(self):
        """Test accent removal functionality."""
        wiki = WikiCallerMultiprocessing()
        assert wiki.remove_accents("Nascimento") == "Nascimento"
        assert wiki.remove_accents("Espécie") == "Especie"
        assert wiki.remove_accents("Gênero") == "Genero"
        assert wiki.remove_accents("Informações") == "Informacoes"

    def test_have_banner_with_banner(self, sample_html_with_banner):
        """Test have_banner returns True when banner exists."""
        wiki = WikiCallerMultiprocessing()
        mock_response = Mock()
        mock_response.text = sample_html_with_banner
        assert wiki.have_banner(mock_response) is True

    def test_have_banner_without_banner(self, sample_html_without_banner):
        """Test have_banner returns False when banner doesn't exist."""
        wiki = WikiCallerMultiprocessing()
        mock_response = Mock()
        mock_response.text = sample_html_without_banner
        assert wiki.have_banner(mock_response) is False

    def test_have_informacoes_bibliograficas(self, sample_html_with_bio_info):
        """Test biographical information detection."""
        wiki = WikiCallerMultiprocessing()
        mock_response = Mock()
        mock_response.text = sample_html_with_bio_info
        assert wiki.have_informacoes_bibliograficas(mock_response) is True

    def test_verify_href_with_banner(self, sample_html_with_banner):
        """Test verify_href returns href when character has banner."""
        wiki = WikiCallerMultiprocessing()
        wiki.session = Mock()
        mock_response = Mock()
        mock_response.text = sample_html_with_banner
        wiki.session.get.return_value = mock_response

        result = wiki.verify_href("https://example.com/harry")
        assert result == "https://example.com/harry"
        assert "https://example.com/harry" in wiki.cache

    def test_verify_href_without_info(self, sample_html_without_banner):
        """Test verify_href returns None when character has no info."""
        wiki = WikiCallerMultiprocessing()
        wiki.session = Mock()
        mock_response = Mock()
        mock_response.text = sample_html_without_banner
        wiki.session.get.return_value = mock_response

        result = wiki.verify_href("https://example.com/spell")
        assert result is None


class TestWikiCallerAsync:
    """Tests for async WikiCaller."""

    def test_init(self):
        """Test WikiCaller initialization."""
        wiki = WikiCallerAsync()
        assert wiki.url_personagem_base == "https://harrypotter.fandom.com"
        assert len(wiki.url_livros) == 7
        assert wiki.verified_characters == []
        assert wiki.cache == {}

    def test_remove_accents(self):
        """Test accent removal functionality."""
        wiki = WikiCallerAsync()
        assert wiki.remove_accents("Nascimento") == "Nascimento"
        assert wiki.remove_accents("Espécie") == "Especie"
        assert wiki.remove_accents("Gênero") == "Genero"

    def test_have_banner_with_banner(self, sample_html_with_banner):
        """Test have_banner returns True when banner exists."""
        wiki = WikiCallerAsync()
        soup = HTMLParser(sample_html_with_banner)
        assert wiki.have_banner(soup) is True

    def test_have_banner_without_banner(self, sample_html_without_banner):
        """Test have_banner returns False when banner doesn't exist."""
        wiki = WikiCallerAsync()
        soup = HTMLParser(sample_html_without_banner)
        assert wiki.have_banner(soup) is False

    def test_have_informacoes_bibliograficas(self, sample_html_with_bio_info):
        """Test biographical information detection."""
        wiki = WikiCallerAsync()
        soup = HTMLParser(sample_html_with_bio_info)
        assert wiki.have_informacoes_bibliograficas(soup) is True

    def test_have_informacoes_bibliograficas_false(
        self, sample_html_without_banner
    ):
        """Test biographical information returns False when absent."""
        wiki = WikiCallerAsync()
        soup = HTMLParser(sample_html_without_banner)
        assert wiki.have_informacoes_bibliograficas(soup) is False

    @pytest.mark.asyncio
    async def test_fetch_with_cache(self):
        """Test fetch returns cached content when available."""
        wiki = WikiCallerAsync()
        wiki.cache["https://example.com"] = "cached content"

        mock_session = Mock()
        result = await wiki.fetch(mock_session, "https://example.com")

        assert result == "cached content"
        mock_session.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_verify_href_with_banner(self, sample_html_with_banner):
        """Test verify_href returns href when character has banner."""
        wiki = WikiCallerAsync()
        wiki.cache["https://example.com/harry"] = sample_html_with_banner

        mock_session = Mock()
        result = await wiki.verify_href(
            mock_session, "https://example.com/harry"
        )

        assert result == "https://example.com/harry"

    @pytest.mark.asyncio
    async def test_verify_href_without_info(self, sample_html_without_banner):
        """Test verify_href returns None when character has no info."""
        wiki = WikiCallerAsync()
        wiki.cache["https://example.com/spell"] = sample_html_without_banner

        mock_session = Mock()
        result = await wiki.verify_href(
            mock_session, "https://example.com/spell"
        )

        assert result is None


class TestRemoveAccents:
    """Test accent removal across all implementations."""

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("café", "cafe"),
            ("São Paulo", "Sao Paulo"),
            ("Informações", "Informacoes"),
            ("Espécie", "Especie"),
            ("Gênero", "Genero"),
            ("José", "Jose"),
            ("açúcar", "acucar"),
        ],
    )
    def test_remove_accents_multiprocessing(self, text, expected):
        """Test accent removal with various inputs."""
        wiki = WikiCallerMultiprocessing()
        assert wiki.remove_accents(text) == expected

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("café", "cafe"),
            ("São Paulo", "Sao Paulo"),
            ("Informações", "Informacoes"),
        ],
    )
    def test_remove_accents_async(self, text, expected):
        """Test accent removal in async implementation."""
        wiki = WikiCallerAsync()
        assert wiki.remove_accents(text) == expected
