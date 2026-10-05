from datetime import date

from pydantic import BaseModel, Field

PARTIES = ("solo", "couple", "family", "group")
BUDGETS = ("low", "mid", "high")


class WizardState(BaseModel):
    csrf: str
    start_date: date | None = None
    end_date: date | None = None
    party: str | None = None
    interests: list[str] = Field(default_factory=list)
    interests_done: bool = False
    budget: str | None = None
    wishes: str = ""
    wishes_done: bool = False

    @property
    def days(self) -> int:
        if not self.start_date or not self.end_date:
            return 0
        return (self.end_date - self.start_date).days + 1


class Slot(BaseModel):
    time: str = Field(max_length=20)
    venue_id: int
    note: str = Field(default="", max_length=600)


class ItineraryDay(BaseModel):
    day: int
    title: str = Field(default="", max_length=200)
    slots: list[Slot] = Field(default_factory=list)


class Itinerary(BaseModel):
    title: str = Field(default="", max_length=200)
    summary: str = Field(default="", max_length=1500)
    days: list[ItineraryDay]
