"""Money in integer minor units (Global Constraint 4). Unknown money is null, never zero.

L0 is GBP only (ADR 0001). The minor-unit exponent is metadata of the currency; code never
assumes a division by 100. `SignedMoney` (economic values, spec section 18) arrives with its
first user, the monthly compiler.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Currency = Literal["GBP"]


class Money(BaseModel):
    """A payment, fee, cap or balance: never negative."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    minor_units: int = Field(ge=0)
    currency: Currency
