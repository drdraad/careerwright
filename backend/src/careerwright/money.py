"""Money in integer minor units (Global Constraint 4). Unknown money is null, never zero.

L0 is GBP only (ADR 0001). The minor-unit exponent is metadata of the currency; code never
assumes a division by 100. `SignedMoney` holds economic values (spec section 18), which may be
negative against a baseline and are never cash available today.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Currency = Literal["GBP"]
# Integer GBP minor units, never negative: for arithmetic inside a module. What crosses the
# API is `Money` or `SignedMoney`, never a bare amount.
Minor = Annotated[int, Field(ge=0)]


class Money(BaseModel):
    """A payment, fee, cap or balance: never negative."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    minor_units: int = Field(ge=0)
    currency: Currency


class SignedMoney(BaseModel):
    """An economic cost or an income change: negative is a gain against the baseline."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    minor_units: int
    currency: Currency
