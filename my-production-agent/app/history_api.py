from fastapi import APIRouter, Depends

from app.auth import verify_api_key


router = APIRouter()


@router.get("/history")
async def history(user_id: str = Depends(verify_api_key)):
    history_items = await router.app.state.history.get_history(user_id)
    return {"count": len(history_items), "messages": history_items}

