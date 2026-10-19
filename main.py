from fastapi import FastAPI
from app.routes import auth
from app.routes import patients
from app.routes import treatments
from app.routes import dentists
from app.routes import appointments
app = FastAPI()

app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(treatments.router)
app.include_router(dentists.router)
app.include_router(appointments.router)


@app.get("/")
def root():
    return {"message": "Welcome to the Dental Booking API!"}
