import time
from dataclasses import dataclass
from enum import Enum


@dataclass
class FinancingRequest:
    company_id: int
    option_grant_ids: list[int]


def process_financing_request(request: FinancingRequest):
    result = {}

    company = fetch_company(request.company_id)

    if company.status is None:
        result["status"] = "in_review"
    else:
        if company.status.value == "approved":
            result["status"] = "accepted"

        if company.status.value == "rejected" or company.status.value == "exited":
            result["status"] = "declined"

    deal_size = 0.0

    for i in range(len(request.option_grant_ids)):
        option_grant = fetch_option_grant(request.option_grant_ids[i])
        deal_size += option_grant.quantity * option_grant.purchase_price

    result["deal_size"] = deal_size

    investors = fetch_investors()

    result["investor_id"] = None

    if result["status"] == "declined":
        return result

    matching_investors = []

    for investor in investors:
        if deal_size > investor.min_deal_size and (
            investor.max_deal_size is None or deal_size < investor.max_deal_size
        ):
            matching_investors.append(investor)

    for matching_investor in matching_investors:
        preferred_investor_found = False

        for preferred_investor_id in company.preferred_investor_ids:
            if preferred_investor_id == matching_investor.investor_id:
                result["investor_id"] = matching_investor.investor_id
                preferred_investor_found = True
                break

        if preferred_investor_found:
            break

    if result["investor_id"] is None:
        result["investor_id"] = matching_investors[0].investor_id

    return result


# companies_service.py


class CompanyStatus(Enum):
    approved = "approved"
    rejected = "rejected"
    exited = "exited"


@dataclass
class Company:
    company_id: int
    status: CompanyStatus | None
    preferred_investor_ids: list[int]


MOCK_COMPANIES = {
    1: Company(
        company_id=1, status=CompanyStatus.approved, preferred_investor_ids=[1, 3]
    ),
    2: Company(
        company_id=2, status=CompanyStatus.rejected, preferred_investor_ids=[1, 3]
    ),
    3: Company(company_id=3, status=None, preferred_investor_ids=[1]),
}


def fetch_company(company_id):
    """Mock API call to the companies service to fetch one company"""
    time.sleep(1)  # Simulate a network delay
    return MOCK_COMPANIES[company_id]


# equity_service.py


@dataclass
class OptionGrant:
    option_grant_id: int
    quantity: int
    purchase_price: float


MOCK_OPTION_GRANTS = {
    1: OptionGrant(option_grant_id=1, quantity=50_000, purchase_price=10.0),
    2: OptionGrant(option_grant_id=2, quantity=110_000, purchase_price=20.0),
    3: OptionGrant(option_grant_id=3, quantity=1_000_000, purchase_price=15.0),
    4: OptionGrant(option_grant_id=4, quantity=100, purchase_price=15.0),
}


def fetch_option_grant(option_grant_id):
    """Mock API call to the equity service to fetch one option grant"""
    time.sleep(1)  # Simulate a network delay
    return MOCK_OPTION_GRANTS[option_grant_id]


# investors_service.py


@dataclass
class Investor:
    investor_id: int
    min_deal_size: float
    max_deal_size: float | None


MOCK_INVESTORS = [
    Investor(investor_id=1, min_deal_size=100_000.0, max_deal_size=10_000_000.0),
    Investor(investor_id=2, min_deal_size=1_000_000.0, max_deal_size=None),
    Investor(investor_id=3, min_deal_size=10_000.0, max_deal_size=1_000_000.0),
]


def fetch_investors():
    """Mock API call to the investors service to fetch all investors"""
    time.sleep(1)  # Simulate a network delay
    return MOCK_INVESTORS
