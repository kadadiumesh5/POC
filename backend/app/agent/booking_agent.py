"""IRCTC BookingAgent — a conversational assistant for Indian Railway ticket booking.

Features:
  - Greetings and personality (IRCTC customer service tone)
  - Multi-turn conversation with session memory
  - FAQ handling (tatkal, cancellation, berth, payment, etc.)
  - Train search with recommendations
  - Availability check with fare comparison
  - Full booking and cancellation flow
  - Station and train info queries
  - Contextual follow-ups and proactive suggestions
"""

from __future__ import annotations

import random
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.agent import intents, tools
from app.agent.session import store as session_store
from app.exceptions import AgentError, PlatformError
from app.repositories.train_repository import TrainRepository
from app.schemas.agent import AgentChatResponse


# --- Greeting responses ---
_GREETINGS = [
    "Namaste! Welcome to IRCTC. I'm your booking assistant.\n\nI can help you with:\n"
    "  🚂 Search & book train tickets\n  📋 Check PNR status\n"
    "  ❌ Cancel bookings\n  ℹ️ Train info & FAQs\n\nHow can I help you today?",

    "Hello! Welcome to Indian Railways booking service.\n\nTry saying:\n"
    "  • \"trains from Delhi to Mumbai tomorrow\"\n"
    "  • \"check PNR 1000000001\"\n  • \"book ticket\"\n\nWhat would you like to do?",

    "Hi there! I'm your IRCTC assistant, ready to help you plan your journey.\n\n"
    "Just tell me where you want to go, and I'll find the best trains for you!",
]

_THANKS_RESPONSES = [
    "You're welcome! Happy journey! 🚂 Let me know if you need anything else.",
    "Glad I could help! Have a safe and comfortable journey. Feel free to reach out anytime.",
    "My pleasure! If you need any help with your booking later, I'm always here.",
]

_UNKNOWN_RESPONSES = [
    "I'm not sure I understood that. Here's what I can help with:\n\n"
    "  🔍 **Search trains**: \"trains from Delhi to Mumbai on 2026-11-01\"\n"
    "  📋 **PNR status**: \"check PNR 1000000001\"\n"
    "  🎫 **Book ticket**: \"book 12951 from NDLS to BCT on 2026-11-01 in 3A for Umesh M 32\"\n"
    "  ❌ **Cancel**: \"cancel PNR 1000000001\"\n"
    "  ❓ **FAQ**: \"tatkal rules\", \"cancellation policy\", \"berth preference\"",

    "I didn't quite catch that. Could you rephrase? You can ask me about:\n"
    "  • Train search and booking\n  • PNR status\n  • Cancellation and refunds\n"
    "  • Tatkal booking rules\n  • General railway FAQ",
]

