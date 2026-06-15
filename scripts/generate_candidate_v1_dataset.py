from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from item_reviser.constants import ERROR_CATEGORIES  # noqa: E402


OUTPUT_DIR = REPO_ROOT / "data" / "processed"
DATASET_PATH = OUTPUT_DIR / "candidate_v1_2000.jsonl"
SUMMARY_PATH = OUTPUT_DIR / "candidate_v1_2000_summary.md"
MANIFEST_PATH = OUTPUT_DIR / "candidate_v1_2000_manifest.json"
RUBRIC_PATH = OUTPUT_DIR / "candidate_v1_rubric.md"
REVIEW_QUEUE_PATH = OUTPUT_DIR / "candidate_v1_review_queue.jsonl"

SEED_DATASET_PATH = REPO_ROOT / "data" / "eval" / "test_set_200_seed.jsonl"


SUPPORT_OPTIONS = [
    "Strongly oppose",
    "Somewhat oppose",
    "Neither support nor oppose",
    "Somewhat support",
    "Strongly support",
]
SATISFACTION_OPTIONS = [
    "Very dissatisfied",
    "Somewhat dissatisfied",
    "Neither satisfied nor dissatisfied",
    "Somewhat satisfied",
    "Very satisfied",
]
FREQUENCY_OPTIONS = [
    "Never",
    "Once",
    "2-3 times",
    "About once a week",
    "Several times a week",
    "Every day",
]
AGREEMENT_OPTIONS = [
    "Strongly disagree",
    "Somewhat disagree",
    "Neither agree nor disagree",
    "Somewhat agree",
    "Strongly agree",
]
YES_NO = ["Yes", "No"]
YES_NO_PREFER = ["Yes", "No", "Prefer not to answer"]
DIFFICULTIES = ["obvious", "realistic", "borderline"]
FORMAT_CYCLE = [
    "support_oppose",
    "binary_yes_no",
    "filter_question",
    "likert_agreement",
    "frequency",
    "ordinal_categories",
    "numeric_ranges",
    "open_ended",
    "categorical_closed_ended",
]
TOPIC_CONTEXT_BASE = {
    "politics/public policy": "your own opinion about public policy",
    "health": "your own experience with health and health services",
    "education": "your own experience with education",
    "work": "your own work situation",
    "labor": "your own employment situation",
    "finances": "your own financial situation",
    "technology": "your own use of digital technology",
    "environment": "your own environmental views or practices",
    "mobility": "your own travel and mobility situation",
    "family/household": "your own household situation",
    "media/culture": "your own media and cultural habits",
    "university life": "your own university experience",
    "public services": "your own experience with public services",
    "sensitive behaviors": "your own behavior or experience",
}
CONTEXT_QUALIFIERS = [
    "as it applies to you personally",
    "in your current circumstances",
    "based on your own experience",
    "with your own situation in mind",
    "based on what you know directly",
    "based on your best estimate",
    "according to your personal opinion",
    "for the setting you know best",
    "based on the option that fits you best",
    "in relation to your everyday life",
    "based on your own judgement",
    "for your current situation",
    "based on your direct observations",
    "with no need to answer for anyone else",
    "based on what happened to you",
    "for your own case",
    "in the context most relevant to you",
    "for the place or service you use most",
    "based on your usual behavior",
    "according to your own preference",
    "for your present living situation",
    "based on your recent experience",
    "for your personal circumstances",
    "based on the option that best describes you",
    "for your normal routine",
    "based on your own interpretation",
    "for your current needs",
    "based on your direct involvement",
    "for your current role",
    "as you understand the issue",
    "based on your own records or memory",
    "for the situation you know most about",
    "based on your own answer, not others' views",
    "according to what applies now",
    "based on your personal participation",
    "for your current access or use",
    "in the context you encounter most often",
    "based on your ordinary circumstances",
    "according to your own experience",
    "for the case that applies most clearly to you",
]


@dataclass(frozen=True)
class Spec:
    slug: str
    topic: str
    target_concept: str
    phrase: str
    clean_question: str
    clean_options: tuple[str, ...]
    item_format: str
    secondary_phrase: str = ""


POLICY_SPECS: list[tuple[str, str, str]] = [
    ("politics/public policy", "public funding for local election information campaigns", "support for public election information funding"),
    ("politics/public policy", "stricter disclosure rules for online political advertising", "support for online political advertising disclosure"),
    ("health", "expanding evening clinic hours in public health centers", "support for evening clinic hours"),
    ("health", "requiring clearer nutrition labels on packaged foods", "support for clearer nutrition labels"),
    ("education", "increasing tutoring support in public schools", "support for school tutoring support"),
    ("education", "limiting smartphone use during school lessons", "support for smartphone limits in school lessons"),
    ("work", "allowing employees to work from home two days per week", "support for hybrid work arrangements"),
    ("labor", "raising the minimum wage for adult workers", "support for raising the minimum wage"),
    ("finances", "stricter consumer protection rules for payday loans", "support for payday-loan consumer protection"),
    ("finances", "tax incentives for household energy renovations", "support for energy-renovation tax incentives"),
    ("technology", "stronger privacy rules for mobile apps", "support for mobile-app privacy rules"),
    ("technology", "public oversight of high-risk AI systems", "support for public oversight of high-risk AI systems"),
    ("environment", "expanding protected urban green spaces", "support for protected urban green spaces"),
    ("environment", "charging higher fees for single-use packaging", "support for fees on single-use packaging"),
    ("mobility", "building more protected bicycle lanes in city centers", "support for protected bicycle lanes"),
    ("mobility", "reducing parking spaces near major transit stops", "support for reducing parking near transit"),
    ("family/household", "subsidized childcare for families with low incomes", "support for subsidized childcare"),
    ("family/household", "paid leave for family caregivers", "support for paid family-care leave"),
    ("media/culture", "public grants for local cultural venues", "support for grants for local cultural venues"),
    ("media/culture", "age ratings for short-form video platforms", "support for age ratings on short-form video platforms"),
    ("university life", "expanding mental health counseling at universities", "support for university mental health counseling"),
    ("university life", "making lecture recordings available after class", "support for lecture recordings"),
    ("public services", "online booking for municipal appointments", "support for online municipal appointment booking"),
    ("public services", "longer opening hours for citizen service offices", "support for longer citizen-service opening hours"),
    ("sensitive behaviors", "anonymous counseling for gambling problems", "support for anonymous gambling counseling"),
    ("health", "free influenza vaccination at workplaces", "support for workplace influenza vaccination"),
    ("education", "more needs-based grants for vocational training", "support for needs-based vocational grants"),
    ("labor", "stronger enforcement of workplace safety rules", "support for workplace safety enforcement"),
    ("technology", "clear labeling of AI-generated media", "support for labeling AI-generated media"),
    ("environment", "financial support for replacing old heating systems", "support for heating-system replacement support"),
    ("mobility", "discounted monthly passes for regional public transport", "support for discounted regional transit passes"),
    ("public services", "plain-language letters from tax offices", "support for plain-language tax-office letters"),
]


SATISFACTION_SPECS: list[tuple[str, str, str]] = [
    ("public services", "the clarity of digital government forms", "satisfaction with digital government forms"),
    ("mobility", "the punctuality of local public transport", "satisfaction with public transport punctuality"),
    ("health", "the availability of appointments with family doctors", "satisfaction with family-doctor appointment availability"),
    ("education", "the feedback students receive on assignments", "satisfaction with assignment feedback"),
    ("work", "the flexibility of your current working hours", "satisfaction with working-hour flexibility"),
    ("labor", "the fairness of scheduling at your workplace", "satisfaction with workplace scheduling fairness"),
    ("finances", "the transparency of fees charged by your main bank", "satisfaction with bank-fee transparency"),
    ("technology", "the control you have over privacy settings in apps", "satisfaction with app privacy controls"),
    ("environment", "the cleanliness of public parks near your home", "satisfaction with local park cleanliness"),
    ("family/household", "the availability of childcare in your area", "satisfaction with childcare availability"),
    ("media/culture", "the diversity of cultural events in your area", "satisfaction with local cultural diversity"),
    ("university life", "the process for registering for courses", "satisfaction with course registration"),
    ("public services", "the waiting time at citizen service offices", "satisfaction with citizen-service waiting time"),
    ("health", "the information provided before medical appointments", "satisfaction with pre-appointment medical information"),
    ("mobility", "the safety of pedestrian crossings in your neighborhood", "satisfaction with pedestrian crossing safety"),
    ("education", "the digital tools used in your courses", "satisfaction with course digital tools"),
]


BEHAVIOR_SPECS: list[tuple[str, str, str]] = [
    ("media/culture", "watch local news videos online", "frequency of watching local news videos online"),
    ("mobility", "use public transport for trips within your city", "frequency of using public transport"),
    ("health", "do at least 30 minutes of physical activity", "frequency of physical activity"),
    ("education", "use an online learning platform for coursework", "frequency of online learning platform use"),
    ("work", "work from home for at least half a day", "frequency of working from home"),
    ("labor", "work overtime beyond your scheduled hours", "frequency of overtime work"),
    ("finances", "check your bank account balance", "frequency of checking bank balance"),
    ("technology", "change privacy settings on a digital service", "frequency of changing digital privacy settings"),
    ("environment", "separate recyclable waste at home", "frequency of household recycling separation"),
    ("family/household", "provide unpaid care for a family member", "frequency of unpaid family care"),
    ("university life", "attend a lecture or seminar in person", "frequency of in-person lecture attendance"),
    ("public services", "contact a public office by email or web form", "frequency of contacting public offices online"),
    ("politics/public policy", "discuss a public policy issue with friends or family", "frequency of discussing public policy"),
    ("sensitive behaviors", "skip a bill payment because money was short", "frequency of skipped bill payments"),
    ("health", "look up health information online", "frequency of online health-information seeking"),
    ("media/culture", "listen to a podcast about current affairs", "frequency of listening to current-affairs podcasts"),
    ("mobility", "walk or cycle for a short trip instead of driving", "frequency of active mobility for short trips"),
    ("environment", "buy a product because it had less packaging", "frequency of low-packaging purchases"),
]


