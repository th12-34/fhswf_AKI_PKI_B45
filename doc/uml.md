```mermaid

classDiagram
    class FinancialAPI {
        - api_url: string
        + get_stock_data(ticker: string): Data
        + get_crypto_data(ticker: string): Data
    }
    
    class DataFetcher {
        - api: FinancialAPI
        + fetch_data(ticker: string): Data
    }
    
    class DataProcessor {
        - data: Data
        - cleaned_data: Data
        + clean_data(): Data
        + calculate_technical_indicators(): Data
        + prepare_for_visualization(): Data
    }
    
    class TechnicalIndicators {
        + moving_average(data: Data): float
        + rsi(data: Data): float
        + macd(data: Data): float
    }
    
    class PortfolioManager {
        + create_portfolio(user: User): Portfolio
        + add_stock_to_portfolio(portfolio: Portfolio, stock: Stock): Portfolio
        + calculate_portfolio_value(portfolio: Portfolio): float
    }
    
    class ForecastingModel {
        - model: ARIMA or Prophet
        + predict_future(ticker: string): float
    }

    class UserInterface {
        + plot_data(data: Data): None
        + render_dashboard(data: Data): None
        + render_forecast(forecast: float): None
        + display_sentiment(sentiment: float): None
    }
    
    class User {
        - username: string
        - portfolio: Portfolio
        + get_portfolio(): Portfolio
    }
    
    class Portfolio {
        - stocks: list
        + add_stock(stock: Stock): None
        + get_value(): float
    }

    class Stock {
        - ticker: string
        - quantity: float
        + get_current_price(): float
    }
    
    FinancialAPI <|-- DataFetcher
    DataFetcher <|-- DataProcessor
    DataProcessor <|-- TechnicalIndicators
    DataProcessor <|-- ForecastingModel
    DataProcessor <|-- UserInterface
    PortfolioManager <|-- User
    User <|-- Portfolio
    Portfolio <|-- Stock
    PortfolioManager <|-- Stock
    DataFetcher <|-- FinancialAPI

    ```