# --- FAQ knowledge base ---
_FAQ_ANSWERS = {
    "tatkal": (
        "**Tatkal Booking Rules:**\n\n"
        "• **AC classes (1A/2A/3A)**: Booking opens at **10:00 AM**, one day before journey\n"
        "• **Non-AC classes (SL/2S)**: Booking opens at **11:00 AM**, one day before journey\n"
        "• **Tatkal charges**: Additional 10-30% over base fare depending on class\n"
        "• **No cancellation** allowed for confirmed Tatkal tickets\n"
        "• **Max 4 passengers** per PNR in Tatkal quota\n"
        "• **ID proof mandatory** — original must be carried during journey\n\n"
        "💡 Tip: Keep your passenger details ready before Tatkal window opens!"
    ),
    "senior_discount": (
        "**Senior Citizen Concession:**\n\n"
        "• **Male passengers (60+)**: 40% discount on base fare\n"
        "• **Female passengers (58+)**: 50% discount on base fare\n"
        "• Applicable on all classes: SL, 3A, 2A, 1A, CC\n"
        "• **Not applicable** on Tatkal, Premium Tatkal, and Suvidha trains\n"
        "• Discount is auto-applied based on age during booking\n\n"
        "In our system, passengers aged 60+ automatically get a 40% discount."
    ),
    "child_discount": (
        "**Child Fare Policy:**\n\n"
        "• **Children below 5 years**: Travel FREE (no separate berth)\n"
        "• **Children 5-11 years**: 50% of adult fare (separate berth allotted)\n"
        "• **12 years and above**: Full adult fare\n\n"
        "In our system, passengers under 12 automatically get a 50% discount."
    ),
    "cancellation": (
        "**Cancellation & Refund Policy:**\n\n"
        "| Time Before Departure | Refund |\n"
        "|---|---|\n"
        "| More than 48 hours | **90%** of fare |\n"
        "| 12 to 48 hours | **50%** of fare |\n"
        "| 4 to 12 hours | **25%** of fare |\n"
        "| Less than 4 hours | **No refund** |\n\n"
        "• Tatkal confirmed tickets: **No cancellation** allowed\n"
        "• RAC/Waitlisted Tatkal: Cancellation allowed with clerkage charge\n"
        "• Refund is processed to the original payment method\n\n"
        "To cancel, say: **\"cancel PNR <your-pnr-number>\"**"
    ),
    "rac_wl": (
        "**RAC & Waitlist Explained:**\n\n"
        "• **CNF (Confirmed)**: Full berth allotted\n"
        "• **RAC (Reservation Against Cancellation)**: Shared berth — "
        "2 passengers share one berth. Gets confirmed if someone cancels\n"
        "• **WL (Waitlist)**: No berth. You may board only if status changes to RAC/CNF "
        "before chart preparation\n\n"
        "**Chart preparation** typically happens 4 hours before departure.\n"
        "If still on WL at chart time, ticket is auto-cancelled with full refund."
    ),
    "berth": (
        "**Berth Types in Indian Railways:**\n\n"
        "**Sleeper (SL) / AC 3-Tier (3A):**\n"
        "  • Lower Berth (LB) — most preferred, easy to sit\n"
        "  • Middle Berth (MB) — folds up during day\n"
        "  • Upper Berth (UB) — topmost, most private\n"
        "  • Side Lower (SL) — by the corridor, converts to seat\n"
        "  • Side Upper (SU) — above side lower\n\n"
        "**AC 2-Tier (2A):**\n"
        "  • Lower Berth, Upper Berth, Side Lower, Side Upper\n\n"
        "**Tips:**\n"
        "  • Senior citizens (60+) get **priority for Lower Berth**\n"
        "  • Ladies traveling alone get preference for Lower Berth\n"
        "  • You can set preference during booking, but it's not guaranteed"
    ),
    "id_proof": (
        "**ID Proof Requirements:**\n\n"
        "Any ONE of the following (original) must be carried:\n"
        "  • Aadhaar Card / e-Aadhaar\n  • Passport\n  • PAN Card\n"
        "  • Voter ID\n  • Driving License\n  • Student ID (for students)\n"
        "  • Senior Citizen concession card\n\n"
        "⚠️ **Photocopy not accepted** — original document required\n"
        "⚠️ For Tatkal tickets, same ID used during booking must be carried"
    ),
    "eticket": (
        "**E-Ticket Information:**\n\n"
        "• E-tickets are sent to your registered email\n"
        "• Show the e-ticket (print or mobile) along with original ID proof\n"
        "• E-ticket is valid only for the passenger whose name is printed\n"
        "• Take a screenshot/printout in case of no network on train\n"
        "• PNR number is your unique booking reference"
    ),
    "how_to_book": (
        "**How to Book a Ticket:**\n\n"
        "**Quick way — just tell me:**\n"
        "  \"book 12951 from NDLS to BCT on 2026-11-01 in 3A for Umesh M 32\"\n\n"
        "**Step-by-step:**\n"
        "  1️⃣ Search: \"trains from Delhi to Mumbai on 2026-11-01\"\n"
        "  2️⃣ I'll show available trains with classes and fares\n"
        "  3️⃣ Book: \"book <train-number> in <class> for <Name Gender Age>\"\n"
        "  4️⃣ I'll confirm your booking with a PNR number\n\n"
        "You can also book through the **website interface** — click 'Book Ticket' on the homepage!"
    ),
    "payment": (
        "**Payment Methods Supported:**\n\n"
        "  💳 Credit/Debit Cards (Visa, Mastercard, RuPay)\n"
        "  🏦 Net Banking (all major banks)\n"
        "  📱 UPI (Google Pay, PhonePe, Paytm, BHIM)\n"
        "  💰 Mobile Wallets (Paytm, Amazon Pay, Mobikwik)\n"
        "  🏧 IRCTC iPay\n\n"
        "All payments are secured with 256-bit encryption."
    ),
    "catering": (
        "**E-Catering Service:**\n\n"
        "• Order food from restaurants at upcoming stations\n"
        "• Available on select trains and stations\n"
        "• Delivery right to your seat/berth\n"
        "• Multiple cuisines available: North Indian, South Indian, Chinese, etc.\n"
        "• Order through IRCTC e-Catering website or app\n"
        "• Helpline: 1323 (for food-related complaints)"
    ),
    "platform_info": (
        "**Platform & Coach Position:**\n\n"
        "• Platform number is displayed at the station on the indicator board\n"
        "• Coach position charts are displayed on platforms\n"
        "• Check the IRCTC app or website for real-time platform info\n"
        "• Arrive at least **30 minutes** before departure for long-distance trains\n"
        "• Coach composition may vary — always check the display board"
    ),
    "luggage": (
        "**Luggage Allowance:**\n\n"
        "| Class | Free Allowance |\n"
        "|---|---|\n"
        "| AC First (1A) | 70 kg |\n"
        "| AC 2 Tier (2A) | 50 kg |\n"
        "| AC 3 Tier (3A) | 40 kg |\n"
        "| Sleeper (SL) | 40 kg |\n"
        "| Chair Car (CC) | 15 kg |\n"
        "| Second Sitting (2S) | 15 kg |\n\n"
        "⚠️ No single piece should exceed 40 kg\n"
        "⚠️ Excess luggage is charged per kg"
    ),
}


