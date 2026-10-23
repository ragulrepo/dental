from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routes import auth
from app.routes import patients
from app.routes import treatments
from app.routes import dentists
from app.routes import appointments
from app.services.scheduler import shutdown_scheduler, start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(treatments.router)
app.include_router(dentists.router)
app.include_router(appointments.router)


@app.get("/")
def root():
    return {"message": "Welcome to the Dental Booking API!"}