SENSITIVE_SPECS: list[tuple[str, str, str]] = [
    ("finances", "underreport cash income on an official form", "self-reported underreporting of cash income"),
    ("education", "copy text into an assignment without citing the source", "self-reported uncited copying in coursework"),
    ("sensitive behaviors", "drive after drinking alcohol", "self-reported driving after drinking"),
    ("technology", "use someone else's password without permission", "self-reported unauthorized password use"),
    ("health", "avoid medical care because of cost", "self-reported avoidance of medical care because of cost"),
    ("family/household", "experience conflict at home that made you feel unsafe", "self-reported feeling unsafe at home"),
    ("work", "take office supplies for personal use without permission", "self-reported taking workplace supplies"),
    ("labor", "work paid hours that were not officially recorded", "self-reported undeclared paid work"),
    ("media/culture", "download copyrighted media from an unofficial source", "self-reported unofficial media downloading"),
    ("university life", "submit work completed mostly by someone else", "self-reported submission of others' work"),
    ("sensitive behaviors", "bet more money than you planned", "self-reported gambling beyond planned amount"),
    ("health", "use a prescription medication not prescribed to you", "self-reported non-prescribed medication use"),
    ("politics/public policy", "feel pressured to vote a certain way by someone close to you", "self-reported voting pressure"),
    ("finances", "borrow money informally to cover basic expenses", "self-reported informal borrowing for basic expenses"),
    ("education", "miss class because of anxiety or stress", "self-reported stress-related class absence"),
    ("technology", "share a private message from someone else without asking", "self-reported sharing private messages without consent"),
]


CATEGORICAL_SPECS: list[Spec] = [
    Spec("age_group", "family/household", "respondent age group", "your age group", "Which age group includes your current age?", ("18-24", "25-34", "35-44", "45-54", "55-64", "65 or older", "Prefer not to say"), "categorical_closed_ended"),
    Spec("education_level", "education", "highest completed education level", "your highest completed education level", "What is the highest level of education you have completed?", ("No formal qualification", "Lower secondary", "Upper secondary", "Vocational training", "Bachelor's degree", "Master's degree or higher", "Other"), "categorical_closed_ended"),
    Spec("commute_mode", "mobility", "main commuting mode", "your main way of traveling to work or study", "Which mode of transport do you use most often for travel to work or study?", ("Walk", "Bicycle", "Public transport", "Car as driver", "Car as passenger", "Work or study from home", "Other"), "categorical_closed_ended"),
    Spec("employment_status", "labor", "current employment status", "your current employment status", "Which of the following best describes your current employment status?", ("Employed full time", "Employed part time", "Self-employed", "Student", "Unemployed and looking for work", "Retired", "Not in paid work for another reason"), "categorical_closed_ended"),
    Spec("housing_tenure", "family/household", "housing tenure", "your housing situation", "Which of the following best describes your current housing situation?", ("Own with mortgage", "Own without mortgage", "Rent privately", "Rent social or subsidized housing", "Live with family or friends without paying rent", "Other"), "categorical_closed_ended"),
    Spec("news_source", "media/culture", "main source of news", "your main source of news", "Which source do you use most often for news about current events?", ("Television", "Radio", "Printed newspaper or magazine", "Online news site", "Social media", "Friends or family", "I do not follow news regularly"), "categorical_closed_ended"),
    Spec("study_level", "university life", "current university study level", "your current study level", "Which best describes your current study level?", ("Bachelor's program", "Master's program", "Doctoral program", "State examination program", "Exchange or visiting student", "Not currently enrolled"), "categorical_closed_ended"),
    Spec("health_insurance", "health", "type of health insurance", "your type of health insurance", "Which type of health insurance coverage do you currently have?", ("Public or statutory insurance", "Private insurance", "Coverage through another person", "No current health insurance", "Other", "Prefer not to say"), "categorical_closed_ended"),
    Spec("banking_method", "finances", "main banking method", "your main way of doing banking", "Which method do you use most often for everyday banking?", ("Mobile banking app", "Online banking website", "ATM or self-service terminal", "Branch counter", "Telephone banking", "Someone else handles it for me"), "categorical_closed_ended"),
    Spec("internet_access", "technology", "primary internet access at home", "your main internet access at home", "Which best describes your main internet access at home?", ("Fixed broadband", "Mobile data only", "Shared connection outside the home", "No regular internet access at home", "Other"), "categorical_closed_ended"),
    Spec("waste_system", "environment", "household waste collection arrangement", "your household waste collection arrangement", "Which waste collection arrangement applies where you live?", ("Separate bins at home", "Shared building bins", "Neighborhood collection point", "No separate recycling collection", "I do not know"), "categorical_closed_ended"),
    Spec("service_channel", "public services", "preferred channel for public services", "your preferred way to contact public services", "How would you prefer to contact a public service office for a routine request?", ("Online form", "Email", "Telephone", "In-person appointment", "Postal mail", "No preference"), "categorical_closed_ended"),
]


OPEN_SPECS: list[Spec] = [
    Spec("neighborhood_problem", "public services", "most important neighborhood problem", "the most important problem in your neighborhood", "In your own words, what is the most important problem in your neighborhood at the moment?", (), "open_ended"),
    Spec("course_choice_reason", "university life", "main reason for choosing study program", "the main reason you chose your study program", "What was the main reason you chose your current study program?", (), "open_ended"),
    Spec("transport_barrier", "mobility", "main barrier to using public transport more often", "the main barrier to using public transport more often", "What is the main reason you do not use public transport more often?", (), "open_ended"),
    Spec("health_info_need", "health", "information needed before medical appointment", "the information you need before a medical appointment", "What information would be most helpful to receive before a medical appointment?", (), "open_ended"),
    Spec("workplace_improvement", "work", "most important workplace improvement", "the most important improvement at your workplace", "What is one change that would most improve your everyday work situation?", (), "open_ended"),
    Spec("news_trust_reason", "media/culture", "reason for trusting a news source", "why you trust a news source", "What makes you trust a news source?", (), "open_ended"),
    Spec("digital_service_problem", "technology", "main problem with digital public services", "the main problem with digital public services", "What is the main problem you have encountered when using digital public services?", (), "open_ended"),
    Spec("family_support_need", "family/household", "most needed family support", "the kind of support your household needs most", "What kind of support would help your household most at the moment?", (), "open_ended"),
]


NUMERIC_SPECS: list[Spec] = [
    Spec("weekly_paid_hours", "labor", "usual weekly paid working hours", "your usual weekly paid working hours", "How many paid hours do you usually work in a week?", ("0 hours", "1-9 hours", "10-19 hours", "20-29 hours", "30-39 hours", "40-49 hours", "50 hours or more"), "numeric_ranges"),
    Spec("monthly_income", "finances", "approximate monthly net household income", "your household's monthly net income", "What was your household's approximate net income last month?", ("Less than 1,000", "1,000-1,999", "2,000-2,999", "3,000-3,999", "4,000-5,999", "6,000 or more", "Prefer not to answer"), "numeric_ranges"),
    Spec("commute_minutes", "mobility", "usual one-way commute time", "your usual one-way commute time", "How long does your usual one-way trip to work or study take?", ("Less than 15 minutes", "15-29 minutes", "30-44 minutes", "45-59 minutes", "60-89 minutes", "90 minutes or more"), "numeric_ranges"),
    Spec("screen_hours", "technology", "daily non-work screen time", "your daily non-work screen time", "On a typical weekday, about how many hours do you spend on screens for non-work or non-study activities?", ("Less than 1 hour", "1-2 hours", "3-4 hours", "5-6 hours", "7 hours or more"), "numeric_ranges"),
    Spec("exercise_minutes", "health", "weekly physical activity minutes", "your weekly physical activity", "During the last 7 days, about how many minutes did you spend doing moderate or vigorous physical activity?", ("0 minutes", "1-59 minutes", "60-149 minutes", "150-299 minutes", "300 minutes or more"), "numeric_ranges"),
    Spec("childcare_hours", "family/household", "weekly unpaid childcare hours", "your weekly unpaid childcare", "During the last 7 days, about how many hours did you spend providing unpaid childcare?", ("0 hours", "1-4 hours", "5-9 hours", "10-19 hours", "20-39 hours", "40 hours or more"), "numeric_ranges"),
]


def variant_index(index: int, pool_size: int) -> int:
    return index // pool_size


def policy_question(phrase: str, index: int) -> str:
    variants = [
        f"To what extent do you support or oppose {phrase}?",
        f"Overall, do you support or oppose {phrase}?",
        f"What is your position on {phrase}?",
        f"How strongly do you support or oppose {phrase}?",
        f"Would you support or oppose {phrase}?",
    ]
    return variants[variant_index(index, len(POLICY_SPECS)) % len(variants)]


def satisfaction_question(phrase: str, index: int) -> str:
    variants = [
        f"How satisfied or dissatisfied are you with {phrase}?",
        f"Overall, how satisfied or dissatisfied are you with {phrase}?",
        f"Thinking about your own experience, how satisfied or dissatisfied are you with {phrase}?",
        f"How satisfied or dissatisfied are you with {phrase} at the moment?",
        f"In general, how satisfied or dissatisfied are you with {phrase}?",
    ]
    return variants[variant_index(index, len(SATISFACTION_SPECS)) % len(variants)]


def behavior_question(phrase: str, index: int) -> str:
    variants = [
        f"During the last 7 days, how often did you {phrase}?",
        f"In the past 7 days, how often did you {phrase}?",
        f"Thinking about the last 7 days, how often did you {phrase}?",
        f"Over the last week, how often did you {phrase}?",
        f"During the most recent 7-day period, how often did you {phrase}?",
        f"How often did you {phrase} during the last week?",
        f"In the last week, how often, if at all, did you {phrase}?",
    ]
    return variants[variant_index(index, len(BEHAVIOR_SPECS)) % len(variants)]


