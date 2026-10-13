"""Seed reference data: tier-1 and tier-2 Indian cities + popular long/short-haul trains.

Station codes follow real IR codes where possible so queries like
"trains from Mumbai to Delhi" or "NDLS to BCT" both resolve.
"""

from sqlalchemy.orm import Session

from app.db import Coach, SessionLocal, Station, Train


# ---------------------------------------------------------------------------
# Stations — tier-1 metros + major tier-2 cities (code, station name, city)
# ---------------------------------------------------------------------------
STATIONS = [
    # Tier-1 metros
    ("NDLS", "New Delhi",              "Delhi"),
    ("BCT",  "Mumbai Central",         "Mumbai"),
    ("CSMT", "CSMT Mumbai",            "Mumbai"),
    ("HWH",  "Howrah Junction",        "Kolkata"),
    ("SDAH", "Sealdah",                "Kolkata"),
    ("MAS",  "MGR Chennai Central",    "Chennai"),
    ("SBC",  "KSR Bengaluru",          "Bengaluru"),
    ("SC",   "Secunderabad Junction",  "Hyderabad"),
    ("HYB",  "Hyderabad Deccan",       "Hyderabad"),
    ("ADI",  "Ahmedabad Junction",     "Ahmedabad"),
    ("PUNE", "Pune Junction",          "Pune"),

    # Tier-2 — North
    ("JP",   "Jaipur Junction",        "Jaipur"),
    ("LKO",  "Lucknow",                "Lucknow"),
    ("CNB",  "Kanpur Central",         "Kanpur"),
    ("AGC",  "Agra Cantt",             "Agra"),
    ("CDG",  "Chandigarh",             "Chandigarh"),
    ("ASR",  "Amritsar Junction",      "Amritsar"),
    ("DDN",  "Dehradun",               "Dehradun"),
    ("JAT",  "Jammu Tawi",             "Jammu"),
    ("BSB",  "Varanasi Junction",      "Varanasi"),
    ("ALD",  "Prayagraj Junction",     "Prayagraj"),
    ("GKP",  "Gorakhpur Junction",     "Gorakhpur"),

    # Tier-2 — West
    ("ST",   "Surat",                  "Surat"),
    ("BRC",  "Vadodara Junction",      "Vadodara"),
    ("RJT",  "Rajkot Junction",        "Rajkot"),
    ("INDB", "Indore Junction",        "Indore"),
    ("BPL",  "Bhopal Junction",        "Bhopal"),
    ("NGP",  "Nagpur Junction",        "Nagpur"),
    ("JBP",  "Jabalpur",               "Jabalpur"),

    # Tier-2 — South
    ("CBE",  "Coimbatore Junction",    "Coimbatore"),
    ("MDU",  "Madurai Junction",       "Madurai"),
    ("TVC",  "Thiruvananthapuram",     "Thiruvananthapuram"),
    ("ERS",  "Ernakulam Junction",     "Kochi"),
    ("MAJN", "Mangaluru Junction",     "Mangaluru"),
    ("MYS",  "Mysuru Junction",        "Mysuru"),
    ("VSKP", "Visakhapatnam",          "Visakhapatnam"),
    ("BZA",  "Vijayawada Junction",    "Vijayawada"),

    # Tier-2 — East
    ("PNBE", "Patna Junction",         "Patna"),
    ("RNC",  "Ranchi Junction",        "Ranchi"),
    ("BBS",  "Bhubaneswar",            "Bhubaneswar"),
    ("GHY",  "Guwahati",               "Guwahati"),
    ("RPR",  "Raipur Junction",        "Raipur"),
]


