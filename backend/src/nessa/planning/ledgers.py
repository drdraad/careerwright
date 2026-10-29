"""The separate ledgers of one route in one scenario (spec section 12, FIN-1 and TIME-1;
S5.5), in integer GBP minor units. Pure.

- **Direct spend:** what the transition costs: fees, instalments and extras, less confirmed
  non-repayable support, including contractual payments due after the horizon, which are
  kept with their dates (FIN1-02). Support paid straight to a provider is shown beside the fee
  it covers and is never also a receipt (FIN1-10).
- **Income difference:** the confirmed baseline against the route's take-home pay, month by
  month over the one common horizon. Lost or gained pay is counted once, here (FIN1-03).
- **Liquidity:** conservative prefunding. Each month's outflows are paid from the opening
  balance and receipts proven to arrive before them; later receipts open the next month
  (TIME1-05). A month-end balance never rescues a month whose lower bound fails.
- **Debt:** existing debt's balance, interest and repayment, apart from cash. New borrowing is
  never planned (spec section 10).
"""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

Minor = Annotated[int, Field(ge=0)]
BASIS_POINTS = 10_000


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DirectMonth(StrictModel):
    month: str
    payments_minor: Minor  # what the person pays this month
    paid_to_provider_minor: (
        Minor  # fees support covered at the provider: never paid, never received
    )
    support_minor: Minor  # confirmed support paid to the person, against direct cost


class Liability(StrictModel):
    """A contractual payment the route incurs beyond the comparison horizon, or with no month
    yet: in direct cost with its timing disclosed, outside the monthly cash ledger."""

    variant_id: str
    due: str | None  # its month or date; None: the variant's dates are not known
    amount_minor: Minor


class DirectLedger(StrictModel):
    months: list[DirectMonth]
    beyond_horizon: list[Liability]
    unscheduled: list[Liability]  # known payments of a variant whose months are unknown
    complete: bool  # every payment's amount is known
    total_minor: Minor | None  # None: some cost is unknown, never 0


class IncomeMonth(StrictModel):
    month: str
    baseline_minor: Minor | None  # None: no confirmed baseline
    route_minor: Minor
    difference_minor: int | None  # baseline less route: lost pay is positive


class IncomeLedger(StrictModel):
    baseline_label: str | None
    continuation_label: str
    months: list[IncomeMonth]
    complete: bool  # every month's route income is known
    difference_minor: int | None  # summed over the horizon; None: unresolved


class LiquidityMonth(StrictModel):
    month: str
    opening_minor: int
    early_receipts_minor: Minor  # proven to arrive before this month's outflows
    living_minor: Minor
    payments_minor: Minor
    debt_service_minor: Minor
    lower_bound_minor: int  # opening + early receipts - outflows: what must stay >= reserve
    later_receipts_minor: Minor
    closing_minor: int


class LiquidityLedger(StrictModel):
    reserve_minor: Minor
    months: list[LiquidityMonth]
    complete: bool  # every outflow and receipt is placed and known


class DebtMonth(StrictModel):
    month: str
    opening_minor: Minor | None
    interest_minor: Minor | None  # None: the balance or the rate is not known
    repayment_minor: Minor
    closing_minor: Minor | None


class DebtLedger(StrictModel):
    debt_id: str
    months: list[DebtMonth]


class Ledgers(StrictModel):
    direct: DirectLedger
    income: IncomeLedger
    liquidity: LiquidityLedger
    debts: list[DebtLedger]


def liquidity(
    months: list[str],
    *,
    opening_minor: int,
    reserve_minor: int,
    early: list[int],
    later: list[int],
    living: list[int],
    payments: list[int],
    debt_service: list[int],
    complete: bool,
) -> LiquidityLedger:
    rows = []
    balance = opening_minor
    for n, month in enumerate(months):
        outflows = living[n] + payments[n] + debt_service[n]
        lower = balance + early[n] - outflows
        closing = lower + later[n]
        rows.append(
            LiquidityMonth(
                month=month,
                opening_minor=balance,
                early_receipts_minor=early[n],
                living_minor=living[n],
                payments_minor=payments[n],
                debt_service_minor=debt_service[n],
                lower_bound_minor=lower,
                later_receipts_minor=later[n],
                closing_minor=closing,
            )
        )
        balance = closing
    return LiquidityLedger(reserve_minor=reserve_minor, months=rows, complete=complete)


def monthly_interest(balance_minor: int, annual_bps: int) -> int:
    """A month's interest on a balance, rounded half up to a whole minor unit: integers only."""
    return (2 * balance_minor * annual_bps + 12 * BASIS_POINTS) // (24 * BASIS_POINTS)


def debt(
    debt_id: str,
    months: list[str],
    *,
    balance_minor: int | None,
    annual_bps: int | None,
    repayment_minor: int,
) -> tuple[DebtLedger, list[int]]:
    """The debt's months, and the repayment each month: the stated amount until a known
    balance is cleared."""
    rows, paid = [], []
    balance = balance_minor
    for month in months:
        interest = None
        if balance is not None and annual_bps is not None:
            interest = monthly_interest(balance, annual_bps)
        repayment = repayment_minor
        closing = None
        if balance is not None and interest is not None:
            repayment = min(repayment_minor, balance + interest)
            closing = balance + interest - repayment
        rows.append(
            DebtMonth(
                month=month,
                opening_minor=balance,
                interest_minor=interest,
                repayment_minor=repayment,
                closing_minor=closing,
            )
        )
        paid.append(repayment)
        balance = closing
    return DebtLedger(debt_id=debt_id, months=rows), paid
