from fastapi import FastAPI,HTTPException
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from typing import List
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
import jwt
from database import Base, SessionLocal, engine
from models.JournalEntries import JournalEntries
from models.user import Users
from schemas import JournalEntryCreate, JournalEntryRead, UserCreate, UserRead, UserLogin, Token
from security import create_access_token, decode_access_token, hash_password, verify_password


app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

Base.metadata.create_all(bind=engine)

inspector = inspect(engine)
if "journal_entries" in inspector.get_table_names():
    columns = {column["name"] for column in inspector.get_columns("journal_entries")}
    if "user_id" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE journal_entries ADD COLUMN user_id INTEGER"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_journal_entries_user_id ON journal_entries (user_id)"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    credentials_error = HTTPException(status_code=401, detail="Invalid authentication credentials")
    try:
        payload = decode_access_token(token)
        sub = payload.get("sub")
        user_id = int(sub)
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise credentials_error

    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise credentials_error
    return user

@app.get("/")
async def healthCheck():
    return {"message": "Hello World"}

@app.post("/journal/{user_id}", response_model=JournalEntryRead)
async def JournalEntriesPost(
    user_id: int,
    entry: JournalEntryCreate,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized for this user")
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db_entry = JournalEntries(**entry.model_dump(), user_id=user_id)
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

@app.get("/journal", response_model=list[JournalEntryRead])
async def getJournalEntries(
    user_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    if user_id is not None and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized for this user")
    entries_query = db.query(JournalEntries)
    if user_id is None:
        user_id = current_user.id
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    entries_query = entries_query.filter(JournalEntries.user_id == user_id)
    entries = entries_query.all()
    if not entries:
        raise HTTPException(status_code=404, detail="No journal entries found")
    return entries


@app.get("/journal/{id}", response_model=JournalEntryRead)
async def getJournalEntryById(
    id:int,
    db:Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    entry = db.query(JournalEntries).filter(JournalEntries.id == id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    if entry.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized for this entry")
    return entry


@app.post("/user" , response_model=UserRead)
async def createUser(user: UserCreate, db: Session = Depends(get_db)):
    db_user = Users(**user.model_dump(exclude={"password"}), password=hash_password(user.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.email == user_credentials.email).first()
    if not user or not verify_password(user_credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"access_token": create_access_token(user.id), "token_type": "bearer"}



@app.get("/user", response_model = List[UserRead])
async def getUser(
    db:Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    users = db.query(Users).all()
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    return users



@app.get("/user/{id}" , response_model = UserRead)
async def getUserById(
    id:int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    if current_user.id != id:
        raise HTTPException(status_code=403, detail="Not authorized for this user")
    user = db.query(Users).filter(Users.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