# ---------------------------------------------------------------------------
# Trains — mix of Rajdhani / Shatabdi / Duronto / Express / Superfast
# (number, name, source_code, destination_code, dep, arr, duration_minutes)
# ---------------------------------------------------------------------------
TRAINS = [
    # Rajdhanis (fully AC)
    ("12951", "Mumbai Rajdhani",      "NDLS", "BCT",  "16:25", "08:35", 970),
    ("12952", "New Delhi Rajdhani",   "BCT",  "NDLS", "17:00", "08:50", 950),
    ("12302", "Howrah Rajdhani",      "NDLS", "HWH",  "16:55", "10:00", 1025),
    ("12301", "New Delhi Rajdhani",   "HWH",  "NDLS", "16:50", "09:55", 1025),
    ("12309", "Patna Rajdhani",       "NDLS", "PNBE", "17:15", "07:30", 855),
    ("22691", "Bengaluru Rajdhani",   "NDLS", "SBC",  "20:45", "05:30", 1965),
    ("12423", "Dibrugarh Rajdhani",   "NDLS", "GHY",  "20:50", "20:00", 1390),
    ("12437", "Secunderabad Rajdhani","NDLS", "SC",   "15:55", "20:45", 1730),

    # Shatabdis (day trains)
    ("12002", "New Delhi Shatabdi",   "NDLS", "BPL",  "06:00", "13:55", 475),
    ("12001", "Bhopal Shatabdi",      "BPL",  "NDLS", "14:50", "22:30", 460),
    ("12029", "Amritsar Shatabdi",    "NDLS", "ASR",  "07:20", "13:35", 375),
    ("12011", "Kalka Shatabdi",       "NDLS", "CDG",  "07:40", "10:55", 195),
    ("12007", "Mysuru Shatabdi",      "MAS",  "MYS",  "06:00", "13:00", 420),
    ("12243", "Coimbatore Shatabdi",  "MAS",  "CBE",  "15:15", "22:40", 445),

    # Durontos
    ("12259", "Sealdah Duronto",      "NDLS", "SDAH", "12:40", "05:55", 1035),
    ("12267", "Mumbai Duronto",       "ADI",  "BCT",  "22:40", "07:05", 505),

    # Mail / Express superfast
    ("12621", "Tamil Nadu Express",   "NDLS", "MAS",  "22:30", "07:10", 1960),
    ("12627", "Karnataka Express",    "NDLS", "SBC",  "20:15", "04:20", 2045),
    ("12137", "Punjab Mail",          "CSMT", "ASR",  "19:40", "05:10", 2010),
    ("12133", "Mangala Lakshadweep",  "CSMT", "ERS",  "21:40", "11:45", 2165),
    ("12723", "Telangana Express",    "NDLS", "HYB",  "06:55", "08:00", 1505),
    ("12616", "Grand Trunk Express",  "NDLS", "MAS",  "18:40", "06:35", 2155),
    ("12841", "Coromandel Express",   "HWH",  "MAS",  "14:50", "16:50", 1560),
    ("12840", "Chennai Mail",         "HWH",  "MAS",  "23:45", "04:40", 1735),

    # Intercity / Shorter day expresses
    ("12123", "Deccan Queen",         "PUNE", "CSMT", "07:15", "10:25", 190),
    ("12125", "Pragati Express",      "PUNE", "CSMT", "07:50", "11:25", 215),
    ("12009", "Shatabdi Express",     "BCT",  "ADI",  "06:25", "12:45", 380),
    ("12910", "Nizamuddin Garib Rath","BCT",  "NZM",  "17:25", "10:55", 1050),
    ("12471", "Swaraj Express",       "BCT",  "JAT",  "08:35", "17:30", 1975),
    ("12555", "Gorakhdham Express",   "GKP",  "NDLS", "17:35", "08:45", 915),
    ("12559", "Shiv Ganga Express",   "BSB",  "NDLS", "19:00", "07:45", 765),
    ("12275", "Allahabad Duronto",    "ALD",  "NDLS", "19:30", "05:30", 600),

    # Regional
    ("17016", "Visakha Express",      "BZA",  "SC",   "23:30", "06:15", 405),
    ("12728", "Godavari Express",     "VSKP", "HYB",  "17:15", "06:55", 820),
    ("12760", "Charminar Express",    "MAS",  "HYB",  "18:10", "06:55", 765),
    ("12677", "Ernakulam Express",    "SBC",  "ERS",  "13:00", "22:35", 575),
    ("12659", "Gurudev Express",      "MAS",  "NGP",  "11:30", "07:20", 1190),
    ("12645", "Nizamuddin Express",   "ERS",  "NDLS", "18:35", "09:40", 2345),

    # Metro-to-tier2
    ("12909", "Bandra Garib Rath",    "BCT",  "INDB", "22:35", "11:35", 780),
    ("12962", "Avantika Express",     "INDB", "BCT",  "16:20", "08:35", 975),
    ("12724", "AP Express",           "HYB",  "NDLS", "06:30", "05:55", 1405),

    # Metro ↔ Metro fillers (common demo queries)
    ("16529", "Udyan Express",        "SBC",  "CSMT", "20:00", "22:30", 1590),
    ("11013", "Coimbatore Express",   "CSMT", "CBE",  "00:05", "08:25", 1700),
    ("11301", "Udyan Express",        "CSMT", "SBC",  "08:05", "10:35", 1590),
    ("12639", "Brindavan Express",    "SBC",  "MAS",  "07:15", "13:55", 400),
    ("12640", "Brindavan Express",    "MAS",  "SBC",  "15:30", "22:05", 395),
    ("12863", "Howrah SF Express",    "SBC",  "HWH",  "19:50", "04:35", 2085),
    ("12864", "Yesvantpur Express",   "HWH",  "SBC",  "22:35", "07:00", 2065),
    ("22692", "New Delhi Rajdhani",   "SBC",  "NDLS", "20:00", "05:55", 1945),
    ("12215", "Delhi Garib Rath",     "BCT",  "NDLS", "15:35", "08:40", 1025),
    ("12297", "Pune Duronto",         "PUNE", "NDLS", "11:05", "08:40", 1295),
]


