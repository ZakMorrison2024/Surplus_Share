from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from geopy.distance import geodesic
from uuid import uuid4
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, String, Float, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database setup
DATABASE_URL = "sqlite:///./swapcircle.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Models
class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    rating = Column(Float, default=0.0)

class Item(Base):
    __tablename__ = "items"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    category = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    owner_id = Column(String)

Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI()

class UserCreate(BaseModel):
    username: str
    password: str
    latitude: float
    longitude: float

class ItemCreate(BaseModel):
    name: str
    description: str
    category: str
    latitude: float
    longitude: float

@app.post("/register/")
def register_user(user: UserCreate, db: SessionLocal = Depends(get_db)):
    hashed_password = pwd_context.hash(user.password)
    db_user = User(id=str(uuid4()), username=user.username, password=hashed_password, latitude=user.latitude, longitude=user.longitude)
    db.add(db_user)
    db.commit()
    return {"message": "User registered successfully"}

@app.post("/items/")
def create_item(item: ItemCreate, db: SessionLocal = Depends(get_db)):
    db_item = Item(id=str(uuid4()), **item.dict())
    db.add(db_item)
    db.commit()
    return {"message": "Item listed successfully"}

@app.get("/items/nearby/")
def get_nearby_items(lat: float, lon: float, radius: float, db: SessionLocal = Depends(get_db)):
    items = db.query(Item).all()
    nearby_items = [
        item for item in items if geodesic((lat, lon), (item.latitude, item.longitude)).km <= radius
    ]
    return nearby_items

@app.get("/users/{username}")
def get_user(username: str, db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
