from fastapi import APIRouter
router=APIRouter(tags=["health"])
@router.get("/health")
def health(): return {"status":"ok","version":"1.0.0"}
@router.get("/readiness")
def readiness(): return {"status":"ready"}
