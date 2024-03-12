import json
from typing import Dict, List
from json import JSONEncoder
import jsonpickle
import dataclasses
Time = int
Symbol = str
Product = str
Position = int
UserId = str
ObservationValue = int


class Listing:

    def __init__(self, symbol: Symbol, product: Product, denomination: Product):
        self.symbol = symbol
        self.product = product
        self.denomination = denomination
        self.synthenic = None
        self.leverage = None
        self.store_box = []
        
                 
class ConversionObservation:

    def __init__(self, bidPrice: float, askPrice: float, transportFees: float, exportTariff: float, importTariff: float, sunlight: float, humidity: float):
        self.bidPrice = bidPrice
        self.askPrice = askPrice
        self.transportFees = transportFees
        self.exportTariff = exportTariff
        self.importTariff = importTariff
        self.sunlight = sunlight
        self.humidity = humidity
        

class Observation:

    def __init__(self, plainValueObservations: Dict[Product, ObservationValue], conversionObservations: Dict[Product, ConversionObservation]) -> None:
        self.plainValueObservations = plainValueObservations
        self.conversionObservations = conversionObservations
        
    def __str__(self) -> str:
        return "(plainValueObservations: " + jsonpickle.encode(self.plainValueObservations) + ", conversionObservations: " + jsonpickle.encode(self.conversionObservations) + ")"
     

class Order:

    def __init__(self, symbol: Symbol, price: int, quantity: int) -> None:
        self.symbol = symbol
        self.price = price
        self.quantity = quantity

    def __str__(self) -> str:
        return "(" + self.symbol + ", " + str(self.price) + ", " + str(self.quantity) + ")"

    def __repr__(self) -> str:
        return "(" + self.symbol + ", " + str(self.price) + ", " + str(self.quantity) + ")"
    

class OrderDepth:

    def __init__(self,buy_orders: Dict[int, int], sell_orders: Dict[int, int]):
        self.buy_orders: Dict[int, int] = buy_orders
        self.sell_orders: Dict[int, int] = sell_orders


class Trade:

    def __init__(self, symbol: Symbol, price: int, quantity: int, buyer: UserId=None, seller: UserId=None, timestamp: int=0) -> None:
        self.symbol = symbol
        self.price: int = price
        self.quantity: int = quantity
        self.buyer = buyer
        self.seller = seller
        self.timestamp = timestamp

    def __str__(self) -> str:
        return "(" + self.symbol + ", " + self.buyer + " << " + self.seller + ", " + str(self.price) + ", " + str(self.quantity) + ", " + str(self.timestamp) + ")"

    def __repr__(self) -> str:
        return "(" + self.symbol + ", " + self.buyer + " << " + self.seller + ", " + str(self.price) + ", " + str(self.quantity) + ", " + str(self.timestamp) + ")"


class TradingState(object):

    def __init__(self,
                 traderData: str,
                 timestamp: Time,
                 listings: Dict[Symbol, Listing],
                 order_depths: Dict[Symbol, OrderDepth],
                 own_trades: Dict[Symbol, List[Trade]],
                 market_trades: Dict[Symbol, List[Trade]],
                 position: Dict[Product, Position],
                 observations: Observation):
        self.traderData = traderData
        self.timestamp = timestamp
        self.listings = listings
        self.order_depths = order_depths
        self.own_trades = own_trades
        self.market_trades = market_trades
        self.position = position
        self.observations = observations
        
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)

    
class ProsperityEncoder(JSONEncoder):

        def default(self, o):
            return o.__dict__
        
from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string
class Trader:
    PRODUCT_LIMIT = {
        'AMETHYSTS': 20,
        'STARFRUIT': 20
    }

    def _getMidPrice(self, order_depth: OrderDepth) -> float:
        priceSum = numPrices = 0
        for price in order_depth.buy_orders:
            priceSum += price
            numPrices += 1

        for price in order_depth.sell_orders:
            priceSum += price
            numPrices += 1

        return priceSum / numPrices

    def run(self, state: TradingState):
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """

        
        decodedTraderData = jsonpickle.decode(
            state.traderData) if state.traderData else {}

        
        listings = state.listings
        position = state.position

        
        orders = {}
        for productSymbol in state.order_depths:
            order_depth: OrderDepth = state.orxder_depths[productSymbol]

            
            productOrders: List[Order] = []

            
            product = listings[productSymbol]['product']

            
            productPosition = position.get(product, 0)

            
            maxBuyAmount = self.PRODUCT_LIMIT[productSymbol] - productPosition
            maxSellAmount = -self.PRODUCT_LIMIT[productSymbol] \
                - productPosition

            
            midPrice = self._getMidPrice(order_depth)
            ema25, ema50 = decodedTraderData.get(product, [midPrice, midPrice])
            alpha25, alpha50 = 1 / (25 + 1), 1 / (50 + 1)
            ema25 = alpha50 * midPrice + (1 - alpha25) * ema25
            ema50 = alpha50 * midPrice + (1 - alpha50) * ema50
            decodedTraderData[product] = [ema25, ema50]

            import sklearn
            
            datapoints = []
            model = sklearn.linear_model.LinearRegression()
            model.fit(datapoints)
            model.predict([ema25, ema50])
            
            if ema25 > ema50:
                
                if order_depth.sell_orders:
                    best_ask, best_ask_amount = list(
                        order_depth.sell_orders.items())[0]
                    print("BUY", str(maxBuyAmount) + "x", ema25)
                    productOrders.append(
                        Order(productSymbol, best_ask, maxBuyAmount))
            elif ema25 < ema50:
                
                if order_depth.buy_orders:
                    best_bid, best_bid_amount = list(
                        order_depth.buy_orders.items())[0]
                    print("SELL", str(maxSellAmount) + "x", ema25)
                    productOrders.append(
                        Order(productSymbol, best_bid, maxSellAmount))

            orders[productSymbol] = productOrders

            
            
        traderData = jsonpickle.encode(decodedTraderData)

        
        conversions = 0
        return orders, conversions, traderData
