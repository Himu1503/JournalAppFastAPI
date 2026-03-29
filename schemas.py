from pydantic import BaseModel, ConfigDict

class JournalEntryCreate(BaseModel):
    title: str
    content: str
    user_id: int


class JournalEntryRead(BaseModel):
    id: int
    title: str
    content: str
    user_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    model_config = ConfigDict(from_attributes=True)


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    journal_entries: list[JournalEntryRead] = []
    model_config = ConfigDict(from_attributes=True)