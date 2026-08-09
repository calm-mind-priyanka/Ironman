import os


def _required(name: str) -> str:
    value = os.environ.get(name)

    if not value:
        raise RuntimeError(
            f"Required environment variable {name} is not set."
        )

    return value


class Config:

    API_ID = int(
        _required("API_ID")
    )

    API_HASH = _required(
        "API_HASH"
    )

    BOT_TOKEN = _required(
        "BOT_TOKEN"
    )

    DATABASE_URI = _required(
        "DATABASE_URI"
    )

    DATABASE_URI_2 = os.environ.get(
        "DATABASE_URI_2",
        DATABASE_URI
    )

    DATABASE_NAME = os.environ.get(
        "DATABASE_NAME",
        "AutoFilterBot"
    )

    ADMINS = [
        int(admin)
        for admin in os.environ.get(
            "ADMINS",
            ""
        ).split()
        if admin.strip()
    ]

    LOG_CHANNEL = int(
        os.environ.get(
            "LOG_CHANNEL",
            "0"
        )
    )

    AUTO_INDEX_CHANNEL = int(
        os.environ.get(
            "AUTO_INDEX_CHANNEL",
            "0"
        )
    )
