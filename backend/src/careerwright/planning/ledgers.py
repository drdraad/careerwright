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
- **A loan to repay** (Task 12c; spec section 22): a fee that a tuition fee loan the person
  stated pays straight to the provider is in neither the direct-spend nor the liquidity
  ledger, never support or a receipt; the route lists it apart (`LoanToRepay`), with its
  repayment unknown.

A month's figure that rests on an amount not known (a payment whose amount or month is not
stated, pay from an option with no dates) is null, never the known part shown as a known one
(Task 12a). The checker still tests its limits on the known part, which an unknown payment can
only make worse.
"""

from pydantic import BaseModel, ConfigDict

from careerwright.money import Minor, Money
from careerwright.planning.catalogue import FeeLoanKind

BASIS_POINTS = 10_000


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DirectMonth(StrictModel):
    """One month's direct spending; each figure is null when some payment's amount or month
    is not known."""

    month: str
    payments_minor: Minor | None  # what the person pays this month
    paid_to_provider_minor: (
        Minor | None  # fees support covered at the provider: never paid, never received
    )
    support_minor: Minor | None  # confirmed support paid to the person, against direct cost


class Liability(StrictModel):
    """A contractual payment the route incurs beyond the comparison horizon, or with no month
    yet: in direct cost with its timing disclosed, outside the monthly cash ledger."""

    variant_id: str
    due: str | None  # its month or date; None: the variant's dates are not known
    amount_minor: Minor


class LoanToRepay(StrictModel):
    """What a fee loan paid straight to the provider (a tuition fee loan or an Advanced Learner
    Loan) pays for a route (spec section 22): a loan the person repays later, never their
    payment, cash, support or a receipt. Facts only; the web words them (R11)."""

    variant_id: str
    # Which loan; the default reads a result stored before the Advanced Learner Loan joined.
    kind: FeeLoanKind = FeeLoanKind.TUITION_FEE_LOAN
    # The month the fee it pays falls due (beyond the horizon too); None: not known, because
    # the loan's amount or the fee's month is not.
    due: str | None
    amount: Money | None  # None: not known, never £0
    repayment: Money | None = None  # not modelled in L0: unknown, never 0
    conditional: bool  # it rests on the loan's approval, not yet confirmed


class DirectLedger(StrictModel):
    months: list[DirectMonth]
    beyond_horizon: list[Liability]
    unscheduled: list[Liability]  # known payments of a variant whose months are unknown
    # Due before the planning start: whether each was paid is not known, so the total is not.
    before_start: list[Liability]
    complete: bool  # every payment's amount is known
    total_minor: Minor | None  # None: some cost is unknown, never 0


class IncomeMonth(StrictModel):
    month: str
    baseline_minor: Minor | None  # None: no confirmed baseline
    route_minor: Minor | None  # None: pay from an option with no months could fall here
    difference_minor: int | None  # baseline less route: lost pay is positive


class IncomeLedger(StrictModel):
    baseline_label: str | None
    continuation_label: str
    months: list[IncomeMonth]
    complete: bool  # every month's route income is known
    difference_minor: int | None  # summed over the horizon; None: unresolved


class LiquidityMonth(StrictModel):
    """One month's cash. Living costs and repayments are always known; a figure resting on
    an unknown payment or receipt, or on an earlier month that does, is null."""

    month: str
    opening_minor: int | None
    early_receipts_minor: Minor | None  # proven to arrive before this month's outflows
    living_minor: Minor
    payments_minor: Minor | None
    debt_service_minor: Minor
    lower_bound_minor: int | None  # opening + early receipts - outflows: must stay >= reserve
    later_receipts_minor: Minor | None
    closing_minor: int | None


class LiquidityLedger(StrictModel):
    reserve_minor: Minor | None  # None: not known, so no month is checked against it
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


def balances(
    opening_minor: int, *, early: list[int], later: list[int], outflows: list[int]
) -> list[tuple[int, int, int]]:
    """Each month's opening balance, prefunded lower bound and closing balance (TIME1-05): the
    outflows are paid from the opening balance and the early receipts; later receipts open
    the next month."""
    found = []
    balance = opening_minor
    for n, out in enumerate(outflows):
        lower = balance + early[n] - out
        closing = lower + later[n]
        found.append((balance, lower, closing))
        balance = closing
    return found


def liquidity(
    months: list[str],
    bounds: list[tuple[int, int, int]],
    *,
    reserve_minor: int | None,
    early: list[int],
    later: list[int],
    living: list[int],
    payments: list[int],
    debt_service: list[int],
    payments_known: bool,
    receipts_known: bool,
    complete: bool,
) -> LiquidityLedger:
    """The cash ledger from `balances`, a figure shown only where everything it rests on is
    known: the first opening is the opening cash, and an unknown month makes every later
    balance unknown."""
    rows = []
    for n, month in enumerate(months):
        opening, lower, closing = bounds[n]
        rows.append(
            LiquidityMonth(
                month=month,
                opening_minor=opening if n == 0 or complete else None,
                early_receipts_minor=early[n] if receipts_known else None,
                living_minor=living[n],
                payments_minor=payments[n] if payments_known else None,
                debt_service_minor=debt_service[n],
                lower_bound_minor=lower if complete else None,
                later_receipts_minor=later[n] if receipts_known else None,
                closing_minor=closing if complete else None,
            )
        )
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
