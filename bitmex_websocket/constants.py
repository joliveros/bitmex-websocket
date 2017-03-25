CHANNELS = [
    'chat',          # Trollbox chat
    'connected',     # Statistics of connected users/bots
    'insurance',     # Daily Insurance Fund updates
    'publicNotifications',  # System-wide notifications
    'liquidation',   # Liquidation orders as they're entered into the book
]

INSTRUMENT_CHANNELS = [
    'instrument',    # Instrument updates including turnover and bid/ask
    'orderBookL2',   # Full level 2 orderBook
    'orderBook10',   # Top 10 levels using traditional full book push
    'quote',         # Top level of the book
    'quoteBin1m',    # 1-minute quote bins
    'settlement',    # Settlements
    'trade',         # Live trades
    'tradeBin1m',    # 1-minute ticker bins
]

SECURE_CHANNELS = [
    'affiliate',   # Affiliate status, such as total referred users & payout %
    'margin',      # Updates on your current account balance and margin requirements
    'privateNotifications',  # Individual notifications - currently not used
    'wallet',       # Bitcoin address balance data, including total deposits & withdrawals
    'transact',     # Deposit/Withdrawal updates
]

SECURE_INSTRUMENT_CHANNELS = [
    'execution',   # Individual executions; can be multiple per order
    'order',       # Live updates on your orders
    'position',    # Updates on your positions
]

# Don't grow a table larger than this amount. Helps cap memory usage.
MAX_TABLE_LEN = 200

# Actions that might be received for each table
ACTIONS = ('partial', 'insert', 'update', 'delete')
