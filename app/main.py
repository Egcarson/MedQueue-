from fastapi import FastAPI
from app.database import engine, Base
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from app.database import engine, Base, SessionLocal
from app.routers import auth, hospitals, users, sign_up_link as link_gen
from app.crud import sign_up_link as link
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

# Function to schedule the cleanup task


def cleanup_job():
    db: Session = SessionLocal()
    try:
        link.delete_expired_tokens(db)
    finally:
        db.close()


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=cleanup_job, trigger="interval", hours=24)
    scheduler.start()
    return scheduler

# Call this function during app startup
@app.lifespan
def app_lifespan(app: FastAPI) -> Lifespan:
    # Start the scheduler
    scheduler = schedule_cleanup()

    yield  # Wait for the app to shut down

    # Shutdown the scheduler gracefully
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

# Include routers
app.include_router(link_gen.router)
app.include_router(auth.router)
app.include_router(hospitals.router)
app.include_router(users.router)


@app.get('/')
def root():
    return {'message': 'Queue_Medix API!'}