def sensitive_question(phrase: str, index: int) -> str:
    variants = [
        "People have different experiences, and you may skip this question. "
        f"During the last 12 months, did you {phrase}?",
        "This question is voluntary. "
        f"During the last 12 months, did you {phrase}?",
        "You may choose Prefer not to answer. "
        f"During the last 12 months, did you {phrase}?",
        "For research purposes only, and without judging the answer, "
        f"during the last 12 months, did you {phrase}?",
        "Some respondents may have had this experience and others may not. "
        f"During the last 12 months, did you {phrase}?",
        "You can choose not to answer. "
        f"In the last 12 months, did you {phrase}?",
        "For this voluntary item, "
        f"did you {phrase} at any time during the last 12 months?",
    ]
    return variants[variant_index(index, len(SENSITIVE_SPECS)) % len(variants)]


def filter_question_text(phrase: str, index: int) -> str:
    variants = [
        f"During the last 12 months, did this happen to you: {phrase}? If yes, how many times did it happen?",
        f"In the last 12 months, did you {phrase}? If yes, how many times?",
        f"Did you {phrase} at any time during the last 12 months? If yes, how often?",
        f"During the past year, did you {phrase}? If yes, how many times?",
        f"In the past 12 months, did this occur: {phrase}? If yes, how often?",
        f"Over the last 12 months, did you {phrase}? If yes, choose how often it happened.",
        f"Thinking about the last 12 months, did you {phrase}? If yes, how many times did this happen?",
    ]
    return variants[variant_index(index, len(SENSITIVE_SPECS)) % len(variants)]


def agreement_question(phrase: str, index: int) -> str:
    variants = [
        f"To what extent do you agree or disagree that {phrase} would be beneficial?",
        f"How much do you agree or disagree that {phrase} would be beneficial?",
        f"Do you agree or disagree that {phrase} would be beneficial?",
        f"Overall, to what extent do you agree or disagree that {phrase} would be beneficial?",
        f"How strongly do you agree or disagree that {phrase} would be beneficial?",
    ]
    return variants[variant_index(index, len(POLICY_SPECS)) % len(variants)]


def categorical_question(spec: Spec, index: int) -> str:
    variants = [
        spec.clean_question,
        f"{spec.clean_question} Please choose one option.",
        f"Which option best describes {spec.phrase}?",
        f"Please select the category that best describes {spec.phrase}.",
        f"Which category comes closest to {spec.phrase}?",
    ]
    return variants[variant_index(index, len(CATEGORICAL_SPECS)) % len(variants)]


def open_question(spec: Spec, index: int) -> str:
    if spec.slug == "neighborhood_problem":
        variants = [
            spec.clean_question,
            "What is the most important local problem where you live at the moment?",
            "In your own words, which problem in your neighborhood matters most right now?",
            "What local issue should be addressed first in your neighborhood?",
            "What is the main problem affecting your neighborhood currently?",
            "Which neighborhood problem is most important to you at the moment?",
            "What problem in your local area should receive the most attention?",
        ]
    elif spec.slug == "course_choice_reason":
        variants = [
            spec.clean_question,
            "In your own words, why did you choose your current study program?",
            "What was the most important factor in your choice of study program?",
            "What mainly influenced your decision to enter your current study program?",
            "What reason best explains your choice of current study program?",
            "What was the main consideration when you chose your study program?",
            "What was the strongest reason for choosing your study program?",
        ]
    else:
        variants = [
            spec.clean_question,
            f"In your own words, what is the main reason related to {spec.phrase}?",
            f"What would you describe as most important about {spec.phrase}?",
            f"What is the main explanation you would give for {spec.phrase}?",
            f"Please describe the main issue related to {spec.phrase}.",
            f"What should someone understand first about {spec.phrase}?",
            f"What is the most important thing to know about {spec.phrase}?",
        ]
    return variants[variant_index(index, len(OPEN_SPECS)) % len(variants)]


def numeric_question(spec: Spec, index: int) -> str:
    variants = [
        spec.clean_question,
        f"Which range best describes {spec.phrase}?",
        f"Please choose the range that best fits {spec.phrase}.",
        f"What category best describes {spec.phrase}?",
        f"Using the ranges below, what best describes {spec.phrase}?",
        f"Approximately which range applies to {spec.phrase}?",
        f"Please estimate {spec.phrase} using one of the ranges below.",
        f"Which of these ranges comes closest to {spec.phrase}?",
        f"What approximate range applies to {spec.phrase}?",
        f"Select the range that comes closest to {spec.phrase}.",
        f"Using the categories provided, where does {spec.phrase} fall?",
    ]
    return variants[variant_index(index, len(NUMERIC_SPECS)) % len(variants)]


def make_policy_spec(index: int) -> Spec:
    topic, phrase, concept = POLICY_SPECS[index % len(POLICY_SPECS)]
    return Spec(
        slug=f"policy_{index % len(POLICY_SPECS):02d}",
        topic=topic,
        target_concept=concept,
        phrase=phrase,
        clean_question=policy_question(phrase, index),
        clean_options=tuple(SUPPORT_OPTIONS),
        item_format="support_oppose",
    )


def make_satisfaction_spec(index: int) -> Spec:
    topic, phrase, concept = SATISFACTION_SPECS[index % len(SATISFACTION_SPECS)]
    return Spec(
        slug=f"satisfaction_{index % len(SATISFACTION_SPECS):02d}",
        topic=topic,
        target_concept=concept,
        phrase=phrase,
        clean_question=satisfaction_question(phrase, index),
        clean_options=tuple(SATISFACTION_OPTIONS),
        item_format="ordinal_categories",
    )


def make_behavior_spec(index: int) -> Spec:
    topic, phrase, concept = BEHAVIOR_SPECS[index % len(BEHAVIOR_SPECS)]
    return Spec(
        slug=f"behavior_{index % len(BEHAVIOR_SPECS):02d}",
        topic=topic,
        target_concept=concept,
        phrase=phrase,
        clean_question=behavior_question(phrase, index),
        clean_options=tuple(FREQUENCY_OPTIONS),
        item_format="frequency",
    )


def make_sensitive_spec(index: int) -> Spec:
    topic, phrase, concept = SENSITIVE_SPECS[index % len(SENSITIVE_SPECS)]
    return Spec(
        slug=f"sensitive_{index % len(SENSITIVE_SPECS):02d}",
        topic=topic,
        target_concept=concept,
        phrase=phrase,
        clean_question=sensitive_question(phrase, index),
        clean_options=tuple(YES_NO_PREFER),
        item_format="binary_yes_no",
    )


def make_categorical_spec(index: int) -> Spec:
    spec = CATEGORICAL_SPECS[index % len(CATEGORICAL_SPECS)]
    return Spec(
        slug=spec.slug,
        topic=spec.topic,
        target_concept=spec.target_concept,
        phrase=spec.phrase,
        clean_question=categorical_question(spec, index),
        clean_options=spec.clean_options,
        item_format=spec.item_format,
        secondary_phrase=spec.secondary_phrase,
    )


def make_open_spec(index: int) -> Spec:
    spec = OPEN_SPECS[index % len(OPEN_SPECS)]
    return Spec(
        slug=spec.slug,
        topic=spec.topic,
        target_concept=spec.target_concept,
        phrase=spec.phrase,
        clean_question=open_question(spec, index),
        clean_options=spec.clean_options,
        item_format=spec.item_format,
        secondary_phrase=spec.secondary_phrase,
    )


def make_numeric_spec(index: int) -> Spec:
    spec = NUMERIC_SPECS[index % len(NUMERIC_SPECS)]
    return Spec(
        slug=spec.slug,
        topic=spec.topic,
        target_concept=spec.target_concept,
        phrase=spec.phrase,
        clean_question=numeric_question(spec, index),
        clean_options=spec.clean_options,
        item_format=spec.item_format,
        secondary_phrase=spec.secondary_phrase,
    )


def spec_for_format(index: int, item_format: str) -> Spec:
    if item_format == "support_oppose":
        return make_policy_spec(index)
    if item_format == "binary_yes_no":
        return make_sensitive_spec(index)
    if item_format == "filter_question":
        sensitive = make_sensitive_spec(index)
        return Spec(
            slug=f"filter_{sensitive.slug}",
            topic=sensitive.topic,
            target_concept=sensitive.target_concept,
            phrase=sensitive.phrase,
            clean_question=filter_question_text(sensitive.phrase, index),
            clean_options=("No, did not happen", "Yes, once", "Yes, 2-3 times", "Yes, 4 or more times", "Prefer not to answer"),
            item_format="filter_question",
        )
    if item_format == "likert_agreement":
        policy = make_policy_spec(index)
        return Spec(
            slug=f"agreement_{policy.slug}",
            topic=policy.topic,
            target_concept=f"agreement that {policy.phrase} would be beneficial",
            phrase=policy.phrase,
            clean_question=agreement_question(policy.phrase, index),
            clean_options=tuple(AGREEMENT_OPTIONS),
            item_format="likert_agreement",
        )
    if item_format == "frequency":
        return make_behavior_spec(index)
    if item_format == "ordinal_categories":
        return make_satisfaction_spec(index)
    if item_format == "numeric_ranges":
        return make_numeric_spec(index)
    if item_format == "open_ended":
        return make_open_spec(index)
    if item_format == "categorical_closed_ended":
        return make_categorical_spec(index)
    raise ValueError(f"Unknown format: {item_format}")