# ---------------------------------------------------------------------------
# Coaches — class availability + base fare for each train
# ---------------------------------------------------------------------------
_PREMIUM = [("1A", 24, 5200), ("2A", 54, 3100), ("3A", 72, 2200)]           # Rajdhani
_SHATABDI = [("CC", 110, 1200), ("EC", 56, 2400)]                            # Shatabdi (CC/EC)
_DURONTO = [("2A", 48, 2800), ("3A", 72, 1900), ("SL", 72, 650)]
_EXPRESS = [("SL", 72, 650), ("3A", 64, 1700), ("2A", 46, 2600)]
_INTERCITY = [("CC", 110, 400), ("2S", 108, 180)]
_PREMIUM_WITH_SL = [("1A", 24, 5200), ("2A", 54, 3100), ("3A", 72, 2200), ("SL", 72, 650)]


_CLASS_LAYOUT = {
    # Rajdhani / Duronto AC-only
    "12951": _PREMIUM, "12952": _PREMIUM, "12302": _PREMIUM, "12301": _PREMIUM,
    "12309": _PREMIUM, "22691": _PREMIUM, "12423": _PREMIUM, "12437": _PREMIUM,
    "12259": _DURONTO, "12267": _DURONTO,
    # Shatabdi day trains
    "12002": _SHATABDI, "12001": _SHATABDI, "12029": _SHATABDI, "12011": _SHATABDI,
    "12007": _SHATABDI, "12243": _SHATABDI,
    # Intercity
    "12123": _INTERCITY, "12125": _INTERCITY, "12009": _INTERCITY,
    # Standard expresses
    "12621": _EXPRESS, "12627": _EXPRESS, "12137": _EXPRESS, "12133": _EXPRESS,
    "12723": _EXPRESS, "12616": _EXPRESS, "12841": _EXPRESS, "12840": _EXPRESS,
    "12471": _EXPRESS, "12555": _EXPRESS, "12559": _EXPRESS,
    "12275": _EXPRESS, "17016": _EXPRESS, "12728": _EXPRESS, "12760": _EXPRESS,
    "12677": _EXPRESS, "12659": _EXPRESS, "12645": _EXPRESS,
    "12962": _EXPRESS, "12909": _EXPRESS, "12724": _EXPRESS,
    # Metro-to-metro fillers
    "16529": _EXPRESS, "11013": _EXPRESS, "11301": _EXPRESS,
    "12639": _INTERCITY, "12640": _INTERCITY,
    "12863": _EXPRESS, "12864": _EXPRESS,
    "22692": _PREMIUM, "12215": _EXPRESS, "12297": _DURONTO,
}


def _build_coaches():
    coaches = []
    for train_number, layout in _CLASS_LAYOUT.items():
        for cls, seats, fare in layout:
            coaches.append((train_number, cls, seats, fare))
    return coaches


COACHES = _build_coaches()


def seed() -> None:
    db: Session = SessionLocal()
    try:
        if db.query(Station).count() == 0:
            db.add_all([Station(code=c, name=n, city=city) for c, n, city in STATIONS])
            db.commit()

        existing_stations = {s.code for s in db.query(Station).all()}
        if db.query(Train).count() == 0:
            db.add_all(
                [
                    Train(
                        number=num,
                        name=name,
                        source_code=src,
                        destination_code=dst,
                        departure_time=dep,
                        arrival_time=arr,
                        duration_minutes=dur,
                        runs_on="MTWTFSS",
                    )
                    for num, name, src, dst, dep, arr, dur in TRAINS
                    if src in existing_stations and dst in existing_stations
                ]
            )
            db.commit()

        if db.query(Coach).count() == 0:
            existing_trains = {t.number for t in db.query(Train).all()}
            db.add_all(
                [
                    Coach(train_number=tn, class_code=cc, total_seats=seats, base_fare=fare)
                    for tn, cc, seats, fare in COACHES
                    if tn in existing_trains
                ]
            )
            db.commit()
    finally:
        db.close()
