RATE_LIMITS = {
    "/":{"capacity": 10, "refill_rate" : 1},
    "/api/login":{"capacity": 5, "refill_rate" : 0.2},
    "/api/data":{"capacity": 20, "refill_rate" : 2},
}

PLAN_LIMITS = {
    "free" : {"capacity": 10, "refill_rate" : 1},
    "premium":{"capacity": 50, "refill_rate" : 10},
    "admin":{"override" : True, "capacity": 100000, "refill_rate": 10000},
}