LABEL_PROVENANCE: dict[str, dict[str, list[str]]] = {
    "leading_question": {
        "source_refs": ["SarisGallhofer2014_ch4_4.6.3", "QuestionnaireDesignLMU_slide_126"],
        "chapter_refs": ["SarisGallhofer2014_ch4"],
        "design_principles": ["neutral_request_wording", "balanced_answer_directions"],
    },
    "loaded_question": {
        "source_refs": ["SarisGallhofer2014_ch4_4.3.2", "QuestionnaireDesignLMU_slide_125"],
        "chapter_refs": ["SarisGallhofer2014_ch4"],
        "design_principles": ["make_implicit_assumptions_explicit", "use_filter_before_followup"],
    },
    "double_barreled": {
        "source_refs": ["SarisGallhofer2014_ch4_4.3.1", "QuestionnaireDesignLMU_slide_124"],
        "chapter_refs": ["SarisGallhofer2014_ch4"],
        "design_principles": ["one_request_one_concept", "split_distinct_concepts"],
    },
    "recall_error": {
        "source_refs": ["SarisGallhofer2014_ch4_4.2", "QuestionnaireDesignLMU_slide_108"],
        "chapter_refs": ["SarisGallhofer2014_ch4"],
        "design_principles": ["fit_reference_period_to_memory_task", "reduce_telescoping_risk"],
    },
    "vague_ambiguous": {
        "source_refs": ["SarisGallhofer2014_ch6_6.2.4", "QuestionnaireDesignLMU_slide_123"],
        "chapter_refs": ["SarisGallhofer2014_ch6"],
        "design_principles": ["define_key_terms_before_request", "keep_request_specific"],
    },
    "sensitive_topic_direct": {
        "source_refs": ["SarisGallhofer2014_ch4_4.2", "QuestionnaireDesignLMU_slides_113_120"],
        "chapter_refs": ["SarisGallhofer2014_ch4"],
        "design_principles": ["reduce_threat_for_sensitive_topics", "allow_nonresponse_for_sensitive_items"],
    },
    "social_desirability": {
        "source_refs": ["SarisGallhofer2014_ch4_4.2", "QuestionnaireDesignLMU_slides_113_118"],
        "chapter_refs": ["SarisGallhofer2014_ch4"],
        "design_principles": ["avoid_normative_cues", "normalize_without_pressuring"],
    },
    "negative_wording": {
        "source_refs": ["SarisGallhofer2014_ch2_2.7", "QuestionnaireDesignLMU_slide_128"],
        "chapter_refs": ["SarisGallhofer2014_ch2", "SarisGallhofer2014_ch4"],
        "design_principles": ["avoid_negative_and_double_negative_forms", "state_construct_directly"],
    },
    "open_closed_mismatch": {
        "source_refs": ["SarisGallhofer2014_ch5_5.1", "SarisGallhofer2014_ch6_6.2", "QuestionnaireDesignLMU_slide_130"],
        "chapter_refs": ["SarisGallhofer2014_ch5", "SarisGallhofer2014_ch6"],
        "design_principles": ["match_open_or_closed_format_to_measurement_goal", "avoid_unusable_answer_space"],
    },
    "agree_disagree_scale": {
        "source_refs": ["SarisGallhofer2014_ch4_4.5.2", "QuestionnaireDesignLMU_slides_157_163"],
        "chapter_refs": ["SarisGallhofer2014_ch4"],
        "design_principles": ["prefer_item_specific_scales", "avoid_unnecessary_agree_disagree_translation"],
    },
    "unbalanced_scale": {
        "source_refs": ["SarisGallhofer2014_ch4_4.6.3", "QuestionnaireDesignLMU_slide_176"],
        "chapter_refs": ["SarisGallhofer2014_ch4", "SarisGallhofer2014_ch5"],
        "design_principles": ["represent_both_sides_of_bipolar_construct", "use_symmetric_response_options"],
    },
    "incomplete_options": {
        "source_refs": ["SarisGallhofer2014_ch5_5.2", "QuestionnaireDesignLMU_slides_134_137"],
        "chapter_refs": ["SarisGallhofer2014_ch5"],
        "design_principles": ["make_closed_options_complete", "include_other_or_none_when_needed"],
    },
    "non_exclusive_options": {
        "source_refs": ["SarisGallhofer2014_ch5_5.2", "QuestionnaireDesignLMU_slides_134_137"],
        "chapter_refs": ["SarisGallhofer2014_ch5"],
        "design_principles": ["make_single_choice_options_mutually_exclusive", "avoid_overlapping_ranges"],
    },
    "missing_scale_labels": {
        "source_refs": ["SarisGallhofer2014_ch5_5.2.3", "QuestionnaireDesignLMU_slide_152"],
        "chapter_refs": ["SarisGallhofer2014_ch5"],
        "design_principles": ["label_fixed_reference_points", "make_numeric_scale_meaning_clear"],
    },
    "too_many_scale_points": {
        "source_refs": ["SarisGallhofer2014_ch5_5.3", "QuestionnaireDesignLMU_slides_155_157"],
        "chapter_refs": ["SarisGallhofer2014_ch5"],
        "design_principles": ["limit_scale_points_when_precision_is_not_justified", "avoid_false_precision"],
    },
    "polarity_mismatch": {
        "source_refs": ["SarisGallhofer2014_ch5_5.4", "QuestionnaireDesignLMU_slides_174_187"],
        "chapter_refs": ["SarisGallhofer2014_ch5"],
        "design_principles": ["match_concept_polarity_to_scale_polarity", "do_not_mix_support_with_satisfaction_or_frequency"],
    },
}


GENERAL_SOURCE_REFS = [
    "SarisGallhofer2014_ch1",
    "SarisGallhofer2014_ch2",
    "SarisGallhofer2014_ch3",
    "SarisGallhofer2014_ch4",
    "SarisGallhofer2014_ch5",
    "SarisGallhofer2014_ch6",
    "QuestionnaireDesignLMU_1",
    "AgenticSurveyItemsGeneratorOverview",
    "ProtocolMeetingAbdulSamad",
    "item_reviser_meeting_deck",
]


def stable_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def context_instruction(index: int, topic: str) -> str:
    base = TOPIC_CONTEXT_BASE.get(topic, "your own situation")
    qualifier = CONTEXT_QUALIFIERS[index % len(CONTEXT_QUALIFIERS)]
    return f"Please answer based on {base}, {qualifier}."


def add_context_to_question(question: str, index: int, topic: str) -> str:
    return f"{question} {context_instruction(index, topic)}"


def expected_revision(
    question: str,
    response_options: list[str],
    notes: list[str],
    split_items: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "question": question,
        "response_options": response_options,
        "revision_notes": notes,
    }
    if split_items:
        payload["split_items"] = split_items
    return payload


def metadata_for(
    *,
    labels: list[str],
    difficulty: str,
    item_format: str,
    authoring_route: str,
    split_group: str,
    review_notes: str,
) -> dict[str, object]:
    source_refs = list(GENERAL_SOURCE_REFS)
    chapter_refs = [
        "SarisGallhofer2014_ch1",
        "SarisGallhofer2014_ch2",
        "SarisGallhofer2014_ch3",
        "SarisGallhofer2014_ch4",
        "SarisGallhofer2014_ch5",
        "SarisGallhofer2014_ch6",
    ]
    design_principles = [
        "preserve_target_concept",
        "formulate_assertion_before_request",
        "match_response_alternatives_to_request",
    ]
    for label in labels:
        prov = LABEL_PROVENANCE[label]
        source_refs.extend(prov["source_refs"])
        chapter_refs.extend(prov["chapter_refs"])
        design_principles.extend(prov["design_principles"])
    return {
        "source": "synthetic_candidate_v1_grounded_in_saris_gallhofer_2014_and_seminar_materials",
        "source_refs": stable_unique(source_refs),
        "chapter_refs": stable_unique(chapter_refs),
        "design_principles": stable_unique(design_principles),
        "candidate_status": "candidate_v1",
        "difficulty": difficulty,
        "item_format": item_format,
        "authoring_route": authoring_route,
        "split_group": split_group,
        "needs_manual_review": True,
        "review_notes": review_notes,
    }


def make_row(
    *,
    item_id: str,
    question: str,
    response_options: list[str],
    known_errors: list[str],
    expected: dict[str, object],
    target_concept: str,
    topic: str,
    metadata: dict[str, object],
) -> dict[str, object]:
    return {
        "id": item_id,
        "question": question,
        "response_options": response_options,
        "known_errors": known_errors,
        "expected_revision": expected,
        "metadata": metadata,
        "is_flawed": bool(known_errors),
        "target_concept": target_concept,
        "topic": topic,
    }


def clean_row(index: int) -> dict[str, object]:
    item_format = FORMAT_CYCLE[index % len(FORMAT_CYCLE)]
    spec = spec_for_format(index, item_format)
    q = spec.clean_question
    opts = list(spec.clean_options)
    item_id = f"candidate-v1-clean-{index + 1:04d}"
    return make_row(
        item_id=item_id,
        question=q,
        response_options=opts,
        known_errors=[],
        expected=expected_revision(q, opts, ["Clean control; no revision expected."]),
        target_concept=spec.target_concept,
        topic=spec.topic,
        metadata=metadata_for(
            labels=[],
            difficulty=DIFFICULTIES[index % len(DIFFICULTIES)],
            item_format=spec.item_format,
            authoring_route="source_distiller>taxonomy_mapper>clean_item_author>critic_adjudicator",
            split_group=f"candidate_v1_{spec.slug}",
            review_notes="Clean control authored to test overcorrection and concept preservation.",
        ),
    )


def split_revision_for_double(spec_a: Spec, spec_b: Spec) -> dict[str, object]:
    split_items = [
        {
            "question": spec_a.clean_question,
            "response_options": list(spec_a.clean_options),
            "target_concept": spec_a.target_concept,
        },
        {
            "question": spec_b.clean_question,
            "response_options": list(spec_b.clean_options),
            "target_concept": spec_b.target_concept,
        },
    ]
    return expected_revision(
        spec_a.clean_question,
        list(spec_a.clean_options),
        [
            "Primary corrected form shown for scorer compatibility; split_items contains the full construct-preserving split.",
            "The original asks about two concepts; split rather than averaging them.",
        ],
        split_items=split_items,
    )


def flawed_leading(index: int) -> tuple[Spec, str, list[str], dict[str, object], str]:
    spec = make_policy_spec(index)
    variants = [
        f"Don't you agree that {spec.phrase} is necessary?",
        f"Wouldn't you say that {spec.phrase} is the responsible choice?",
        f"Most people see the value of {spec.phrase}; do you?",
    ]
    return spec, variants[index % len(variants)], YES_NO, expected_revision(spec.clean_question, list(spec.clean_options), ["Remove the cue toward agreement and use a balanced support-oppose scale."]), "binary_yes_no"


