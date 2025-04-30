from fastapi import Request


def start_logging(app):
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        print(f"Запрос: {request.method} {request.url} {request.headers}")
        print(await request.json())
        response = await call_next(request)
        return response
