def buid_rate_limit_key(request):
    
    if request.user.is_authenticated:
        identifier = f"user_{request.user.id}"
    elif request.headers.get("X-API-Key"):
        identifier = f"api_{request.headers.get('X-API-Key')}"
    else:
        identifier = request.META.get("REMOTE_ADDR")

    path = request.path

    return f"rate_limit:{identifier}:{path}"