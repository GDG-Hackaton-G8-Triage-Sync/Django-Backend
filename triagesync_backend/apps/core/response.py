def api_success(data=None, message="success"):
    return {
        "ok": True,
        "message": message,
        "data": data,
    }
