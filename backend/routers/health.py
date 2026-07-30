from fastapi import APIRouter

router = APIRouter(tags=['health'])


@router.get('/health')
def health_check():
    """Liveness check -- deliberately has no DB dependency, so it still
    answers even if the database is unreachable (useful for Part 11
    deploy health checks distinguishing "app is up" from "app can reach its DB")."""
    return {'status': 'ok'}