HELP_TEXT = (
    "🚂 **IRCTC Booking Assistant — Here's what I can do:**\n\n"
    "**🔍 Search Trains**\n"
    "  \"trains from Delhi to Mumbai tomorrow\"\n"
    "  \"find trains from NDLS to BCT on 2026-11-01\"\n\n"
    "**🎫 Book Tickets**\n"
    "  \"book 12951 from NDLS to BCT on 2026-11-01 in 3A for Umesh M 32\"\n"
    "  \"book ticket\" (I'll ask for details step by step)\n\n"
    "**📋 PNR Status**\n"
    "  \"check PNR 1000000001\"\n"
    "  \"pnr status 1000000001\"\n\n"
    "**💰 Fare Enquiry**\n"
    "  \"fare for train 12951 in 3A\"\n"
    "  \"how much does 12951 cost\"\n\n"
    "**❌ Cancel Booking**\n"
    "  \"cancel PNR 1000000001\"\n\n"
    "**ℹ️ Information & FAQ**\n"
    "  \"tatkal rules\", \"cancellation policy\"\n"
    "  \"berth types\", \"senior citizen discount\"\n"
    "  \"luggage limit\", \"ID proof required\"\n\n"
    "**💡 Tips:**\n"
    "  • I remember your recent searches — just say \"book\" after searching\n"
    "  • Use station codes (NDLS, BCT) or city names (Delhi, Mumbai)\n"
    "  • Say \"tomorrow\" or \"next Monday\" instead of dates"
)


