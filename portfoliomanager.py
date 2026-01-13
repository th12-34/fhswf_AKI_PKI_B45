"""
Programmname: PortfolioManager

Autor: Bastian Pivarcsi

Datum: 13.01.2026

Beschreibung:
Diese Klasse dient als zentrale Steuerungseinheit für die Portfolio-Verwaltung 
eines Nutzers. Sie ermöglicht das Erstellen, Löschen und Auswählen von Portfolios 
sowie das Management von Assets innerhalb des aktuell ausgewählten Portfolios.


Quellen: 
- Programmierung
    - Lehrbrief zur Vorlesung
"""

from databaseHandler import DatabaseAdministration
from portfolioasset import PortfolioAsset
from portfolio import Portfolio

class PortfolioManager():
    """
    Verwaltet die Interaktion zwischen dem Nutzer, seinen Portfolios und der Datenbank.
    """

    def __init__(self, userName):
        """
        Initialisiert den PortfolioManager für einen spezifischen Nutzer.

        :param userName: Der Name des aktuell angemeldeten Nutzers
        :return: -
        """
        self.handler = DatabaseAdministration()
        self.userName = userName
        self.portfolioIds = self.handler.get_portfolio_ids(self.userName)
        self.currentPortfolio = None

    def createPortfolio(self, portfolioName: str = ""):
        """
        Erstellt ein neues Portfolio in der Datenbank und setzt es als aktuell ausgewählt.

        :param portfolioName: Name des neuen Portfolios
        :return: -
        """
        id = self.handler.create_portfolio(self.userName, portfolioName)
        self.portfolioIds.append(id)
        # Das neu erstellte Portfolio direkt zur Bearbeitung auswählen
        self.selectPortfolioId(id)

    def deletePortfolio(self, portfolioId: int) -> bool:
        """
        Löscht ein Portfolio des Nutzers aus der Datenbank.

        :param portfolioId: Die ID des zu löschenden Portfolios
        :return: True bei Erfolg, sonst False
        """
        success = self.handler.delete_portfolio(self.userName, portfolioId)
        if not success:
            print(f"Portfolio {portfolioId} konnte nicht gelöscht werden.")
        return success

    def selectPortfolioId(self, id: int):
        """
        Wählt ein Portfolio anhand seiner ID aus und lädt die enthaltenen Assets.

        :param id: Die ID des auszuwählenden Portfolios
        :return: -
        """
        if id in self.portfolioIds:
            self.currentPortfolio = Portfolio(id, self.handler)
            self.currentPortfolio.load_assets()
        else:
            print("Portfolio-ID existiert nicht.")

    def getPortfolios(self):
        """
        Gibt eine Liste aller Portfolios des Nutzers zurück.

        :param: -
        :return: Liste von Tupeln [(id, name), ...]
        """
        return self.handler.get_portfolios_for_user(self.userName)

    def addAssetToPortfolio(self, asset: PortfolioAsset):
        """
        Fügt dem aktuell ausgewählten Portfolio ein neues Asset hinzu.

        :param asset: Ein Objekt der Klasse PortfolioAsset
        :return: -
        """
        if self.currentPortfolio:
            self.handler.add_asset(self.currentPortfolio.id,
                                   asset.type,
                                   asset.symbol,
                                   asset.name,
                                   asset.amount,
                                   asset.buy_price,
                                   asset.bought_at,
                                   asset.currency)
            # Ansicht nach dem Hinzufügen aktualisieren
            self.currentPortfolio.load_assets()
        else:
            print("Hinzufügen nicht möglich: Kein gültiges Portfolio ausgewählt.")

    def deleteAsset(self, asset_id: int):
        """
        Löscht ein spezifisches Asset aus der Datenbank und aktualisiert die Asset-Liste.

        :param asset_id: Die ID des zu löschenden Assets
        :return: True bei Erfolg, sonst False
        """
        if self.currentPortfolio:
            success = self.handler.delete_asset(asset_id)
            
            if success:
                self.currentPortfolio.load_assets()
                return True
            else:
                print(f"Fehler beim Löschen von Asset {asset_id} in der Datenbank.")
                return False
        else:
            print("Kein Portfolio ausgewählt. Asset kann nicht gelöscht werden.")
            return False