def flawed_loaded(index: int) -> tuple[Spec, str, list[str], dict[str, object], str]:
    sensitive = make_sensitive_spec(index)
    q = f"How many times did you {sensitive.phrase} during the last 12 months?"
    revised_q = f"During the last 12 months, did you {sensitive.phrase}? If yes, how many times did this happen?"
    revised_opts = ["No, did not happen", "Yes, once", "Yes, 2-3 times", "Yes, 4 or more times", "Prefer not to answer"]
    return sensitive, q, ["Once", "2-3 times", "4 or more times"], expected_revision(revised_q, revised_opts, ["Add a filter option so the item does not assume the behavior occurred."]), "filter_question"


def flawed_double(index: int) -> tuple[Spec, str, list[str], dict[str, object], str]:
    spec_a = make_satisfaction_spec(index)
    spec_b = make_satisfaction_spec(index + 5)
    q = f"How satisfied or dissatisfied are you with {spec_a.phrase} and {spec_b.phrase}?"
    combo = Spec(
        slug=f"double_{spec_a.slug}_{spec_b.slug}",
        topic=spec_a.topic,
        target_concept=f"{spec_a.target_concept} and {spec_b.target_concept}",
        phrase=f"{spec_a.phrase} and {spec_b.phrase}",
        clean_question=spec_a.clean_question,
        clean_options=spec_a.clean_options,
        item_format="ordinal_categories",
    )
    return combo, q, list(SATISFACTION_OPTIONS), split_revision_for_double(spec_a, spec_b), "ordinal_categories"


def flawed_recall(index: int) -> tuple[Spec, str, list[str], dict[str, object], str]:
    spec = make_behavior_spec(index)
    q = f"During the last 12 months, how many times did you {spec.phrase}?"
    revised_q = f"During the last 7 days, how often did you {spec.phrase}?"
    return spec, q, ["0 times", "1-10 times", "11-50 times", "More than 50 times"], expected_revision(revised_q, list(FREQUENCY_OPTIONS), ["Shorten the reference period for a frequent behavior to reduce recall burden."]), "frequency"


def flawed_vague(index: int) -> tuple[Spec, str, list[str], dict[str, object], str]:
    spec = make_satisfaction_spec(index)
    variants = [
        f"How do you feel overall about {spec.phrase}?",
        f"Are things okay with {spec.phrase}?",
        f"How would you rate {spec.phrase}?",
        f"What do you think about {spec.phrase}?",
        f"Is {spec.phrase} good enough?",
    ]
    q = variants[variant_index(index, len(SATISFACTION_SPECS)) % len(variants)]
    return spec, q, ["Bad", "Okay", "Good"], expected_revision(spec.clean_question, list(spec.clean_options), ["Specify the service domain and use fully interpretable response options."]), "ordinal_categories"


def flawed_sensitive_direct(index: int) -> tuple[Spec, str, list[str], dict[str, object], str]:
    spec = make_sensitive_spec(index)
    variants = [
        f"Did you {spec.phrase} during the last 12 months?",
        f"In the last 12 months, did you {spec.phrase}?",
        f"Have there been any times in the last 12 months when you did {spec.phrase}?",
    ]
    q = variants[variant_index(index, len(SENSITIVE_SPECS)) % len(variants)]
    return spec, q, YES_NO, expected_revision(spec.clean_question, list(spec.clean_options), ["Use a bounded reference period, reduce threat, and allow a prefer-not-to-answer response."]), "binary_yes_no"


def flawed_social_desirability(index: int) -> tuple[Spec, str, list[str], dict[str, object], str]:
    spec = make_behavior_spec(index)
    q = f"How often do you responsibly {spec.phrase}, as people should?"
    return spec, q, ["Never", "Sometimes", "Always"], expected_revision(spec.clean_question, list(spec.clean_options), ["Remove the normative cue and ask about the behavior neutrally."]), "frequency"


def flawed_negative(index: int) -> tuple[Spec, str, list[str], dict[str, object], str]:
    spec = make_policy_spec(index)
    q = f"To what extent do you disagree that {spec.phrase} should not be avoided?"
    return spec, q, list(AGREEMENT_OPTIONS), expected_revision(spec.clean_question, list(spec.clean_options), ["Replace the double negative with a direct support-oppose request."]), "likert_agreement"


def flawed_open_closed(index: int) -> tuple[Spec, str, list[str], dict[str, object], str]:
    spec = make_open_spec(index)
    q = spec.clean_question
    opts = ["Yes", "No"]
    return spec, q, opts, expected_revision(q, [], ["The request asks for a reason or description, so leave it open-ended."]), "open_ended"


def flawed_agree_disagree(index: int) -> tuple[Spec, str, list[str], dict[str, object], str]:
    spec = make_policy_spec(index)
    q = f"How far do you agree or disagree that {spec.phrase} would be good?"
    return spec, q, list(AGREEMENT_OPTIONS), expected_revision(spec.clean_question, list(spec.clean_options), ["Use an item-specific support-oppose scale instead of an agree-disagree translation."]), "likert_agreement"


def flawed_unbalanced(index: int) -> tuple[Spec, str, list[str], dict[str, object], str]:
    spec = make_policy_spec(index)
    q = f"To what extent do you favor {spec.phrase}?"
    opts = ["Strongly favor", "Favor", "Somewhat favor", "Neutral", "Oppose"]
    return spec, q, opts, expected_revision(spec.clean_question, list(spec.clean_options), ["Represent both support and opposition symmetrically."]), "support_oppose"


def flawed_incomplete(index: int) -> tuple[Spec, str, list[str], dict[str, object], str]:
    spec = make_categorical_spec(index)
    q = spec.clean_question
    if spec.slug == "age_group":
        opts = ["18-24", "25-34", "35-44", "45-54"]
    elif spec.slug == "commute_mode":
        opts = ["Car", "Public transport"]
    else:
        opts = list(spec.clean_options[: max(2, len(spec.clean_options) - 2)])
    return spec, q, opts, expected_revision(q, list(spec.clean_options), ["Add omitted plausible categories or an appropriate residual category."]), "categorical_closed_ended"


def flawed_nonexclusive(index: int) -> tuple[Spec, str, list[str], dict[str, object], str]:
    spec = make_categorical_spec(index)
    q = spec.clean_question
    if spec.slug == "age_group":
        opts = ["18-25", "25-34", "34-44", "44-64", "65 or older"]
    elif spec.slug == "education_level":
        opts = ["Lower secondary or less", "Upper secondary", "Upper secondary or vocational training", "Bachelor's degree", "Bachelor's degree or higher", "Other"]
    elif spec.slug == "commute_mode":
        opts = ["Walk or bicycle", "Bicycle or public transport", "Public transport", "Car as driver", "Car as driver or passenger", "Other"]
    elif spec.slug == "employment_status":
        opts = ["Employed", "Employed full time", "Employed part time", "Self-employed or employed", "Student", "Not in paid work"]
    elif spec.slug == "housing_tenure":
        opts = ["Own", "Own with mortgage", "Rent", "Rent privately", "Rent social or subsidized housing", "Live with family or friends"]
    elif spec.slug == "news_source":
        opts = ["Online news", "Online news site", "Social media", "Television or online video", "Radio or podcast", "Friends or family"]
    elif spec.slug == "study_level":
        opts = ["Undergraduate", "Bachelor's program", "Graduate program", "Master's program", "Doctoral program", "Not currently enrolled"]
    elif spec.slug == "health_insurance":
        opts = ["Public insurance", "Private insurance", "Public or private insurance", "Coverage through another person", "No current health insurance", "Other"]
    elif spec.slug == "banking_method":
        opts = ["Mobile banking", "Online banking", "Mobile or online banking", "ATM or self-service terminal", "Branch counter", "Someone else handles it"]
    elif spec.slug == "internet_access":
        opts = ["Fixed broadband", "Mobile data", "Fixed or mobile data", "Shared connection outside the home", "No regular internet access", "Other"]
    elif spec.slug == "waste_system":
        opts = ["Separate bins at home", "Shared bins", "Shared building bins", "Neighborhood collection point", "No separate recycling collection", "I do not know"]
    elif spec.slug == "service_channel":
        opts = ["Online form", "Email", "Online form or email", "Telephone", "In-person appointment", "Postal mail"]
    else:
        opts = ["Option A", "Option A or B", "Option B", "Option C"]
    return spec, q, opts, expected_revision(q, list(spec.clean_options), ["Make single-choice categories mutually exclusive."]), "categorical_closed_ended"


def flawed_missing_labels(index: int) -> tuple[Spec, str, list[str], dict[str, object], str]:
    spec = make_satisfaction_spec(index)
    q = f"How satisfied are you with {spec.phrase}? Use the scale from 0 to 10."
    opts = [str(i) for i in range(0, 11)]
    revised_opts = ["0 - Very dissatisfied", "1", "2", "3", "4", "5 - Neither satisfied nor dissatisfied", "6", "7", "8", "9", "10 - Very satisfied"]
    return spec, q, opts, expected_revision(q, revised_opts, ["Label fixed reference points so respondents know the meaning of the numeric scale."]), "numeric_ranges"


def flawed_too_many_points(index: int) -> tuple[Spec, str, list[str], dict[str, object], str]:
    spec = make_policy_spec(index)
    q = spec.clean_question
    opts = [str(i) for i in range(0, 21)]
    return spec, q, opts, expected_revision(q, list(SUPPORT_OPTIONS), ["Use a simpler item-specific scale because the requested precision is not justified for this benchmark item."]), "numeric_ranges"


def flawed_polarity(index: int) -> tuple[Spec, str, list[str], dict[str, object], str]:
    spec = make_satisfaction_spec(index)
    q = spec.clean_question
    opts = list(SUPPORT_OPTIONS)
    return spec, q, opts, expected_revision(q, list(SATISFACTION_OPTIONS), ["Use satisfaction options for a satisfaction concept rather than support-oppose options."]), "ordinal_categories"


