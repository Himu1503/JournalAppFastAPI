import logging
from time import perf_counter
from uuid import uuid4
from fastapi import FastAPI,HTTPException, Request
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
import jwt
from database import Base, SessionLocal, engine
from models.JournalEntries import JournalEntries
from models.user import Users
from schemas import JournalEntryCreate, JournalEntryRead, UserCreate, UserRead, UserLogin, Token
from security import create_access_token, decode_access_token, hash_password, verify_password

from utils.logging import setup_logging
setup_logging()
logger = logging.getLogger(__name__)


app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid4())[:8]
    start = perf_counter()
    response = await call_next(request)
    duration_ms = round((perf_counter() - start) * 1000, 2)
    logger.info(
        "request_id=%s method=%s path=%s status=%s duration_ms=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    response.headers["X-Request-ID"] = request_id
    return response

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
        logger.warning("auth_failed reason=invalid_token")
        raise credentials_error

    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        logger.warning("auth_failed reason=user_not_found user_id=%s", user_id)
        raise credentials_error
    logger.info("auth_success user_id=%s", user.id)
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
    logger.info("journal_created user_id=%s journal_id=%s", user_id, db_entry.id)
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
    logger.info("user_created user_id=%s email=%s", db_user.id, db_user.email)
    return db_user


@app.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.email == user_credentials.email).first()
    if not user or not verify_password(user_credentials.password, user.password):
        logger.warning("login_failed email=%s", user_credentials.email)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    logger.info("login_success user_id=%s", user.id)
    return {"access_token": create_access_token(user.id), "token_type": "bearer"}



@app.get("/user", response_model = list[UserRead])
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