class BookingAgent:
    def __init__(self, db: Session):
        self.db = db
        self._station_repo = TrainRepository(db)
        self._dispatch = {
            intents.INTENT_SEARCH: self._handle_search,
            intents.INTENT_AVAILABILITY: self._handle_availability,
            intents.INTENT_BOOK: self._handle_book,
            intents.INTENT_CANCEL: self._handle_cancel,
            intents.INTENT_GET: self._handle_get,
            intents.INTENT_PNR_STATUS: self._handle_pnr_status,
            intents.INTENT_LIVE_STATUS: self._handle_live_status,
            intents.INTENT_HELP: self._handle_help,
            intents.INTENT_GREETING: self._handle_greeting,
            intents.INTENT_THANKS: self._handle_thanks,
            intents.INTENT_FAQ: self._handle_faq,
            intents.INTENT_FARE_ENQUIRY: self._handle_fare_enquiry,
            intents.INTENT_STATION_INFO: self._handle_station_info,
            intents.INTENT_TRAIN_INFO: self._handle_train_info,
        }

    def chat(self, message: str, session_id: str | None = None) -> AgentChatResponse:
        session_store.add_message(session_id, "user", message)
        intent = intents.parse(message)

        if intent.name == intents.INTENT_UNKNOWN:
            reply = random.choice(_UNKNOWN_RESPONSES)
            session_store.add_message(session_id, "assistant", reply, intent.name)
            return AgentChatResponse(intent=intent.name, reply=reply)

        # For intents that don't need slots, dispatch directly
        if intent.name in (intents.INTENT_GREETING, intents.INTENT_THANKS,
                           intents.INTENT_HELP, intents.INTENT_FAQ,
                           intents.INTENT_STATION_INFO):
            handler = self._dispatch[intent.name]
            response = handler(intent.slots)
            session_store.add_message(session_id, "assistant", response.reply, intent.name)
            session_store.set_last_intent(session_id, intent.name)
            return response

        # Apply session memory for slot-based intents
        session = session_store.get(session_id)
        remembered = session.slots
        intent.slots, intent.missing = _apply_memory(intent.name, intent.slots, intent.missing, remembered)

        if intent.missing:
            session_store.merge(session_id, intent.slots)
            session_store.set_last_intent(session_id, intent.name)
            reply = self._build_missing_prompt(intent, remembered)
            session_store.add_message(session_id, "assistant", reply, intent.name)
            return AgentChatResponse(
                intent=intent.name,
                reply=reply,
                data={"slots": _jsonable(intent.slots), "missing": intent.missing},
            )

        handler = self._dispatch[intent.name]
        try:
            response = handler(intent.slots)
        except PlatformError as exc:
            raise AgentError(exc.message) from exc

        session_store.merge(session_id, intent.slots)
        session_store.set_last_intent(session_id, intent.name)
        if isinstance(response.data, dict) and "pnr" in response.data:
            session_store.merge(session_id, {"pnr": response.data["pnr"]})

        session_store.add_message(session_id, "assistant", response.reply, intent.name)
        return response

    def _pretty(self, code: str) -> str:
        station = self._station_repo.get_station(code)
        if station is None:
            return code
        return f"{station.city} ({station.code})"

    def _build_missing_prompt(self, intent, remembered: dict) -> str:
        """Build a user-friendly prompt asking for missing information."""
        field_labels = {
            "source": "departure station (e.g., NDLS or New Delhi)",
            "destination": "arrival station (e.g., BCT or Mumbai)",
            "travel_date": "travel date (e.g., 2026-11-01 or tomorrow)",
            "train_number": "train number (5-digit, e.g., 12951)",
            "class_code": "class (SL, 3A, 2A, 1A, CC)",
            "passenger": "passenger details (e.g., Umesh M 32)",
            "pnr": "PNR number (10-digit)",
        }

        missing_labels = [field_labels.get(m, m) for m in intent.missing]

        mem_bits = []
        for key in ("source", "destination", "travel_date", "train_number", "class_code"):
            if key in intent.slots:
                mem_bits.append(f"**{key}**: {intent.slots[key]}")

        reply = f"I need a few more details to proceed:\n\n"
        for label in missing_labels:
            reply += f"  • {label}\n"

        if mem_bits:
            reply += f"\n✅ I already have: {', '.join(mem_bits)}"

        return reply

    # --- Intent handlers ---

    def _handle_greeting(self, _slots: dict[str, Any]) -> AgentChatResponse:
        return AgentChatResponse(intent=intents.INTENT_GREETING, reply=random.choice(_GREETINGS))

    def _handle_thanks(self, _slots: dict[str, Any]) -> AgentChatResponse:
        return AgentChatResponse(intent=intents.INTENT_THANKS, reply=random.choice(_THANKS_RESPONSES))

    def _handle_help(self, _slots: dict[str, Any]) -> AgentChatResponse:
        return AgentChatResponse(intent=intents.INTENT_HELP, reply=HELP_TEXT)

    def _handle_faq(self, slots: dict[str, Any]) -> AgentChatResponse:
        faq_key = slots.get("faq_key", "")
        answer = _FAQ_ANSWERS.get(faq_key, "I don't have information on that topic. Try asking about tatkal, cancellation policy, berth types, or senior citizen discounts.")
        return AgentChatResponse(intent=intents.INTENT_FAQ, reply=answer, data={"faq_key": faq_key})

    def _handle_station_info(self, slots: dict[str, Any]) -> AgentChatResponse:
        stations = self._station_repo.list_stations()
        cities = {}
        for s in stations:
            cities.setdefault(s.city, []).append(f"{s.code} ({s.name})")

        lines = []
        for city in sorted(cities.keys()):
            codes = ", ".join(cities[city])
            lines.append(f"  **{city}**: {codes}")

        reply = f"🏙️ **Available Stations ({len(stations)} total):**\n\n" + "\n".join(lines)
        reply += "\n\n💡 You can use either the station code (NDLS) or city name (Delhi) when searching."
        return AgentChatResponse(
            intent=intents.INTENT_STATION_INFO,
            reply=reply,
            data=[{"code": s.code, "name": s.name, "city": s.city} for s in stations],
        )

    def _handle_train_info(self, slots: dict[str, Any]) -> AgentChatResponse:
        train = self._station_repo.get_train(slots["train_number"])
        if not train:
            return AgentChatResponse(
                intent=intents.INTENT_TRAIN_INFO,
                reply=f"Train {slots['train_number']} not found in our database.",
            )

        coaches = self._station_repo.list_coaches(train.number)
        hrs, mins = divmod(train.duration_minutes, 60)

        classes_info = "\n".join(
            f"  • **{c.class_code}**: {c.total_seats} seats, ₹{c.base_fare:,.0f}"
            for c in coaches
        )

        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        runs = ", ".join(d for d, r in zip(days, train.runs_on) if r != "-")

        reply = (
            f"🚂 **{train.name}** (#{train.number})\n\n"
            f"**Route:** {self._pretty(train.source_code)} → {self._pretty(train.destination_code)}\n"
            f"**Departure:** {train.departure_time} | **Arrival:** {train.arrival_time}\n"
            f"**Duration:** {hrs}h {mins}m\n"
            f"**Runs on:** {runs}\n\n"
            f"**Classes & Fares:**\n{classes_info}\n\n"
            f"💡 To check availability, say: \"availability {train.number} in 3A on 2026-11-01\""
        )

        return AgentChatResponse(
            intent=intents.INTENT_TRAIN_INFO,
            reply=reply,
            data=_train_dict(train),
            actions_taken=["train_info"],
        )

    def _handle_fare_enquiry(self, slots: dict[str, Any]) -> AgentChatResponse:
        train_number = slots.get("train_number")
        class_code = slots.get("class_code")

        if train_number:
            train = self._station_repo.get_train(train_number)
            if not train:
                return AgentChatResponse(
                    intent=intents.INTENT_FARE_ENQUIRY,
                    reply=f"Train {train_number} not found.",
                )

            coaches = self._station_repo.list_coaches(train_number)
            if class_code:
                coaches = [c for c in coaches if c.class_code == class_code.upper()]

            if not coaches:
                return AgentChatResponse(
                    intent=intents.INTENT_FARE_ENQUIRY,
                    reply=f"Class {class_code} is not available on train {train_number}.",
                )

            lines = []
            for c in coaches:
                child_fare = round(c.base_fare * 0.5)
                senior_fare = round(c.base_fare * 0.6)
                lines.append(
                    f"  **{c.class_code}**: ₹{c.base_fare:,.0f} "
                    f"(child: ₹{child_fare:,}, senior: ₹{senior_fare:,})"
                )

            reply = (
                f"💰 **Fare for {train.name} (#{train_number})**\n"
                f"Route: {self._pretty(train.source_code)} → {self._pretty(train.destination_code)}\n\n"
                + "\n".join(lines)
                + "\n\n*Child (under 12): 50% discount | Senior (60+): 40% discount*"
            )
        else:
            reply = "Please specify a train number for fare enquiry. Example: \"fare for 12951 in 3A\""

        return AgentChatResponse(intent=intents.INTENT_FARE_ENQUIRY, reply=reply)

    def _handle_search(self, slots: dict[str, Any]) -> AgentChatResponse:
        trains = tools.tool_search_trains(
            self.db, slots["source"], slots["destination"], slots["travel_date"]
        )
        if not trains:
            reply = (
                f"😔 No trains found from **{slots['source']}** to **{slots['destination']}** "
                f"on **{slots['travel_date']}**.\n\n"
                f"💡 Try:\n  • A different date\n  • Nearby stations\n"
                f"  • Checking if the train runs on this day of the week"
            )
        else:
            lines = []
            for idx, t in enumerate(trains, 1):
                hrs, mins = divmod(t.duration_minutes, 60)
                coaches = self._station_repo.list_coaches(t.number)
                classes = ", ".join(c.class_code for c in coaches) or "—"
                cheapest = min((c.base_fare for c in coaches), default=0)
                lines.append(
                    f"  **{idx}. {t.name}** (#{t.number})\n"
                    f"     {self._pretty(t.source_code)} **{t.departure_time}** → "
                    f"{self._pretty(t.destination_code)} **{t.arrival_time}** "
                    f"({hrs}h {mins}m)\n"
                    f"     Classes: {classes} | From ₹{cheapest:,.0f}"
                )

            # Recommend fastest train
            fastest = min(trains, key=lambda t: t.duration_minutes)
            fh, fm = divmod(fastest.duration_minutes, 60)

            reply = (
                f"🚂 Found **{len(trains)} train(s)** from **{slots['source']}** to "
                f"**{slots['destination']}** on **{slots['travel_date']}**:\n\n"
                + "\n\n".join(lines)
                + f"\n\n⭐ **Recommended:** {fastest.name} (#{fastest.number}) — fastest at {fh}h {fm}m"
                + "\n\n💡 **Next steps:**\n"
                + "  • Check availability: \"availability <train#> in <class>\"\n"
                + "  • Book directly: \"book <train#> in <class> for <Name Gender Age>\""
            )

        return AgentChatResponse(
            intent=intents.INTENT_SEARCH,
            reply=reply,
            data=[_train_dict(t) for t in trains],
            actions_taken=["search_trains"],
        )

    def _handle_availability(self, slots: dict[str, Any]) -> AgentChatResponse:
        info = tools.tool_check_availability(
            self.db, slots["train_number"], slots["class_code"], slots["travel_date"]
        )
        train = self._station_repo.get_train(info["train_number"])
        route = f"{self._pretty(train.source_code)} → {self._pretty(train.destination_code)}" if train else ""

        status_emoji = "✅" if info["status"] == "AVAILABLE" else "🟡" if info["status"] == "RAC" else "🔴"
        status_text = {
            "AVAILABLE": f"Available — {info['available']} seats",
            "RAC": "RAC (Reservation Against Cancellation)",
            "WL": "Waitlisted",
        }.get(info["status"], info["status"])

        reply = (
            f"{status_emoji} **{info['class_code']} on {info['train_number']}** — {route}\n"
            f"📅 Date: {info['travel_date']}\n\n"
            f"**Status:** {status_text}\n"
            f"**Fare:** ₹{info['fare']:,.0f} per person\n"
            f"**Seats:** {info['available']}/{info['total_seats']}\n"
        )

        if info["status"] == "AVAILABLE":
            reply += f"\n💡 Ready to book? Say: \"book {info['train_number']} in {info['class_code']} for <Name M Age>\""
        elif info["status"] == "RAC":
            reply += "\n⚠️ Only RAC available. You'll get a shared berth, confirmed if someone cancels."
        else:
            reply += "\n⚠️ Waitlisted. Consider an alternate train or date."

        return AgentChatResponse(
            intent=intents.INTENT_AVAILABILITY,
            reply=reply,
            data=_jsonable(info),
            actions_taken=["check_availability"],
        )

    def _handle_book(self, slots: dict[str, Any]) -> AgentChatResponse:
        booking = tools.tool_book_ticket(
            self.db,
            train_number=slots["train_number"],
            source=slots["source"],
            destination=slots["destination"],
            travel_date=slots["travel_date"],
            class_code=slots["class_code"],
            passengers=slots["passengers"],
        )

        pax_lines = []
        for p in booking.passengers:
            pax_lines.append(f"  • {p.name} ({p.gender}/{p.age}y) — Seat: **{p.seat_number}** [{p.status}]")

        reply = (
            f"✅ **Booking Confirmed!**\n\n"
            f"**PNR:** `{booking.pnr}`\n"
            f"**Train:** {booking.train_number} — {self._pretty(booking.source_code)} → "
            f"{self._pretty(booking.destination_code)}\n"
            f"**Date:** {booking.travel_date} | **Class:** {booking.class_code}\n\n"
            f"**Passengers:**\n" + "\n".join(pax_lines) + "\n\n"
            f"**Total Fare:** ₹{booking.total_fare:,.0f} | **Payment:** {booking.payment_status}\n\n"
            f"📋 Check status anytime: \"PNR status {booking.pnr}\"\n"
            f"❌ To cancel: \"cancel PNR {booking.pnr}\"\n\n"
            f"🚂 Have a pleasant journey!"
        )

        return AgentChatResponse(
            intent=intents.INTENT_BOOK,
            reply=reply,
            data=_booking_dict(booking),
            actions_taken=["check_availability", "book_ticket", "charge_payment"],
        )

    def _handle_cancel(self, slots: dict[str, Any]) -> AgentChatResponse:
        result = tools.tool_cancel_booking(self.db, slots["pnr"])
        reply = (
            f"❌ **Booking Cancelled**\n\n"
            f"**PNR:** {result['pnr']}\n"
            f"**Refund Amount:** ₹{result['refund_amount']:,.0f}\n"
            f"**Status:** {result['status']}\n\n"
            f"💰 Refund will be processed to your original payment method within 5-7 business days."
        )
        return AgentChatResponse(
            intent=intents.INTENT_CANCEL,
            reply=reply,
            data=result,
            actions_taken=["cancel_booking", "refund_payment"],
        )

    def _handle_pnr_status(self, slots: dict[str, Any]) -> AgentChatResponse:
        info = tools.tool_pnr_status(self.db, slots["pnr"])

        status_emoji = {"CONFIRMED": "✅", "CANCELLED": "❌", "RAC": "🟡", "WL": "🔴"}.get(
            info.get("status", ""), "ℹ️"
        )

        pax_lines = []
        for p in info.get("passengers", []):
            pax_lines.append(f"  • {p['name']} ({p['gender']}/{p['age']}y) — **{p['status']}** Seat: {p.get('seat_number', '-')}")

        reply = (
            f"📋 **PNR Status: {slots['pnr']}**\n\n"
            f"{status_emoji} **Status:** {info.get('status', 'UNKNOWN')}\n"
            f"**Train:** {info.get('train_number', '-')}\n"
            f"**Route:** {info.get('source_code', '-')} → {info.get('destination_code', '-')}\n"
            f"**Date:** {info.get('travel_date', '-')} | **Class:** {info.get('class_code', '-')}\n"
        )

        if pax_lines:
            reply += f"\n**Passengers:**\n" + "\n".join(pax_lines)

        reply += f"\n\n**Total Fare:** ₹{info.get('total_fare', 0):,.0f}"

        if info.get("status") == "CONFIRMED":
            reply += "\n\n🎉 Your ticket is confirmed. Have a great journey!"
        elif info.get("status") == "CANCELLED":
            reply += "\n\nThis booking has been cancelled."

        return AgentChatResponse(
            intent=intents.INTENT_PNR_STATUS,
            reply=reply,
            data=info,
            actions_taken=["pnr_status"],
        )

    def _handle_live_status(self, slots: dict[str, Any]) -> AgentChatResponse:
        try:
            info = tools.tool_live_status(self.db, slots["train_number"])
            reply = f"📍 Live status for train {slots['train_number']} fetched."
        except PlatformError:
            raise
        except Exception:
            reply = (
                f"📍 Live train status for **{slots['train_number']}** is not available in demo mode.\n\n"
                f"In production, this would show real-time running status from the IRCTC API.\n"
                f"💡 You can check train info instead: \"train info {slots['train_number']}\""
            )
            info = {"message": "Live status unavailable in demo mode"}
        return AgentChatResponse(
            intent=intents.INTENT_LIVE_STATUS,
            reply=reply,
            data=info,
            actions_taken=["live_status"],
        )

    def _handle_get(self, slots: dict[str, Any]) -> AgentChatResponse:
        booking = tools.tool_get_booking(self.db, slots["pnr"])

        pax_lines = []
        for p in booking.passengers:
            pax_lines.append(f"  • {p.name} ({p.gender}/{p.age}y) — Seat: {p.seat_number or '-'} [{p.status}]")

        status_emoji = {"CONFIRMED": "✅", "CANCELLED": "❌"}.get(booking.status, "ℹ️")

        reply = (
            f"📄 **Booking Details — PNR {booking.pnr}**\n\n"
            f"{status_emoji} **Status:** {booking.status}\n"
            f"**Train:** {booking.train_number} — "
            f"{self._pretty(booking.source_code)} → {self._pretty(booking.destination_code)}\n"
            f"**Date:** {booking.travel_date} | **Class:** {booking.class_code}\n\n"
            f"**Passengers:**\n" + "\n".join(pax_lines) + "\n\n"
            f"**Total Fare:** ₹{booking.total_fare:,.0f} | **Payment:** {booking.payment_status}"
        )

        return AgentChatResponse(
            intent=intents.INTENT_GET,
            reply=reply,
            data=_booking_dict(booking),
            actions_taken=["get_booking"],
        )


