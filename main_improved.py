import asyncio
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

# companies_service.py


class CompanyStatus(Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    EXITED = "exited"


@dataclass(frozen=True)
class Company:
    company_id: int
    status: CompanyStatus | None
    preferred_investor_ids: tuple[int, ...]


MOCK_COMPANIES: dict[int, Company] = {
    1: Company(
        company_id=1, status=CompanyStatus.APPROVED, preferred_investor_ids=(1, 3)
    ),
    2: Company(
        company_id=2, status=CompanyStatus.REJECTED, preferred_investor_ids=(1, 3)
    ),
    3: Company(company_id=3, status=None, preferred_investor_ids=(1,)),
}


async def fetch_company(company_id: int) -> Company:
    """Mock API call to the companies service to fetch one company"""
    await asyncio.sleep(1)  # Simulate a network delay
    return MOCK_COMPANIES[company_id]


# equity_service.py


@dataclass(frozen=True)
class OptionGrant:
    option_grant_id: int
    quantity: int
    purchase_price: Decimal

    @property
    def value(self) -> Decimal:
        return self.quantity * self.purchase_price


MOCK_OPTION_GRANTS: dict[int, OptionGrant] = {
    1: OptionGrant(option_grant_id=1, quantity=50_000, purchase_price=Decimal("10.0")),
    2: OptionGrant(option_grant_id=2, quantity=110_000, purchase_price=Decimal("20.0")),
    3: OptionGrant(
        option_grant_id=3, quantity=1_000_000, purchase_price=Decimal("15.0")
    ),
    4: OptionGrant(option_grant_id=4, quantity=100, purchase_price=Decimal("15.0")),
}


async def fetch_option_grant(option_grant_id: int) -> OptionGrant:
    """Mock API call to the equity service to fetch one option grant"""
    await asyncio.sleep(1)  # Simulate a network delay
    return MOCK_OPTION_GRANTS[option_grant_id]


async def fetch_option_grants(option_grant_ids: Iterable[int]) -> list[OptionGrant]:
    return await asyncio.gather(
        *(fetch_option_grant(grant_id) for grant_id in option_grant_ids)
    )


# investors_service.py


@dataclass(frozen=True)
class Investor:
    investor_id: int
    min_deal_size: Decimal
    max_deal_size: Decimal | None

    def accepts(self, deal_size: Decimal) -> bool:
        return deal_size > self.min_deal_size and (
            self.max_deal_size is None or deal_size < self.max_deal_size
        )


MOCK_INVESTORS: list[Investor] = [
    Investor(
        investor_id=1,
        min_deal_size=Decimal(100_000),
        max_deal_size=Decimal(10_000_000),
    ),
    Investor(investor_id=2, min_deal_size=Decimal(1_000_000), max_deal_size=None),
    Investor(
        investor_id=3,
        min_deal_size=Decimal(10_000),
        max_deal_size=Decimal(1_000_000),
    ),
]


async def fetch_investors() -> list[Investor]:
    """Mock API call to the investors service to fetch all investors"""
    await asyncio.sleep(1)  # Simulate a network delay
    return MOCK_INVESTORS


# financing.py


class FinancingStatus(Enum):
    IN_REVIEW = "in_review"
    ACCEPTED = "accepted"
    DECLINED = "declined"


_STATUS_BY_COMPANY_STATUS: dict[CompanyStatus | None, FinancingStatus] = {
    None: FinancingStatus.IN_REVIEW,
    CompanyStatus.APPROVED: FinancingStatus.ACCEPTED,
    CompanyStatus.REJECTED: FinancingStatus.DECLINED,
    CompanyStatus.EXITED: FinancingStatus.DECLINED,
}


@dataclass(frozen=True)
class FinancingRequest:
    company_id: int
    option_grant_ids: list[int]


@dataclass(frozen=True)
class FinancingResult:
    status: FinancingStatus
    deal_size: Decimal
    investor_id: int | None = None


def determine_status(company: Company) -> FinancingStatus:
    return _STATUS_BY_COMPANY_STATUS[company.status]


def calculate_deal_size(option_grants: Iterable[OptionGrant]) -> Decimal:
    return sum((grant.value for grant in option_grants), Decimal(0))


def select_investor(
    deal_size: Decimal,
    investors: Iterable[Investor],
    preferred_investor_ids: Iterable[int],
) -> int | None:
    """Pick the first matching preferred investor, else the first matching one."""
    matching = [investor for investor in investors if investor.accepts(deal_size)]
    if not matching:
        return None

    preferred = set(preferred_investor_ids)
    return next(
        (inv.investor_id for inv in matching if inv.investor_id in preferred),
        matching[0].investor_id,
    )


async def process_financing_request(request: FinancingRequest) -> FinancingResult:
    company, investors, option_grants = await asyncio.gather(
        fetch_company(request.company_id),
        fetch_investors(),
        fetch_option_grants(request.option_grant_ids),
    )

    status = determine_status(company)
    deal_size = calculate_deal_size(option_grants)

    if status is FinancingStatus.DECLINED:
        return FinancingResult(status=status, deal_size=deal_size)

    return FinancingResult(
        status=status,
        deal_size=deal_size,
        investor_id=select_investor(
            deal_size, investors, company.preferred_investor_ids
        ),
    )
