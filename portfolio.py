from typing import List
from portfolioasset import PortfolioAsset
from databaseHandler import DatabaseAdministration

class Portfolio:
    def __init__(self, portfolio_id: int, database_handler: DatabaseAdministration):
        self.id = portfolio_id
        self.handler = database_handler
        self.assets: List[PortfolioAsset] = []

    def load_assets(self):

        raw_assets = self.handler.get_assets_for_portfolio(self.id)
        
        self.assets = []
        
        for data in raw_assets:
            new_asset = PortfolioAsset(
                portfolio_id=data["portfolio_id"],
                asset_type=data["asset_type"],
                asset_symbol=data["asset_symbol"],
                asset_name=data["asset_name"],
                amount=data["amount"],
                buy_price=data["buy_price"],
                bought_at=data["bought_at"]
            )
            self.assets.append(new_asset)

    def get_total_value(self) -> float:
        total = 0.0
        for asset in self.assets:
            total = total + asset.get_total_value()
        return total