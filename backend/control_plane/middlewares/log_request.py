from fastapi import Request


def start_logging(app):
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        print(f"Запрос: {request.method} {request.url} {request.headers}")
        try:
            print(await request.json())
        except:
            pass
        response = await call_next(request)
        return response