# --- Serializers ---

def _train_dict(t) -> dict:
    return {
        "number": t.number,
        "name": t.name,
        "source_code": t.source_code,
        "destination_code": t.destination_code,
        "departure_time": t.departure_time,
        "arrival_time": t.arrival_time,
        "duration_minutes": t.duration_minutes,
    }


def _booking_dict(b) -> dict:
    return {
        "pnr": b.pnr,
        "train_number": b.train_number,
        "source_code": b.source_code,
        "destination_code": b.destination_code,
        "travel_date": b.travel_date.isoformat(),
        "class_code": b.class_code,
        "total_fare": b.total_fare,
        "status": b.status,
        "payment_status": b.payment_status,
        "passengers": [
            {"name": p.name, "age": p.age, "gender": p.gender, "seat_number": p.seat_number, "status": p.status}
            for p in b.passengers
        ],
    }


# --- Memory helpers ---

_SLOTS_PER_INTENT = {
    intents.INTENT_SEARCH:       ["source", "destination", "travel_date"],
    intents.INTENT_AVAILABILITY: ["train_number", "class_code", "travel_date"],
    intents.INTENT_BOOK:         ["train_number", "source", "destination", "travel_date", "class_code", "passengers"],
    intents.INTENT_CANCEL:       ["pnr"],
    intents.INTENT_GET:          ["pnr"],
    intents.INTENT_PNR_STATUS:   ["pnr"],
    intents.INTENT_LIVE_STATUS:  ["train_number"],
    intents.INTENT_FARE_ENQUIRY: ["train_number"],
    intents.INTENT_TRAIN_INFO:   ["train_number"],
}


def _apply_memory(intent_name: str, slots: dict, missing: list[str], remembered: dict) -> tuple[dict, list[str]]:
    required = _SLOTS_PER_INTENT.get(intent_name, [])
    merged = dict(slots)
    for key in required:
        if key not in merged and key in remembered:
            merged[key] = remembered[key]
    new_missing = [m for m in missing if m not in merged]
    if "passenger" in new_missing and merged.get("passengers"):
        new_missing.remove("passenger")
    return merged, new_missing


def _jsonable(value):
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value