FLAW_BUILDERS: dict[str, Callable[[int], tuple[Spec, str, list[str], dict[str, object], str]]] = {
    "leading_question": flawed_leading,
    "loaded_question": flawed_loaded,
    "double_barreled": flawed_double,
    "recall_error": flawed_recall,
    "vague_ambiguous": flawed_vague,
    "sensitive_topic_direct": flawed_sensitive_direct,
    "social_desirability": flawed_social_desirability,
    "negative_wording": flawed_negative,
    "open_closed_mismatch": flawed_open_closed,
    "agree_disagree_scale": flawed_agree_disagree,
    "unbalanced_scale": flawed_unbalanced,
    "incomplete_options": flawed_incomplete,
    "non_exclusive_options": flawed_nonexclusive,
    "missing_scale_labels": flawed_missing_labels,
    "too_many_scale_points": flawed_too_many_points,
    "polarity_mismatch": flawed_polarity,
}


def single_label_row(label: str, index: int) -> dict[str, object]:
    spec, q, opts, expected, item_format = FLAW_BUILDERS[label](index)
    item_id = f"candidate-v1-single-{label.replace('_', '-')}-{index + 1:03d}"
    return make_row(
        item_id=item_id,
        question=q,
        response_options=opts,
        known_errors=[label],
        expected=expected,
        target_concept=spec.target_concept,
        topic=spec.topic,
        metadata=metadata_for(
            labels=[label],
            difficulty=DIFFICULTIES[(index + ERROR_CATEGORIES.index(label)) % len(DIFFICULTIES)],
            item_format=item_format,
            authoring_route="source_distiller>taxonomy_mapper>clean_item_author>flaw_injector>gold_reviser>critic_adjudicator",
            split_group=f"candidate_v1_{spec.slug}",
            review_notes=f"Single-label candidate for {label}; revision is minimal and construct-preserving.",
        ),
    )


MULTI_COMBO_CYCLE = [
    ("leading_question", "unbalanced_scale"),
    ("unbalanced_scale", "missing_scale_labels"),
    ("missing_scale_labels", "too_many_scale_points"),
    ("too_many_scale_points", "agree_disagree_scale"),
    ("agree_disagree_scale", "negative_wording"),
    ("negative_wording", "polarity_mismatch"),
    ("polarity_mismatch", "incomplete_options"),
    ("incomplete_options", "non_exclusive_options"),
    ("non_exclusive_options", "open_closed_mismatch"),
    ("open_closed_mismatch", "loaded_question"),
    ("loaded_question", "sensitive_topic_direct"),
    ("sensitive_topic_direct", "social_desirability"),
    ("social_desirability", "vague_ambiguous"),
    ("vague_ambiguous", "recall_error"),
    ("recall_error", "double_barreled"),
    ("double_barreled", "leading_question"),
]


def multi_label_payload(labels: tuple[str, str], index: int) -> tuple[Spec, str, list[str], dict[str, object], str]:
    a, b = labels
    if labels == ("leading_question", "unbalanced_scale"):
        spec = make_policy_spec(index)
        q = f"Don't you agree that reasonable people should support {spec.phrase}?"
        opts = ["Strongly support", "Support", "Somewhat support", "Neutral", "Oppose"]
        expected = expected_revision(spec.clean_question, list(spec.clean_options), ["Remove leading wording and balance the response scale."])
        return spec, q, opts, expected, "support_oppose"
    if labels == ("unbalanced_scale", "missing_scale_labels"):
        spec = make_policy_spec(index)
        q = f"To what extent do you support or oppose {spec.phrase}? Use the numbered scale."
        opts = ["1", "2", "3", "4", "5 - Support"]
        expected = expected_revision(spec.clean_question, list(spec.clean_options), ["Provide balanced, labeled support and opposition categories."])
        return spec, q, opts, expected, "numeric_ranges"
    if labels == ("missing_scale_labels", "too_many_scale_points"):
        spec = make_satisfaction_spec(index)
        q = f"How satisfied are you with {spec.phrase}? Choose a number."
        opts = [str(i) for i in range(0, 21)]
        expected = expected_revision(spec.clean_question, list(spec.clean_options), ["Reduce false precision and label the response scale."])
        return spec, q, opts, expected, "numeric_ranges"
    if labels == ("too_many_scale_points", "agree_disagree_scale"):
        spec = make_policy_spec(index)
        q = f"How far do you agree or disagree that {spec.phrase} is good? Choose 0 to 20."
        opts = [str(i) for i in range(0, 21)]
        expected = expected_revision(spec.clean_question, list(spec.clean_options), ["Use a concise item-specific support-oppose scale."])
        return spec, q, opts, expected, "likert_agreement"
    if labels == ("agree_disagree_scale", "negative_wording"):
        spec = make_behavior_spec(index)
        q = f"How far do you agree or disagree that you do not fail to {spec.phrase}?"
        expected = expected_revision(spec.clean_question, list(spec.clean_options), ["Ask directly about frequency instead of using a negative agree-disagree statement."])
        return spec, q, list(AGREEMENT_OPTIONS), expected, "likert_agreement"
    if labels == ("negative_wording", "polarity_mismatch"):
        spec = make_satisfaction_spec(index)
        q = f"How dissatisfied are you that {spec.phrase} is not worse?"
        expected = expected_revision(spec.clean_question, list(spec.clean_options), ["Remove negative wording and align the response options with satisfaction."])
        return spec, q, list(SUPPORT_OPTIONS), expected, "ordinal_categories"
    if labels == ("polarity_mismatch", "incomplete_options"):
        spec = make_satisfaction_spec(index)
        q = spec.clean_question
        opts = ["Strongly support", "Somewhat support", "Neither support nor oppose"]
        expected = expected_revision(q, list(spec.clean_options), ["Use satisfaction categories and include both dissatisfied and satisfied positions."])
        return spec, q, opts, expected, "ordinal_categories"
    if labels == ("incomplete_options", "non_exclusive_options"):
        spec = make_categorical_spec(index)
        q = spec.clean_question
        if spec.slug == "age_group":
            opts = ["18-25", "25-34", "34-44"]
        elif spec.slug == "education_level":
            opts = ["Lower secondary or less", "Upper secondary", "Upper secondary or vocational training"]
        elif spec.slug == "commute_mode":
            opts = ["Walk or bicycle", "Bicycle or public transport", "Public transport"]
        elif spec.slug == "employment_status":
            opts = ["Employed", "Employed full time", "Employed part time"]
        elif spec.slug == "housing_tenure":
            opts = ["Own", "Own with mortgage", "Rent"]
        elif spec.slug == "news_source":
            opts = ["Online news", "Online news site", "Social media"]
        elif spec.slug == "study_level":
            opts = ["Undergraduate", "Bachelor's program", "Graduate program"]
        elif spec.slug == "health_insurance":
            opts = ["Public insurance", "Private insurance", "Public or private insurance"]
        elif spec.slug == "banking_method":
            opts = ["Mobile banking", "Online banking", "Mobile or online banking"]
        elif spec.slug == "internet_access":
            opts = ["Fixed broadband", "Mobile data", "Fixed or mobile data"]
        elif spec.slug == "waste_system":
            opts = ["Shared bins", "Shared building bins", "Neighborhood collection point"]
        elif spec.slug == "service_channel":
            opts = ["Online form", "Email", "Online form or email"]
        else:
            opts = ["First option", "First or second option", "Second option"]
        expected = expected_revision(q, list(spec.clean_options), ["Make categories complete and mutually exclusive."])
        return spec, q, opts, expected, "categorical_closed_ended"
    if labels == ("non_exclusive_options", "open_closed_mismatch"):
        spec = make_open_spec(index)
        q = spec.clean_question
        opts = ["Cost", "Cost or time", "Time", "Availability", "Availability or quality", "Other"]
        expected = expected_revision(q, [], ["Leave the reason request open-ended; do not force overlapping categories."])
        return spec, q, opts, expected, "open_ended"
    if labels == ("open_closed_mismatch", "loaded_question"):
        spec = make_sensitive_spec(index)
        q = f"Why did you {spec.phrase}?"
        revised_q = f"During the last 12 months, did you {spec.phrase}? If yes, what was the main reason?"
        expected = expected_revision(revised_q, [], ["Add a filter before the open follow-up and keep the reason response open-ended."])
        return spec, q, YES_NO, expected, "filter_question"
    if labels == ("loaded_question", "sensitive_topic_direct"):
        spec = make_sensitive_spec(index)
        q = f"How often did you {spec.phrase}?"
        revised_q = f"People have different experiences, and you may skip this question. During the last 12 months, did you {spec.phrase}? If yes, how many times?"
        revised_opts = ["No, did not happen", "Yes, once", "Yes, 2-3 times", "Yes, 4 or more times", "Prefer not to answer"]
        expected = expected_revision(revised_q, revised_opts, ["Avoid assuming occurrence and reduce sensitivity threat."])
        return spec, q, ["Once", "2-3 times", "4 or more times"], expected, "filter_question"
    if labels == ("sensitive_topic_direct", "social_desirability"):
        spec = make_sensitive_spec(index)
        q = f"Honest people answer truthfully: during the last 12 months, did you {spec.phrase}?"
        expected = expected_revision(spec.clean_question, list(spec.clean_options), ["Remove moral pressure, bound the reference period, and allow nonresponse."])
        return spec, q, YES_NO, expected, "binary_yes_no"
    if labels == ("social_desirability", "vague_ambiguous"):
        spec = make_behavior_spec(index)
        variants = [
            f"How often do you responsibly {spec.phrase} the way people should?",
            f"How often do you do your part by responsibly trying to {spec.phrase}?",
            f"How often do you properly {spec.phrase} like a responsible person?",
        ]
        q = variants[variant_index(index, len(BEHAVIOR_SPECS)) % len(variants)]
        expected = expected_revision(spec.clean_question, list(spec.clean_options), ["Replace vague and normative wording with a specific behavior and time period."])
        return spec, q, ["Never", "Sometimes", "Always"], expected, "frequency"
    if labels == ("vague_ambiguous", "recall_error"):
        spec = make_behavior_spec(index)
        q = f"Over the past few years, how often did you {spec.phrase} or similar things?"
        expected = expected_revision(spec.clean_question, list(spec.clean_options), ["Specify the behavior and use a shorter reference period."])
        return spec, q, ["Rarely", "Sometimes", "Often"], expected, "frequency"
    if labels == ("recall_error", "double_barreled"):
        spec_a = make_behavior_spec(index)
        spec_b = make_behavior_spec(index + 7)
        q = f"During the last 12 months, how many times did you {spec_a.phrase} and {spec_b.phrase}?"
        split_items = [
            {"question": spec_a.clean_question, "response_options": list(spec_a.clean_options), "target_concept": spec_a.target_concept},
            {"question": spec_b.clean_question, "response_options": list(spec_b.clean_options), "target_concept": spec_b.target_concept},
        ]
        expected = expected_revision(
            spec_a.clean_question,
            list(FREQUENCY_OPTIONS),
            [
                "Primary corrected form shown for scorer compatibility; split_items contains the full construct-preserving split.",
                "Separate the two behaviors and reduce recall burden.",
            ],
            split_items=split_items,
        )
        spec = Spec(f"multi_recall_double_{spec_a.slug}_{spec_b.slug}", spec_a.topic, f"{spec_a.target_concept} and {spec_b.target_concept}", q, spec_a.clean_question, spec_a.clean_options, "frequency")
        return spec, q, ["0", "1-10", "11-50", "More than 50"], expected, "frequency"
    if labels == ("double_barreled", "leading_question"):
        spec_a = make_policy_spec(index)
        spec_b = make_policy_spec(index + 9)
        q = f"Don't you agree that {spec_a.phrase} and {spec_b.phrase} are both necessary?"
        split_items = [
            {"question": spec_a.clean_question, "response_options": list(spec_a.clean_options), "target_concept": spec_a.target_concept},
            {"question": spec_b.clean_question, "response_options": list(spec_b.clean_options), "target_concept": spec_b.target_concept},
        ]
        expected = expected_revision(
            spec_a.clean_question,
            list(SUPPORT_OPTIONS),
            [
                "Primary corrected form shown for scorer compatibility; split_items contains the full construct-preserving split.",
                "Remove leading wording and separate the two policy concepts.",
            ],
            split_items=split_items,
        )
        spec = Spec(f"multi_double_leading_{spec_a.slug}_{spec_b.slug}", spec_a.topic, f"{spec_a.target_concept} and {spec_b.target_concept}", q, spec_a.clean_question, spec_a.clean_options, "support_oppose")
        return spec, q, YES_NO, expected, "support_oppose"
    raise ValueError(f"No multi-label payload builder for {a}, {b}")


