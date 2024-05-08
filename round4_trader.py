import json
from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
from typing import Any, List, Dict
import collections
import jsonpickle

class Logger:
    def __init__(self) -> None:
        self.logs = ""

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders: dict[Symbol, list[Order]], conversions: int, trader_data: str) -> None:
        print(json.dumps([
            self.compress_state(state),
            self.compress_orders(orders),
            conversions,
            trader_data,
            self.logs,
        ], cls=ProsperityEncoder, separators=(",", ":")))

        self.logs = ""

    def compress_state(self, state: TradingState) -> list[Any]:
        return [
            state.timestamp,
            state.traderData,
            self.compress_listings(state.listings),
            self.compress_order_depths(state.order_depths),
            self.compress_trades(state.own_trades),
            self.compress_trades(state.market_trades),
            state.position,
            self.compress_observations(state.observations),
        ]

    def compress_listings(self, listings: dict[Symbol, Listing]) -> list[list[Any]]:
        compressed = []
        for listing in listings.values():
            compressed.append([listing["symbol"], listing["product"], listing["denomination"]])

        return compressed

    def compress_order_depths(self, order_depths: dict[Symbol, OrderDepth]) -> dict[Symbol, list[Any]]:
        compressed = {}
        for symbol, order_depth in order_depths.items():
            compressed[symbol] = [order_depth.buy_orders, order_depth.sell_orders]

        return compressed

    def compress_trades(self, trades: dict[Symbol, list[Trade]]) -> list[list[Any]]:
        compressed = []
        for arr in trades.values():
            for trade in arr:
                compressed.append([
                    trade.symbol,
                    trade.price,
                    trade.quantity,
                    trade.buyer,
                    trade.seller,
                    trade.timestamp,
                ])

        return compressed

    def compress_observations(self, observations: Observation) -> list[Any]:
        conversion_observations = {}
        for product, observation in observations.conversionObservations.items():
            conversion_observations[product] = [
                observation.bidPrice,
                observation.askPrice,
                observation.transportFees,
                observation.exportTariff,
                observation.importTariff,
                observation.sunlight,
                observation.humidity,
            ]

        return [observations.plainValueObservations, conversion_observations]

    def compress_orders(self, orders: dict[Symbol, list[Order]]) -> list[list[Any]]:
        compressed = []
        for arr in orders.values():
            for order in arr:
                compressed.append([order.symbol, order.price, order.quantity])

        return compressed

logger = Logger()

POSITION_LIMIT = {
    'AMETHYSTS' : 20, 
    'STARFRUIT' : 20, 
    'ORCHIDS' : 100, 
    'GIFT_BASKET' : 60, 
    'STRAWBERRIES' : 350, 
    'CHOCOLATE' : 250, 
    'ROSES' : 60, 
    # 'BAGUETTE': 150, 
    # 'UKULELE' : 70, 
    # 'PICNIC_BASKET' : 70
}

class Position:
    def __init__(self):
        for product in POSITION_LIMIT:
            setattr(self, product, 0)
    
    def __getitem__(self, product):
        return getattr(self, product)
    
    def __setitem__(self, product, value):
        setattr(self, product, value)

    def set(self, product_dict: Dict[str, int]):
        for product, value in product_dict.items():
            setattr(self, product, value)

    def get(self, product):
        return getattr(self, product)

    def __str__(self):
        return str({product: getattr(self, product) for product in POSITION_LIMIT})
    
    def __repr__(self):
        return str({product: getattr(self, product) for product in POSITION_LIMIT})

def calc_mid_price(order_depth: OrderDepth) -> float:
    best_ask = min(order_depth.sell_orders)
    best_bid = max(order_depth.buy_orders)
    return (best_ask + best_bid) / 2

