from fastapi import APIRouter, Depends, Request

from app.auth import verify_api_key


router = APIRouter()


@router.get("/history")
async def history(request: Request, user_id: str = Depends(verify_api_key)):
    history_items = await request.app.state.history.get_history(user_id)
    return {"count": len(history_items), "messages": history_items}