def multi_label_row(combo_index: int, repeat_index: int) -> dict[str, object]:
    labels = MULTI_COMBO_CYCLE[combo_index]
    global_index = repeat_index * len(MULTI_COMBO_CYCLE) + combo_index
    spec, q, opts, expected, item_format = multi_label_payload(labels, global_index)
    label_slug = "-".join(label.replace("_", "-") for label in labels)
    item_id = f"candidate-v1-multi-{label_slug}-{repeat_index + 1:03d}"
    return make_row(
        item_id=item_id,
        question=q,
        response_options=opts,
        known_errors=list(labels),
        expected=expected,
        target_concept=spec.target_concept,
        topic=spec.topic,
        metadata=metadata_for(
            labels=list(labels),
            difficulty=DIFFICULTIES[(global_index + 1) % len(DIFFICULTIES)],
            item_format=item_format,
            authoring_route="source_distiller>taxonomy_mapper>clean_item_author>flaw_injector>gold_reviser>critic_adjudicator>coverage_auditor",
            split_group=f"candidate_v1_{spec.slug}",
            review_notes=f"Multi-label candidate for {' + '.join(labels)}; combination selected from realistic adjacent flaw families.",
        ),
    )


def build_dataset() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    rows.extend(clean_row(i) for i in range(400))
    for label in ERROR_CATEGORIES:
        rows.extend(single_label_row(label, i) for i in range(80))
    for repeat_index in range(20):
        for combo_index in range(len(MULTI_COMBO_CYCLE)):
            rows.append(multi_label_row(combo_index, repeat_index))
    assert len(rows) == 2000
    disambiguate_duplicate_questions(rows)
    return rows


def disambiguate_duplicate_questions(rows: list[dict[str, object]]) -> None:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["question"])].append(row)

    context_index = 0
    for question, duplicates in grouped.items():
        if len(duplicates) <= 1:
            continue
        keep_row = next((row for row in duplicates if not row["known_errors"]), duplicates[0])
        for duplicate_index, row in enumerate(duplicates):
            if row is keep_row:
                continue
            old_question = str(row["question"])
            topic = str(row["topic"])
            new_question = add_context_to_question(old_question, context_index, topic)
            context_index += 1
            row["question"] = new_question

            expected = row["expected_revision"]
            expected_question = str(expected.get("question", ""))
            if expected_question and not expected_question.startswith("Split this"):
                expected["question"] = add_context_to_question(
                    expected_question,
                    context_index - 1,
                    topic,
                )

            if not row["known_errors"]:
                expected["question"] = new_question
                expected["response_options"] = row["response_options"]

            review_notes = str(row["metadata"]["review_notes"])
            row["metadata"]["review_notes"] = (
                f"{review_notes} Duplicate template stem disambiguated with a neutral context instruction."
                if duplicate_index > 0
                else review_notes
            )


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    ids = [str(row["id"]) for row in rows]
    questions = [str(row["question"]) for row in rows]
    known_lengths = Counter(len(row["known_errors"]) for row in rows)
    category_counts = Counter(label for row in rows for label in row["known_errors"])
    missing_metadata: dict[str, list[str]] = defaultdict(list)
    required_metadata = [
        "source",
        "source_refs",
        "chapter_refs",
        "design_principles",
        "candidate_status",
        "difficulty",
        "item_format",
        "authoring_route",
        "split_group",
        "needs_manual_review",
        "review_notes",
    ]
    for row in rows:
        metadata = row["metadata"]
        for key in required_metadata:
            if key not in metadata:
                missing_metadata[str(row["id"])].append(key)
        for label in row["known_errors"]:
            if label not in ERROR_CATEGORIES:
                raise ValueError(f"Unknown label {label} in {row['id']}")
        if not row["known_errors"]:
            expected = row["expected_revision"]
            if expected["question"] != row["question"] or expected["response_options"] != row["response_options"]:
                raise ValueError(f"Clean row revision mismatch: {row['id']}")
    duplicate_ids = [item for item, count in Counter(ids).items() if count > 1]
    duplicate_questions = [item for item, count in Counter(questions).items() if count > 1]
    if duplicate_ids:
        raise ValueError(f"Duplicate ids: {duplicate_ids[:5]}")
    if missing_metadata:
        first = next(iter(missing_metadata.items()))
        raise ValueError(f"Missing metadata: {first}")
    return {
        "total_rows": len(rows),
        "clean_controls": known_lengths[0],
        "single_label_flawed": known_lengths[1],
        "multi_label_flawed": sum(count for labels, count in known_lengths.items() if labels > 1),
        "label_cardinality": dict(sorted(known_lengths.items())),
        "category_counts": dict(sorted(category_counts.items())),
        "duplicate_ids": duplicate_ids,
        "duplicate_question_count": len(duplicate_questions),
        "topic_distribution": dict(sorted(Counter(str(row["topic"]) for row in rows).items())),
        "format_distribution": dict(sorted(Counter(str(row["metadata"]["item_format"]) for row in rows).items())),
        "difficulty_distribution": dict(sorted(Counter(str(row["metadata"]["difficulty"]) for row in rows).items())),
        "source_ref_distribution": dict(sorted(Counter(ref for row in rows for ref in row["metadata"]["source_refs"]).items())),
        "chapter_ref_distribution": dict(sorted(Counter(ref for row in rows for ref in row["metadata"]["chapter_refs"]).items())),
    }


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def markdown_table(counter: dict[str, int], key_header: str, value_header: str = "Count") -> str:
    lines = [f"| {key_header} | {value_header} |", "|---|---:|"]
    for key, value in counter.items():
        lines.append(f"| `{key}` | {value} |")
    return "\n".join(lines)


def rubric_markdown() -> str:
    return """# Candidate v1 Benchmark Rubric

This rubric defines the candidate_v1 benchmark logic for the item-reviser only. It paraphrases the first six chapters of Saris and Gallhofer (2014) and the local seminar materials; it is not a final gold-codebook.

## Source-Grounded Design Logic

- Preserve the target concept. A revision may improve wording only if it still measures the same concept-by-intuition or the same intended indicator of a concept-by-postulation.
- Make the assertion behind the request clear. The item should make it easy to see what subject, object, predicate, time reference, and condition are being measured.
- Keep one request tied to one concept unless a carefully justified composite measure is intended. Ordinary double-barreled items should be split.
- Make assumptions explicit. If a follow-up only applies to respondents with an experience or behavior, use a filter structure.
- Match the response space to the request. Closed categories should fit the concept, be complete, be mutually exclusive for single-choice items, and use suitable labels or reference points.
- Choose open-ended items when the benchmarked measurement goal is a reason, explanation, top-of-mind problem, or other answer not known in advance.
- Prefer item-specific response options over agree-disagree translations when the item is trying to place respondents on a substantive dimension such as support, satisfaction, frequency, intensity, or evaluation.
- Reduce avoidable response burden: keep reference periods realistic, define unclear terms before the request, avoid unnecessary subordinate clauses, and avoid negative or double-negative wording.
- Treat sensitive and socially desirable behaviors with lower-threat wording, bounded reference periods, neutral context, and a nonresponse option where appropriate.
- Do not overcorrect clean controls. Some clean items are deliberately simple, and some are nuanced but acceptable.

## Label Adjudication Rules

| Label | Candidate trigger | Preferred correction |
|---|---|---|
| `leading_question` | Stem signals a preferred answer or says one answer is normal/responsible. | Reword neutrally and use balanced options. |
| `loaded_question` | Stem assumes an event, behavior, attitude, or status that may not apply. | Add a filter or explicit none/not applicable path. |
| `double_barreled` | One item asks about two separable concepts, objects, or behaviors. | Split into separate items; keep each response scale aligned. |
| `recall_error` | Reference period is too long or vague for the behavior being recalled. | Use a shorter, specific reference period or a usual-behavior frame. |
| `vague_ambiguous` | Key concept, object, actor, time, or scale meaning is unclear. | Define the term and specify the target behavior, service, or period. |
| `sensitive_topic_direct` | Sensitive behavior is asked abruptly without threat reduction. | Normalize lightly, bound time, and include `Prefer not to answer` where suitable. |
| `social_desirability` | Wording invokes moral norms, good citizenship, honesty, responsibility, or shame. | Remove normative pressure and ask the behavior neutrally. |
| `negative_wording` | Negatives or double negatives make the direction hard to process. | Recast positively or directly. |
| `open_closed_mismatch` | Open answer is needed but closed options are supplied, or a closed decision is requested without options. | Match open/closed structure to the measurement goal. |
| `agree_disagree_scale` | Agree-disagree format is used where an item-specific scale is clearer. | Replace with support, satisfaction, frequency, evaluation, or other construct-specific options. |
| `unbalanced_scale` | A bipolar construct gives more weight to one side or omits the opposite side. | Use symmetric categories around a neutral point when applicable. |
| `incomplete_options` | A closed list omits plausible respondent states. | Add missing categories or an appropriate residual option. |
| `non_exclusive_options` | Single-choice categories overlap. | Use non-overlapping categories or allow multiple selection if that is the intended task. |
| `missing_scale_labels` | Numeric points lack enough labels or fixed reference points. | Label endpoints and important anchors. |
| `too_many_scale_points` | The item asks for more precision than most respondents can use reliably for the benchmarked construct. | Use a shorter labeled scale unless high precision is justified. |
| `polarity_mismatch` | The concept and response scale point in different semantic directions. | Use options that express the same polarity as the stem. |

## Candidate Review Guidance

Human reviewers should check whether each row has the right label set, whether the expected revision preserves the target concept, whether multi-label combinations are realistic, and whether the clean controls are truly clean enough for false-positive testing.
"""