class Trader:    
    def compute_orders_simple(
        self,
        product: str,
        order_depth: OrderDepth,
        acceptable_price: int = 10000,
        tol: int = 1,
    ) -> List[Order]:
        current_position_buy = self.position.get(product)
        current_position_sell = self.position.get(product)
        orders = []

        ########## Market take! ##########
        best_ask = min(order_depth.sell_orders)
        best_ask_vol = order_depth.sell_orders[best_ask] # This is negative!
        best_bid = max(order_depth.buy_orders)
        best_bid_vol = order_depth.buy_orders[best_bid] # This is positive!

        if best_ask <= acceptable_price:
            for ask, ask_vol in order_depth.sell_orders.items():
                ##### Is market below best price... #####
                if ask < acceptable_price or (ask == acceptable_price and current_position_buy <= 0):
                    ##### YES! Let's buy! #####
                    volume = min(-ask_vol, POSITION_LIMIT[product]-current_position_buy)
                    orders.append(
                        Order(
                            product, 
                            ask, 
                            volume
                        )
                    )
                    current_position_buy += volume
        elif best_bid >= acceptable_price:
            for bid, bid_vol in order_depth.buy_orders.items():
                ##### Is market above best price... #####
                if bid > acceptable_price or (bid == acceptable_price and current_position_sell >= 0):
                    ##### YES! Let's sell! #####
                    volume = min(bid_vol, POSITION_LIMIT[product]+current_position_sell)
                    orders.append(
                        Order(
                            product, 
                            bid, 
                            -volume
                        )
                    )
                    current_position_sell -= volume

        ########## Market make! ##########
        ##### Ask orders (me selling) #####
        if current_position_sell > -POSITION_LIMIT[product]: 
            mm_best_ask = max(acceptable_price+tol, best_ask-1)
            volume = max(-40, -POSITION_LIMIT[product] - current_position_sell)
            orders.append(
                Order(
                    product,
                    mm_best_ask,
                    volume # This must be negative because we are selling
                )
            )

        ##### Bid orders (me buying) #####
        if current_position_buy < POSITION_LIMIT[product]:
            mm_best_bid = min(acceptable_price-tol, best_ask+1)
            volume = min(40, POSITION_LIMIT[product] - current_position_buy)
            orders.append(
                Order(
                    product,
                    mm_best_bid,
                    volume # This must be positive because we are buying
                )
            )

        return orders
    

    def calc_acceptable_price_starfruit(
        self, 
        price_history: list[float],
    ) -> int:
        n=len(price_history)
        if n < 10:
            return int(round(sum(price_history) / n))
        
        # Calculate the average price of the last 6 prices
        avg6 = sum(price_history[-6:]) / 6

        # Calculate the average price of the last n prices
        avg = sum(price_history) / n

        return int(round(0.5 * avg + 0.5 * avg6))
    

    def calc_acceptable_price_gift_basket(
        self,
        chocolate_orders: int,
        strawberry_orders: int,
        roses_orders: int,
    ) -> int:
        chocolate_price = calc_mid_price(chocolate_orders)
        roses_price = calc_mid_price(roses_orders)
        strawberry_price = calc_mid_price(strawberry_orders)
        
        return int(4*chocolate_price + roses_price + 6*strawberry_price + 379)
    

    def run(self, state: TradingState) -> tuple[dict[Symbol, list[Order]], int, str]:
        self.position = Position()
        self.position.set(state.position)
        result = {}
        if state.timestamp == 0:
            traderData = {"STARFRUIT_PRICES": []}
        else:
            traderData = jsonpickle.decode(state.traderData)

        amethyst_orders = self.compute_orders_simple(
            product="AMETHYSTS",
            order_depth=state.order_depths["AMETHYSTS"],
            acceptable_price=10000,
            tol=4,
        )
        if len(amethyst_orders) > 0:
            result["AMETHYSTS"] = amethyst_orders

        if state.timestamp > 0: 
            starfruit_orders = self.compute_orders_simple(
                product="STARFRUIT",
                order_depth=state.order_depths["STARFRUIT"],
                acceptable_price=self.calc_acceptable_price_starfruit(
                    traderData["STARFRUIT_PRICES"]
                ),
                tol=3,
            )
            if len(starfruit_orders) > 0:
                result["STARFRUIT"] = starfruit_orders

            gift_basket_orders = self.compute_orders_simple(
                product="GIFT_BASKET",
                order_depth=state.order_depths["GIFT_BASKET"],
                acceptable_price=self.calc_acceptable_price_gift_basket(
                    state.order_depths["CHOCOLATE"],
                    state.order_depths["STRAWBERRIES"],
                    state.order_depths["ROSES"],
                ),
                tol=6,
            )
            if len(gift_basket_orders) > 0:
                result["GIFT_BASKET"] = gift_basket_orders

            
        
        # String value holding Trader state data required. 
        # It will be delivered as TradingState.traderData on next execution.
        starfruit_best_ask = min(state.order_depths["STARFRUIT"].sell_orders)
        starfruit_best_bid = max(state.order_depths["STARFRUIT"].buy_orders)
        starfruit_price = (starfruit_best_ask + starfruit_best_bid) / 2
        if state.timestamp > 2000:
            traderData["STARFRUIT_PRICES"].pop(0)
        traderData["STARFRUIT_PRICES"].append(starfruit_price)
        traderData = jsonpickle.encode(traderData)
        
        # Sample conversion request. Check more details below. 
        conversions = 1

        logger.flush(state, result, conversions, traderData)
        return result, conversions, traderData