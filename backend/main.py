from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base, SessionLocal
from app.seed import init_seed_data
from app.api import products as products_api
from app.api import templates as templates_api
from app.api import projects as projects_api
from app.api import ai as ai_api
from app.api import settings as settings_api
from app.api import export as export_api
from app.api import stakeholders as stakeholders_api
from app.api import docs_api
from app.api import template_mgmt as template_mgmt_api
from app.api import overdue as overdue_api
from app.api import email_api as email_api
from app.api import tracking as tracking_api
from app.api import acceptance as acceptance_api
from app.api import report as report_api

app = FastAPI(title="CCB 项目管理系统 API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev
        "file://",                 # Electron production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        init_seed_data(db)
    finally:
        db.close()


app.include_router(products_api.router)
app.include_router(templates_api.router)
app.include_router(projects_api.router)
app.include_router(settings_api.router)
app.include_router(export_api.router)
app.include_router(stakeholders_api.router)
app.include_router(tracking_api.router)
app.include_router(acceptance_api.router)
app.include_router(docs_api.router)
app.include_router(ai_api.router)
app.include_router(ai_api.project_router)
app.include_router(template_mgmt_api.router)
app.include_router(report_api.router)
app.include_router(overdue_api.router)
app.include_router(email_api.router)
app.include_router(email_api.notify_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
