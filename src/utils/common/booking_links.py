"""
Booking redirect links for hotels and transport.
Generates deep-link URLs to MakeMyTrip, IRCTC, Booking.com, Goibibo, RedBus.
No API key required — pure URL construction.
"""
from datetime import date, timedelta
from urllib.parse import quote


def _fmt(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def _iso(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def hotel_links(city: str, checkin: date, checkout: date) -> list[dict]:
    city_q = quote(city)
    ci, co = _iso(checkin), _iso(checkout)
    ci_fmt, co_fmt = _fmt(checkin), _fmt(checkout)
    nights = (checkout - checkin).days or 1
    return [
        {
            "name": "Booking.com",
            "icon": "🏨",
            "url": f"https://www.booking.com/searchresults.html?ss={city_q}&checkin={ci}&checkout={co}&group_adults=1",
            "color": "#003580",
        },
        {
            "name": "MakeMyTrip",
            "icon": "🛎️",
            "url": f"https://www.makemytrip.com/hotels/hotel-listing/?checkin={ci_fmt}&checkout={co_fmt}&city={city_q}&roomCount=1&adultsCount=1",
            "color": "#e8262d",
        },
        {
            "name": "Goibibo",
            "icon": "🏩",
            "url": f"https://www.goibibo.com/hotels/hotels-in-{city.lower().replace(' ', '-')}-city/?ci={checkin.strftime('%Y%m%d')}&co={checkout.strftime('%Y%m%d')}&r=1",
            "color": "#e8262d",
        },
        {
            "name": "Google Hotels",
            "icon": "🔍",
            "url": f"https://www.google.com/travel/hotels/{city_q}?q=hotels+in+{city_q}&checkin={ci}&checkout={co}",
            "color": "#4285f4",
        },
    ]


def train_links(from_city: str, to_city: str, travel_date: date) -> list[dict]:
    f, t = quote(from_city.upper()), quote(to_city.upper())
    d = travel_date.strftime("%Y%m%d")
    return [
        {
            "name": "IRCTC",
            "icon": "🚂",
            "url": f"https://www.irctc.co.in/nget/train-search?fromStation={f}&toStation={t}&journeyDate={d}&journeyQuota=GN",
            "color": "#1a6bb5",
        },
        {
            "name": "ConfirmTkt",
            "icon": "🎫",
            "url": f"https://confirmtkt.com/train-between-stations?from={quote(from_city)}&to={quote(to_city)}&date={travel_date.strftime('%d-%m-%Y')}",
            "color": "#ff6b35",
        },
        {
            "name": "RailYatri",
            "icon": "🛤️",
            "url": f"https://www.railyatri.in/trains-between-stations?from={quote(from_city)}&to={quote(to_city)}&date={travel_date.strftime('%d%m%Y')}",
            "color": "#e84c3d",
        },
    ]


def flight_links(from_city: str, to_city: str, travel_date: date) -> list[dict]:
    f, t = quote(from_city), quote(to_city)
    d = _iso(travel_date)
    d_fmt = travel_date.strftime("%d/%m/%Y")
    return [
        {
            "name": "MakeMyTrip",
            "icon": "✈️",
            "url": f"https://www.makemytrip.com/flights/domestic-routes/{from_city.lower()}-to-{to_city.lower()}.html?departDate={d_fmt}",
            "color": "#e8262d",
        },
        {
            "name": "Goibibo",
            "icon": "✈️",
            "url": f"https://www.goibibo.com/flights/search/?source={f}&destination={t}&travelDate={travel_date.strftime('%Y%m%d')}&seatingClass=E&adults=1&children=0&infants=0&tripType=O",
            "color": "#e8262d",
        },
        {
            "name": "Google Flights",
            "icon": "🌐",
            "url": f"https://www.google.com/travel/flights?q=flights+from+{f}+to+{t}+on+{d}",
            "color": "#4285f4",
        },
        {
            "name": "Skyscanner",
            "icon": "🔎",
            "url": f"https://www.skyscanner.co.in/transport/flights/{from_city.lower()[:3]}/{to_city.lower()[:3]}/{travel_date.strftime('%y%m%d')}/",
            "color": "#0770e3",
        },
    ]


def bus_links(from_city: str, to_city: str, travel_date: date) -> list[dict]:
    f, t = quote(from_city), quote(to_city)
    d = travel_date.strftime("%d-%b-%Y")
    return [
        {
            "name": "RedBus",
            "icon": "🚌",
            "url": f"https://www.redbus.in/bus-tickets/{from_city.lower().replace(' ', '-')}-to-{to_city.lower().replace(' ', '-')}?doj={d}",
            "color": "#d84315",
        },
        {
            "name": "AbhiBus",
            "icon": "🚍",
            "url": f"https://www.abhibus.com/{from_city.lower().replace(' ', '-')}-to-{to_city.lower().replace(' ', '-')}-bus-tickets?date={travel_date.strftime('%d-%m-%Y')}",
            "color": "#ff5722",
        },
    ]


def get_booking_links(from_city: str, to_city: str, distance_km: float, travel_date: date) -> dict:
    """Return all relevant booking links for a leg based on distance."""
    links = {"train": train_links(from_city, to_city, travel_date), "bus": [], "flight": []}
    if distance_km >= 500:
        links["flight"] = flight_links(from_city, to_city, travel_date)
    if distance_km <= 500:
        links["bus"] = bus_links(from_city, to_city, travel_date)
    return links
