

def validate_age(age: str, min_age: int = 18, max_age: int = 100) -> bool:
    try:
        age = int(age)
    except ValueError:
        return False
    return min_age <= age <= max_age


def validate_experience(experience: str) -> bool:
    try:
        experience = int(experience)
    except ValueError:
        return False
    return experience > 0


def validate_info(info: str) -> bool:
    return len(info) <= 600


def validate_price(price: str) -> bool:
    try:
        price = float(price)
    except ValueError:
        return False
    return price > 0

