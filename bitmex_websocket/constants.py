from enum import Enum, auto


class NoValue(Enum):
    def __repr__(self):
        return '<%s.%s>' % (self.__class__.__name__, self.name)

class BaseChannels(NoValue):
    pass

class Channels(BaseChannels):
    # Trollbox chat
    chat = auto()

    # Statistics of connected users/bots
    connected = auto()

    # Daily Insurance Fund updates
    insurance = auto()

    # Liquidation orders as they're entered into the book
    liquidation = auto()

    # System-wide notifications
    publicNotifications = auto()


class SecureChannels(BaseChannels):
    # Affiliate status, such as total referred users & payout %
    affiliate = auto()

    # Updates on your current account balance and margin requirements
    margin = auto()

    # Individual notifications - currently not used
    privateNotifications = auto()

    # Bitcoin address balance data, including total deposits & withdrawals
    wallet = auto()

    # Deposit/Withdrawal updates
    transact = auto()


class InstrumentChannels(BaseChannels):
    # Instrument updates including turnover and bid/ask
    instrument = auto()

    # Top 10 levels using traditional full book push
    orderBook10 = auto()

    # Full level 2 orderBook
    orderBookL2 = auto()

    # Top level of the book
    quote = auto()

    # 1-minute quote bins
    quoteBin1m = auto()

    # Settlements
    settlement = auto()

    # Live trades
    trade = auto()

    # 1-minute ticker bins
    tradeBin1m = auto()


class SecureInstrumentChannels(BaseChannels):
    # Individual executions; can be multiple per order
    execution = auto()

    # Live updates on your orders
    order = auto()

    # Updates on your positions
    position = auto()


class Action(NoValue):
    partial = auto()

    insert = auto()

    update = auto()

    delete = auto()


# Don't grow a table larger than this amount. Helps cap memory usage.
MAX_TABLE_LEN = 200
