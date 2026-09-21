from bot.paper_trader import PaperTrader

def test_buy_take_profit():
    trader = PaperTrader(10_000.0)
    trader.open("BUY", 100.0)
    trader.check_exit(high=104.0, low=99.5)

    assert trader.position is None
    assert len(trader.trades) == 1
    assert trader.trades[0].reason == "TAKE_PROFIT"
    assert trader.balance > trader.starting_balance

def test_buy_stop_loss():
    trader = PaperTrader(10_000.0)
    trader.open("BUY", 100.0)
    trader.check_exit(high=100.5, low=98.0)

    assert trader.position is None
    assert trader.trades[0].reason == "STOP_LOSS"
    assert trader.balance < trader.starting_balance

def test_does_not_open_second_position():
    trader = PaperTrader(10_000.0)
    trader.open("BUY", 100.0)
    first = trader.position.copy()
    trader.open("SELL", 110.0)

    assert trader.position == first
