from aiogram import Router

def setup_routers() -> Router:
    from .users import (
        admin, start, help, register, selecttest, starttest,
        updateFIO, admin_registration, add_group, statistics
    )
    from .errors import error_handler
    from .groups import start_group

    router = Router()

    router.include_routers(
        admin.router, start.router, register.router, admin_registration.admin_router,
        selecttest.router, starttest.router, updateFIO.router, help.router,
        error_handler.router, add_group.admin_router, start_group.router, statistics.router
    )

    return router
