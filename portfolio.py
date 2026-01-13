"""
Klasse: Portfolio

Autor: Bastian Pivarcsi

Datum: 13.01.2026

Beschreibung:
Diese Klasse repräsentiert ein Nutzer-Portfolio. Sie dient als Container für 
einzelne Assets und bietet Methoden zum Laden der Daten aus der Datenbank 
sowie zur Berechnung des Gesamtwerts aller enthaltenen Positionen.


Quellen: 
- Programmierung
    - Lehrbrief zur Vorlesung
    - https://docs.python.org/3/library/typing.html
"""

from typing import List
from portfolioasset import PortfolioAsset
from databaseHandler import DatabaseAdministration

class Portfolio:
    """
    Verwaltet eine Sammlung von PortfolioAsset-Objekten für eine bestimmte Portfolio-ID.
    """

    def __init__(self, portfolio_id: int, database_handler: DatabaseAdministration):
        """
        Initialisiert eine Instanz der Klasse Portfolio.

        :param portfolio_id: Die eindeutige ID des Portfolios aus der Datenbank
        :param database_handler: Instanz der Datenbankverwaltung für den Datenzugriff
        :return: -
        """
        self.id = portfolio_id
        self.handler = database_handler
        self.assets: List[PortfolioAsset] = []

    def load_assets(self):
        """
        Lädt alle zugehörigen Assets aus der Datenbank und instanziiert 
        entsprechende PortfolioAsset-Objekte.

        :param: -
        :return: -
        """
        # Abruf der Rohdaten über den DatabaseHandler
        raw_assets = self.handler.get_assets_for_portfolio(self.id)
        
        # Liste zurücksetzen, um Dopplungen beim Neuladen zu vermeiden
        self.assets = []
        
        # Umwandlung der Datenbankzeilen in Objekte
        for data in raw_assets:
            new_asset = PortfolioAsset(
                portfolio_id=data["portfolio_id"],
                asset_type=data["asset_type"],
                asset_symbol=data["asset_symbol"],
                asset_name=data["asset_name"],
                amount=data["amount"],
                buy_price=data["buy_price"],
                bought_at=data["bought_at"],
                asset_id=data["asset_id"]
            )
            self.assets.append(new_asset)

    def get_total_value(self) -> float:
        """
        Berechnet den kumulierten Gesamtwert aller im Portfolio befindlichen Assets.

        :param: -
        :return: total - Summe der Werte aller Assets als Gleitkommazahl
        """
        total = 0.0
        for asset in self.assets:
            total = total + asset.get_total_value()
        return total