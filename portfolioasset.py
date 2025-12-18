from typing import Optional

class PortfolioAsset:
    def __init__(
        self,
        portfolio_id: int,
        asset_type: str,
        asset_symbol: str,
        asset_name: Optional[str],
        amount: float,
        buy_price: float,          
        bought_at: str,
        currency: str = "EUR"
    ):
        self.portfolio_id = portfolio_id
        self.type = asset_type
        self.symbol = asset_symbol
        self.name = asset_name
        self.amount = amount
        self.buy_price = buy_price
        self.bought_at = bought_at
        self.currency = currency

    def get_total_value(self) -> float:
        return self.amount * self.buy_price