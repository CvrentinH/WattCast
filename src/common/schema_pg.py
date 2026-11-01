from sqlalchemy.orm import Session, sessionmaker


class SchemaPG:
    def __init__(self, client: sessionmaker[Session], name: str) -> None:
        if not name:
            raise ValueError("Bucket name is required")

        self.client = client
        self.name = name
