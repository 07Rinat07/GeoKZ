import argparse
import asyncio
from getpass import getpass

from app.application.auth import AuthenticationService, UserAccountConflictError
from app.core.database import AsyncSessionFactory
from app.models.enums import UserRole


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GeoKZ authentication administration")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser(
        "create-user",
        help="Create a local GeoKZ account. Password is read securely from the terminal.",
    )
    create.add_argument("--username", required=True)
    create.add_argument("--display-name", required=True)
    create.add_argument(
        "--role",
        required=True,
        choices=[role.value for role in UserRole],
    )
    return parser


async def _create_user(args: argparse.Namespace) -> int:
    password = getpass("Password (minimum 12 characters): ")
    confirmation = getpass("Repeat password: ")
    if password != confirmation:
        print("Passwords do not match.")
        return 2

    async with AsyncSessionFactory() as session:
        try:
            user = await AuthenticationService(session).create_user(
                username=args.username,
                display_name=args.display_name,
                role=UserRole(args.role),
                password=password,
                created_by=None,
            )
        except (ValueError, UserAccountConflictError) as error:
            print(f"Cannot create user: {error}")
            return 2

    print(f"Created GeoKZ user {user.username!r} with role={user.role.value}.")
    return 0


async def _run(args: argparse.Namespace) -> int:
    if args.command == "create-user":
        return await _create_user(args)
    raise RuntimeError(f"Unsupported command: {args.command}")


def main() -> None:
    args = _parser().parse_args()
    raise SystemExit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
