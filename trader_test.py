from datamodel import OrderDepth, Symbol, TradingState, Order
from typing import List
import jsonpickle


class Trader:
    PRODUCT_LIMIT = {
        'AMETHYSTS': 20,
        'STARFRUIT': 20,
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

        # Decode traderData
        decodedTraderData = jsonpickle.decode(
            state.traderData) if state.traderData else {}

        # Get listings and position
        listings = state.listings
        position = state.position

        # Orders to be placed on exchange matching engine
        orders = {}
        for productSymbol in state.order_depths:
            order_depth: OrderDepth = state.order_depths[productSymbol]

            # Initialize the list of Orders to be sent as an empty list
            productOrders: List[Order] = []

            # Get product from symbol
            product = listings[productSymbol]['product']

            # Get position for product
            productPosition = position.get(product, 0)

            # Calculate max buy and sell amounts
            maxBuyAmount = self.PRODUCT_LIMIT[productSymbol] - productPosition
            maxSellAmount = -self.PRODUCT_LIMIT[productSymbol] \
                - productPosition

            # Calculate EMA for periods 5 and 20
            midPrice = self._getMidPrice(order_depth)
            ema5, ema20 = decodedTraderData.get(product, [midPrice, midPrice])
            alpha5, alpha20 = 1 / (5 + 1), 1 / (20 + 1)
            ema5 = alpha5 * midPrice + (1 - alpha5) * ema5
            ema20 = alpha20 * midPrice + (1 - alpha20) * ema20
            decodedTraderData[product] = [ema5, ema20]

            # Use EMAs to form buy and sell signals
            if ema5 > ema20:
                # Buy signal
                if order_depth.sell_orders:
                    best_ask, best_ask_amount = list(
                        order_depth.sell_orders.items())[0]
                    print("BUY", str(maxBuyAmount) + "x", ema5)
                    productOrders.append(
                        Order(productSymbol, best_ask, maxBuyAmount))
            elif ema5 < ema20:
                # Sell signal
                if order_depth.buy_orders:
                    best_bid, best_bid_amount = list(
                        order_depth.buy_orders.items())[0]
                    print("SELL", str(maxSellAmount) + "x", ema5)
                    productOrders.append(
                        Order(productSymbol, best_bid, maxSellAmount))

            orders[productSymbol] = productOrders

            # String value holding Trader state data required.
            # It will be delivered as TradingState.traderData on next execution.
        traderData = jsonpickle.encode(decodedTraderData)

        # Sample conversion request. Check more details below.
        conversions = 0
        return orders, conversions, traderData
