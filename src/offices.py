OFFICES = [
    {"_id": "engineering-kano", "name": "Engineering Kano", "location": "Kano"},
    {"_id": "logistics-kano", "name": "Logistics Kano", "location": "Kano"},
    {"_id": "logistics-bauchi", "name": "Logistics Bauchi", "location": "Bauchi"},
    {"_id": "logistics-lagos", "name": "Logistics Lagos", "location": "Lagos"},
    {"_id": "logistics-onitsha", "name": "Logistics Onitsha", "location": "Onitsha"},
    {"_id": "logistics-ph", "name": "Logistics PH", "location": "PH"},
    {"_id": "logistics-abuja", "name": "Logistics Abuja", "location": "Abuja"},
]
OFFICE_MAP = {office["_id"]: office for office in OFFICES}


def sync_offices(office_docs):
    """Synchronize dynamically loaded offices into OFFICES and OFFICE_MAP."""
    if not office_docs:
        return
    for doc in office_docs:
        oid = doc.get("_id")
        if not oid:
            continue
        OFFICE_MAP[oid] = doc
        if not any(o["_id"] == oid for o in OFFICES):
            OFFICES.append(doc)


def register_office(doc):
    """Register a newly created office."""
    if not doc:
        return
    oid = doc.get("_id")
    if not oid:
        return
    OFFICE_MAP[oid] = doc
    if not any(o["_id"] == oid for o in OFFICES):
        OFFICES.append(doc)
