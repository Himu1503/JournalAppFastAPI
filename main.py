from fastapi import FastAPI,HTTPException
from fastapi import Depends
from typing import List
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from database import Base, SessionLocal, engine
from models.JournalEntries import JournalEntries
from models.user import Users
from schemas import JournalEntryCreate, JournalEntryRead, UserCreate, UserRead


app = FastAPI()

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

@app.get("/")
async def healthCheck():
    return {"message": "Hello World"}

@app.post("/journal", response_model=JournalEntryRead)
async def JournalEntriesPost(entry: JournalEntryCreate, db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.id == entry.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db_entry = JournalEntries(**entry.model_dump())
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

@app.get("/journal", response_model=list[JournalEntryRead])
async def getJournalEntries(user_id: int | None = None, db: Session = Depends(get_db)):
    entries_query = db.query(JournalEntries)
    if user_id is not None:
        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        entries_query = entries_query.filter(JournalEntries.user_id == user_id)
    entries = entries_query.all()
    if not entries:
        raise HTTPException(status_code=404, detail="No journal entries found")
    return entries


@app.get("/journal/{id}", response_model=JournalEntryRead)
async def getJournalEntryById(id:int , db:Session = Depends(get_db)):
    entry = db.query(JournalEntries).filter(JournalEntries.id == id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return entry


@app.post("/user" , response_model=UserRead)
async def createUser(user: UserCreate, db: Session = Depends(get_db)):
    db_user = Users(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user



@app.get("/user", response_model = List[UserRead])
async def getUser(db:Session = Depends(get_db)):
    users = db.query(Users).all()
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    return users



@app.get("/user/{id}" , response_model = UserRead)
async def getUserById(id:int , db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

