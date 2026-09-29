from fastapi import Request

from app.database import Databases


def get_databases(request: Request) -> Databases:
    return request.app.state.databases

