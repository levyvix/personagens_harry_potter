"""Pytest configuration and fixtures for tests."""

import pytest


@pytest.fixture
def sample_character_data():
    """Sample character data for testing."""
    return {
        "Nome": "Harry Potter",
        "Nascimento": "31 de julho de 1980",
        "Especie": "Humano",
        "Genero": "Masculino",
    }


@pytest.fixture
def sample_html_with_banner():
    """HTML with a character that has a birth banner."""
    return """
    <html>
        <div class="pi-item pi-data pi-item-spacing pi-border-color">
            <h3 class="pi-data-label pi-secondary-font">Nascimento</h3>
            <div class="pi-data-value pi-font">31 de julho de 1980</div>
        </div>
        <h2 class="pi-item pi-item-spacing pi-title pi-secondary-background">
            Harry Potter
        </h2>
    </html>
    """


@pytest.fixture
def sample_html_with_bio_info():
    """HTML with a character that has biographical information."""
    return """
    <html>
        <h2 class="pi-item pi-header pi-secondary-font pi-item-spacing \
pi-secondary-background">
            <center>Informações biográficas</center>
        </h2>
        <h2 class="pi-item pi-item-spacing pi-title pi-secondary-background">
            Hermione Granger
        </h2>
    </html>
    """


@pytest.fixture
def sample_html_without_banner():
    """HTML without character information (e.g., a spell page)."""
    return """
    <html>
        <h2 class="pi-item pi-item-spacing pi-title pi-secondary-background">
            Expelliarmus
        </h2>
        <div class="pi-data-value pi-font">Desarmament Charm</div>
    </html>
    """


@pytest.fixture
def sample_book_page_html():
    """HTML from a book page with character links."""
    return """
    <html>
        <div class="mw-parser-output">
            <p>
                <a href="/pt-br/wiki/Harry_Potter">Harry Potter</a>
                <a href="/pt-br/wiki/Hermione_Granger">Hermione Granger</a>
                <a href="/pt-br/wiki/Ronald_Weasley">Ron Weasley</a>
            </p>
        </div>
    </html>
    """


@pytest.fixture
def sample_character_page_html():
    """HTML from a complete character page."""
    return """
    <html>
        <h2 class="pi-item pi-item-spacing pi-title pi-secondary-background">
            Harry Potter
        </h2>
        <div class="pi-item pi-data pi-item-spacing pi-border-color">
            <h3 class="pi-data-label pi-secondary-font">Nascimento</h3>
            <div class="pi-data-value pi-font">31 de julho de 1980</div>
        </div>
        <div class="pi-item pi-data pi-item-spacing pi-border-color">
            <h3 class="pi-data-label pi-secondary-font">Espécie</h3>
            <div class="pi-data-value pi-font">Humano</div>
        </div>
        <div class="pi-item pi-data pi-item-spacing pi-border-color">
            <h3 class="pi-data-label pi-secondary-font">Gênero</h3>
            <div class="pi-data-value pi-font">Masculino</div>
        </div>
    </html>
    """