def summary_markdown(audit: dict[str, object], dataset_hash: str, seed_hash: str) -> str:
    category_counts = audit["category_counts"]
    topic_distribution = audit["topic_distribution"]
    format_distribution = audit["format_distribution"]
    difficulty_distribution = audit["difficulty_distribution"]
    chapter_distribution = audit["chapter_ref_distribution"]
    return f"""# candidate_v1_2000 Summary

Generated `candidate_v1_2000.jsonl` as a literature-grounded candidate benchmark for the item-reviser. The existing seed set at `data/eval/test_set_200_seed.jsonl` was not modified.

## Counts

- Total rows: {audit["total_rows"]}
- Clean controls: {audit["clean_controls"]}
- Flawed rows: {audit["single_label_flawed"] + audit["multi_label_flawed"]}
- Single-label flawed rows: {audit["single_label_flawed"]}
- Multi-label flawed rows: {audit["multi_label_flawed"]}
- Dataset SHA-256: `{dataset_hash}`
- Seed set SHA-256 after generation: `{seed_hash}`

## Taxonomy Label Counts

Single-label rows contribute 80 examples per label. Multi-label rows contribute 40 additional examples per label, so each taxonomy label appears 120 times in candidate_v1.

{markdown_table(category_counts, "Label")}

## Topic Distribution

{markdown_table(topic_distribution, "Topic")}

## Response-Format Distribution

{markdown_table(format_distribution, "Item format")}

## Difficulty Distribution

{markdown_table(difficulty_distribution, "Difficulty")}

## Source and Chapter Coverage

All rows carry item-level provenance in `metadata.source_refs`, `metadata.chapter_refs`, and `metadata.design_principles`. The design logic is grounded in the first six chapters of Saris and Gallhofer (2014), the LMU questionnaire-design slides, the agentic survey-item overview, the meeting protocols, and the local item-reviser deck.

{markdown_table(chapter_distribution, "Chapter/source ref")}

## Known Limitations and Review Risks

- This is candidate_v1, not final gold. All rows are marked `needs_manual_review: true`.
- Items are synthetic and template-assisted. They are designed for coverage and auditability, not for claiming population-realistic item frequencies.
- Some labels, especially `too_many_scale_points`, `missing_scale_labels`, and `agree_disagree_scale`, are context-sensitive in the literature. Reviewers should confirm that the intended correction is appropriate for each target concept.
- Clean controls include a few nuanced but acceptable formats, including direct agreement items whose target concept is explicitly agreement. They should be audited for overcorrection risk.
- Multi-label rows use realistic two-label combinations only. This keeps label incidence exactly balanced, but a future v2 could add carefully reviewed three-label cases.
- Expected revisions are minimal benchmark references, not the only acceptable revisions.
"""


def manifest(audit: dict[str, object], dataset_hash: str, seed_hash: str) -> dict[str, object]:
    source_files = [
        "seminar-material/Willem E. Saris, Irmtraud N. Gallhofer-Design, Evaluation, and Analysis of Questionnaires for Survey Research-Wiley (2014).pdf",
        "seminar-material/Questionnaire Design_LMU_1.pptx",
        "seminar-material/Agentic Survey Items Generator Overview.pdf",
        "seminar-material/Protocol Meeting Abdul Samad-v1.docx",
        "seminar-material/Protocol Meeting Abdul Samad.docx",
        "seminar-material/item_reviser_meeting_deck.tex",
        "docs/source_notes.md",
        "docs/literature_checklist.md",
    ]
    return {
        "dataset_name": "candidate_v1_2000",
        "candidate_status": "candidate_v1",
        "description": "Literature-grounded synthetic candidate benchmark for the SEMINAR-ITEM-REVISER item-reviser.",
        "row_count": audit["total_rows"],
        "schema_contract": "Compatible with src/item_reviser/evaluation/dataset.py and SurveyItem.from_dict.",
        "dataset_path": str(DATASET_PATH.relative_to(REPO_ROOT)),
        "summary_path": str(SUMMARY_PATH.relative_to(REPO_ROOT)),
        "rubric_path": str(RUBRIC_PATH.relative_to(REPO_ROOT)),
        "review_queue_path": str(REVIEW_QUEUE_PATH.relative_to(REPO_ROOT)),
        "dataset_sha256": dataset_hash,
        "seed_eval_set_path": str(SEED_DATASET_PATH.relative_to(REPO_ROOT)),
        "seed_eval_set_sha256_after_generation": seed_hash,
        "target_composition": {
            "clean_controls": 400,
            "single_label_flawed": 1280,
            "single_label_per_taxonomy_label": 80,
            "multi_label_flawed": 320,
            "multi_label_additional_instances_per_label": 40,
        },
        "actual_counts": audit,
        "source_files": [
            {
                "path": path,
                "sha256": sha256_file(REPO_ROOT / path) if (REPO_ROOT / path).exists() else None,
            }
            for path in source_files
        ],
        "generation_workflow": [
            "source_distiller: paraphrased design principles from first six textbook chapters and seminar materials",
            "taxonomy_mapper: aligned principles to the 16 repository labels",
            "clean_item_author: authored clean base items across topic domains and response formats",
            "flaw_injector: generated controlled single-label and realistic multi-label flaws",
            "gold_reviser: generated minimal construct-preserving expected revisions",
            "critic_adjudicator: encoded schema, label, clean-control, and revision checks in the script audit",
            "coverage_auditor: enforced quotas and distribution summaries",
            "repo_integrator: wrote processed artifacts and ran the repository validator",
        ],
        "validation_command": "python scripts/validate_eval_set.py data/processed/candidate_v1_2000.jsonl",
        "manual_review_required": True,
    }


def review_queue_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    queue = []
    for row in rows:
        queue.append(
            {
                "id": row["id"],
                "known_errors": row["known_errors"],
                "is_flawed": row["is_flawed"],
                "topic": row["topic"],
                "target_concept": row["target_concept"],
                "difficulty": row["metadata"]["difficulty"],
                "item_format": row["metadata"]["item_format"],
                "split_group": row["metadata"]["split_group"],
                "question": row["question"],
                "response_options": row["response_options"],
                "expected_revision": row["expected_revision"],
                "review_status": "pending",
                "review_notes": row["metadata"]["review_notes"],
            }
        )
    return queue


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = build_dataset()
    audit = audit_rows(rows)
    if audit["total_rows"] != 2000:
        raise ValueError("Dataset must contain exactly 2,000 rows.")
    if audit["clean_controls"] != 400:
        raise ValueError("Dataset must contain exactly 400 clean controls.")
    if audit["single_label_flawed"] != 1280:
        raise ValueError("Dataset must contain exactly 1,280 single-label flawed rows.")
    if audit["multi_label_flawed"] != 320:
        raise ValueError("Dataset must contain exactly 320 multi-label flawed rows.")
    for label in ERROR_CATEGORIES:
        if audit["category_counts"].get(label) != 120:
            raise ValueError(f"Expected exactly 120 total instances for {label}.")

    write_jsonl(DATASET_PATH, rows)
    dataset_hash = sha256_file(DATASET_PATH)
    seed_hash = sha256_file(SEED_DATASET_PATH)
    RUBRIC_PATH.write_text(rubric_markdown(), encoding="utf-8")
    SUMMARY_PATH.write_text(summary_markdown(audit, dataset_hash, seed_hash), encoding="utf-8")
    MANIFEST_PATH.write_text(json.dumps(manifest(audit, dataset_hash, seed_hash), indent=2, sort_keys=True), encoding="utf-8")
    write_jsonl(REVIEW_QUEUE_PATH, review_queue_rows(rows))
    print(f"Wrote {DATASET_PATH.relative_to(REPO_ROOT)}")
    print(f"Wrote {SUMMARY_PATH.relative_to(REPO_ROOT)}")
    print(f"Wrote {MANIFEST_PATH.relative_to(REPO_ROOT)}")
    print(f"Wrote {RUBRIC_PATH.relative_to(REPO_ROOT)}")
    print(f"Wrote {REVIEW_QUEUE_PATH.relative_to(REPO_ROOT)}")
    print(f"Rows: {audit['total_rows']}")
    print(f"Dataset SHA-256: {dataset_hash}")
    print(f"Seed SHA-256: {seed_hash}")


if __name__ == "__main__":
    main()
