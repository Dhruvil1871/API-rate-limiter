from limiter.models import RouteLimit

DEFAULT_LIMIT = {
    "capacity" : 10,
    "refill_rate" : 1,
    "algorithm" : "token_bucket"
}

def get_route_config(path):
    try:
        route = RouteLimit.objects.get(
            route = path,
            enabled = True,
        )

        return{
            "capacity" : route.capacity,
            "refill_rate" : route.refill_rate,
            "algorithm" : route.algorithm,
        }
    
    except RouteLimit.DoesNotExist:
        return DEFAULT_LIMIT