

def split_subject(subject: str) -> list[str]:
    return [x.strip().lower() for x in subject.split(',')]
