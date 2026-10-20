"""Deterministic provider normalization; yf.download is always replaced locally."""
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from src import market_data
from src.prospective_validation_data import append_daily, completed_daily


def canonical_prices(tz=None):
    return pd.DataFrame(
        {
            "open": [100., 101., 102.],
            "high": [103., 104., 105.],
            "low": [98., 99., 100.],
            "close": [102., 103., 104.],
            "volume": [1000, 1200, 1400],
        },
        index=pd.DatetimeIndex(["2026-09-17", "2026-09-18", "2026-09-21"],
                               tz=tz, name="Date"),
    )


def mock_yahoo(monkeypatch, values, multiindex):
    provider = values.rename(columns=str.title)
    provider["Adj Close"] = provider.Close * .9
    provider = provider[["Close", "Adj Close", "High", "Low", "Open", "Volume"]]
    if multiindex:
        provider.columns = pd.MultiIndex.from_tuples(
            [(c, "TEST") for c in provider], names=["Price", "Ticker"])
    else:
        provider.columns.name = "Price"

    def download(ticker, **kwargs):
        assert ticker == "TEST"
        assert kwargs == dict(period="5y", interval="1d", auto_adjust=False,
                              prepost=False, progress=False)
        return provider.copy(deep=True)

    monkeypatch.setattr(market_data.yf, "download", download)
    return market_data.download_yahoo_data("TEST", period="5y", interval="1d")


@pytest.mark.parametrize("multiindex", [False, True])
@pytest.mark.parametrize("tz", [None, "America/New_York"])
def test_yahoo_normalization_removes_axis_metadata_without_changing_data(monkeypatch, multiindex, tz):
    expected = canonical_prices(tz)
    result = mock_yahoo(monkeypatch, expected, multiindex)
    assert result.columns.name is None
    assert list(result) == ["open", "high", "low", "close", "volume"]
    # Exact equality includes values, dtypes, index labels/name/timezone and axes.
    assert_frame_equal(result, expected, check_exact=True)


@pytest.mark.parametrize("multiindex", [False, True])
def test_canonical_provider_input_avoids_false_revision(monkeypatch, multiindex):
    previous = canonical_prices()
    metadata_only_difference = previous.rename_axis("Price", axis="columns")
    with pytest.raises(ValueError, match="Previously observed OHLCV revised") as error:
        append_daily(previous, metadata_only_difference, "2026-09-18")
    assert isinstance(error.value.__cause__, AssertionError)
    assert 'Attribute "names" are different' in str(error.value.__cause__)

    incoming = mock_yahoo(monkeypatch, previous, multiindex)
    completed = completed_daily(incoming, "2026-09-21T21:00:00Z")
    assert_frame_equal(append_daily(previous, completed, "2026-09-18"),
                       previous, check_exact=True)


@pytest.mark.parametrize("column", ["open", "high", "low", "close", "volume"])
@pytest.mark.parametrize("offset", [0, 2], ids=["seed-overlap", "observed-validation"])
def test_real_value_revision_still_fails_after_provider_normalization(monkeypatch, column, offset):
    previous = canonical_prices()
    revised = previous.copy()
    revised.iloc[offset, revised.columns.get_loc(column)] += 1 if column == "volume" else .25
    incoming = mock_yahoo(monkeypatch, revised, multiindex=True)
    assert incoming.columns.name is None
    with pytest.raises(ValueError, match="Previously observed OHLCV revised") as error:
        append_daily(previous, incoming, "2026-09-18")
    assert isinstance(error.value.__cause__, AssertionError)
    assert "values are different" in str(error.value.__cause__)
