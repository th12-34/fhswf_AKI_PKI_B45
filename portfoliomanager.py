from databaseHandler import DatabaseAdministration
from portfolioasset import PortfolioAsset
from portfolio import Portfolio

class PortfolioManager():
    def __init__(self,userName):
        self.handler = DatabaseAdministration()
        self.userName = userName
        self.portfolioIds = self.handler.get_portfolio_ids(self.userName)
        self.currentPortfolio = None

    def createPortfolio(self, portfolioName : str = ""):
        id = self.handler.create_portfolio(self.userName, portfolioName)
        self.portfolioIds.append(id)
        self.selectPortfolioId(id) # select last added portfolio as current  to manage

    def deletePortfolio(self, portfolioId : int):
        success = self.handler.delete_portfolio(self.userName,portfolioId)
        if not success:
            print("couldnt delete portfolio")

    def selectPortfolioId(self, id :int):
        if id in self.portfolioIds:
            self.currentPortfolio = Portfolio(id, self.handler)
            self.currentPortfolio.load_assets()
        else:
            print("portfolio id doesnt exist")

    def getPortfolios(self):
        """Returns a list of tuples [(id, name), ...] for the user."""
        return self.handler.get_portfolios_for_user(self.userName)

    def addAssetToPortfolio(self, asset : PortfolioAsset):
        if self.currentPortfolio:
            self.handler.add_asset(self.currentPortfolio.id,
                                asset.type,
                                asset.symbol,
                                asset.name,
                                asset.amount,
                                asset.buy_price,
                                asset.bought_at,
                                asset.currency)
            self.currentPortfolio.load_assets()
        else:
            print("Cant add as no valid portfolio added")

    def deleteAsset(self, asset_id: int):
        """
        Deletes a specific asset from the database and 
        refreshes the current portfolio's asset list.
        """
        if self.currentPortfolio:
            success = self.handler.delete_asset(asset_id)
            
            if success:
                self.currentPortfolio.load_assets()
                return True
            else:
                print(f"Failed to delete asset {asset_id} from database")
                return False
        else:
            print("No portfolio selected. Cannot delete asset.")
            return False
        
        
    
    

