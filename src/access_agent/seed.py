"""Generate the fictional company.

Larkspur Freight doesn't exist. Every person and group here is made up by this
file, the same way on every run, and the email domain is under `.example`,
which is reserved and can never resolve.

The directory includes the awkward cases on purpose, because an eval set with
only clean cases proves nothing: people who share a name, groups whose names
differ by a word, a restricted group with no owner, and inactive accounts.
"""

from __future__ import annotations

import random

from .directory import Directory
from .models import Group, Status, Tier, User

COMPANY = "Larkspur Freight"
DOMAIN = "larkspur-freight.example"
DEFAULT_SEED = 20261114

DEPARTMENTS = ("Finance", "Operations", "Sales", "Engineering", "People", "Legal", "Support")

FIRST = (
    "Ada", "Ben", "Cora", "Dev", "Elena", "Farid", "Gwen", "Hugo", "Ines", "Jonah", "Kira", "Leo",
    "Mara", "Nico", "Opal", "Priya", "Quinn", "Rafa", "Sana", "Theo", "Uma", "Vik", "Wren", "Yara",
)  # fmt: skip
LAST = (
    "Abbott", "Barros", "Castell", "Dunmore", "Eklund", "Farrow", "Galvez", "Hartwell", "Ibarra",
    "Jessop", "Kovacs", "Lindqvist", "Marlowe", "Nakata", "Oyelaran", "Pellegrin", "Quimby",
    "Rosales", "Strand", "Tavares", "Underhill", "Voss", "Whitlock", "Yoon",
)  # fmt: skip

# name, description, tier, owning department (None = no owner), departments allowed to join
GROUPS: tuple[tuple[str, str, Tier, str | None, tuple[str, ...]], ...] = (
    ("All-Staff-News", "Company announcements for everyone", Tier.STANDARD, "People", ()),
    ("Office-Wifi-Guests", "Guest wifi sponsors", Tier.STANDARD, "Operations", ()),
    ("Sales-Team", "Sales team shared files and channel", Tier.STANDARD, "Sales", ("Sales",)),
    ("Sales-Forecast-Readers", "Read access to the sales forecast", Tier.STANDARD, "Sales", ("Sales", "Finance")),
    ("Support-Queue-Agents", "Agents who work the support queue", Tier.STANDARD, "Support", ("Support",)),
    ("Engineering-Docs", "Engineering wiki and design docs", Tier.STANDARD, "Engineering", ()),
    ("Engineering-Oncall", "Engineers on the on-call rota", Tier.STANDARD, "Engineering", ("Engineering",)),
    ("Operations-Dispatch", "Dispatch board for freight operations", Tier.STANDARD, "Operations", ("Operations",)),
    ("Finance-Reports", "Read access to monthly finance reports", Tier.RESTRICTED, "Finance", ("Finance", "Legal")),
    ("Finance-Reports-Editors", "Edit access to monthly finance reports", Tier.RESTRICTED, "Finance", ("Finance",)),
    ("Finance-Payroll", "Payroll runs and salary data", Tier.RESTRICTED, "Finance", ("Finance", "People")),
    ("People-Records", "Employee records and reviews", Tier.RESTRICTED, "People", ("People",)),
    ("Legal-Contracts", "Signed customer and carrier contracts", Tier.RESTRICTED, "Legal", ("Legal", "Sales")),
    ("Customer-Data-Export", "Bulk export of customer shipment data", Tier.RESTRICTED, None, ("Support", "Operations")),
    ("Engineering-Prod-Deploy", "Can deploy to production", Tier.RESTRICTED, "Engineering", ("Engineering",)),
    ("Directory-Admins", "Administers this directory", Tier.PRIVILEGED, "Engineering", ("Engineering",)),
    ("Finance-Bank-Approvers", "Approves outgoing bank payments", Tier.PRIVILEGED, "Finance", ("Finance",)),
    ("Security-Break-Glass", "Emergency access to every system", Tier.PRIVILEGED, "Engineering", ("Engineering",)),
)  # fmt: skip

USERS_PER_DEPARTMENT = 14
INACTIVE_SHARE = 0.08


def _email(name: str, taken: set[str]) -> str:
    base = name.lower().replace(" ", ".")
    email = f"{base}@{DOMAIN}"
    n = 2
    while email in taken:
        email = f"{base}{n}@{DOMAIN}"
        n += 1
    taken.add(email)
    return email


def seed(directory: Directory, seed_value: int = DEFAULT_SEED) -> None:
    """Fill an empty directory. Same seed, same company."""
    rng = random.Random(seed_value)  # noqa: S311 - generating fake data, not secrets
    taken: set[str] = set()
    users: list[User] = []
    heads: dict[str, str] = {}
    number = 0

    for department in DEPARTMENTS:
        head_id: str | None = None
        for position in range(USERS_PER_DEPARTMENT):
            number += 1
            user_id = f"u-{number:05d}"
            name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
            is_head = position == 0
            status = Status.ACTIVE if is_head or rng.random() > INACTIVE_SHARE else Status.INACTIVE
            users.append(
                User(
                    id=user_id,
                    name=name,
                    email=_email(name, taken),
                    department=department,
                    status=status,
                    manager_id=head_id,
                )
            )
            if is_head:
                head_id = user_id
                heads[department] = user_id

    # Two pairs of people who share a name, in different departments, so a
    # name alone never identifies anyone.
    for name, first_dept, second_dept in (("Sam Carter", "Finance", "Sales"), ("Jo Bianchi", "Support", "Legal")):
        for department in (first_dept, second_dept):
            number += 1
            users.append(
                User(
                    id=f"u-{number:05d}",
                    name=name,
                    email=_email(name, taken),
                    department=department,
                    status=Status.ACTIVE,
                    manager_id=heads[department],
                )
            )

    for user in users:
        directory.put_user(user)

    for index, (name, description, tier, owner_dept, allowed) in enumerate(GROUPS, start=1):
        directory.put_group(
            Group(
                id=f"g-{index:04d}",
                name=name,
                description=description,
                tier=tier,
                owner_id=heads[owner_dept] if owner_dept else None,
                allowed_departments=allowed,
            )
        )
