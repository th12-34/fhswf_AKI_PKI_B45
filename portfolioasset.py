"""
Programmname: PortfolioAsset

Autor: Bastian Pivarcsi

Datum: 13.01.2026

Beschreibung:
Diese Klasse repräsentiert ein einzelnes Asset (z. B. eine Aktie oder eine 
Kryptowährung) innerhalb eines Portfolios. Sie speichert alle relevanten 
Kaufdaten und bietet Funktionen zur Berechnung des Positionswerts.


Quellen: 
- Programmierung
    - Lehrbrief zur Vorlesung
    - https://docs.python.org/3/tutorial/classes.html
"""

class PortfolioAsset:
    """
    Repräsentiert eine einzelne Anlageposition mit allen kaufrelevanten Informationen.
    """

    def __init__(
        self,
        portfolio_id: int,
        asset_type: str,
        asset_symbol: str,
        asset_name: str | None,
        amount: float,
        buy_price: float,          
        bought_at: str,
        currency: str = "EUR"
    ):
        """
        Initialisiert ein PortfolioAsset-Objekt.

        :param portfolio_id: ID des zugehörigen Portfolios
        :param asset_type: Typ der Anlage (z.B. 'stock' oder 'crypto')
        :param asset_symbol: Offizielles Kürzel (z.B. 'AAPL' oder 'BTC')
        :param asset_name: Name der Anlage oder None
        :param amount: Menge der Anteile
        :param buy_price: Kaufpreis pro Einheit
        :param bought_at: Datum/Zeitpunkt des Kaufs
        :param currency: Währung des Kaufs (Standard: 'EUR')
        :return: -
        """
        self.portfolio_id = portfolio_id
        self.type = asset_type
        self.symbol = asset_symbol
        self.name = asset_name
        self.amount = amount
        self.buy_price = buy_price
        self.bought_at = bought_at
        self.currency = currency

    def get_total_value(self) -> float:
        """
        Berechnet den Gesamtwert dieser Position basierend auf dem Kaufpreis.

        :param: -
        :return: Produkt aus Menge und Kaufpreis als Gleitkommazahl
        """
        return self.amount * self.buy_price