#resolve the final rate limit by combining route and plan configs
def resolve_limits(route_config, plan_config):

    # Admin plans bypass normal route restrictions.
    if plan_config.get("override"):
        return{
            "capacity": plan_config.get("capacity", 100000),
            "refill_rate": plan_config.get("refill_rate", 100000)
        }
    
    return{
        "capacity": min(route_config["capacity"], plan_config["capacity"]),
        "refill_rate": min(route_config["refill_rate"], plan_config["refill_rate"])
    }