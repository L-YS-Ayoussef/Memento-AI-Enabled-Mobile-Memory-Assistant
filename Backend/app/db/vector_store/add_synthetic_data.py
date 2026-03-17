from datetime import datetime, timedelta, timezone
from vector_store import vector_store as vs

now = datetime.now(timezone.utc)

synthetic_tenants = [
    {
        "tenant_id": "1",
        "general_information": (
            "Aisha is a Cairo-based software engineer who loves astronomy "
            "and open-source contribution."
        ),
        "events": [
            {   # variable event 1
                "title":          "Morning run along the Nile",
                "trigger":        "time",
                "start_time":     (now + timedelta(days=1, hours=6)).isoformat(),
                "end_time":       (now + timedelta(days=1, hours=7)).isoformat(),
                "min_start_time": (now + timedelta(days=1, hours=6)).isoformat(),
                "max_end_time":   (now + timedelta(days=1, hours=23, minutes=59, seconds=59)).isoformat(),
                "can_overlap":    False,
                "recurring":      86400,
                "place":          "Corniche el-Nile",
                "people":         ["Aisha"],
                "details":        "5 km cardio as part of training plan.",
                "cancelled": False
            },
            {   # variable event 2
                "title":          "Ramadan charity coding workshop",
                "trigger":        "time",
                "start_time":     (now + timedelta(days=3, hours=16)).isoformat(),
                "end_time":       (now + timedelta(days=3, hours=19)).isoformat(),
                "min_start_time": (now + timedelta(days=3, hours=16)).isoformat(),
                "max_end_time":   (now + timedelta(days=3, hours=23, minutes=59, seconds=59)).isoformat(),
                "can_overlap":    False,
                "recurring":      0,
                "place":          "Cairo MakerHub",
                "people":         ["Volunteer team"],
                "details":        "Teach Python basics to local students.",
                "cancelled": False
            },
        ],
    },
    {
        "tenant_id": "2",
        "general_information": (
            "Diego is an Argentinian UX designer living in Berlin; enjoys cycling."
        ),
        "events": [
            {
                "title":          "Design sprint kickoff",
                "trigger":        "time",
                "start_time":     (now + timedelta(days=2, hours=10)).isoformat(),
                "end_time":       (now + timedelta(days=2, hours=12)).isoformat(),
                "min_start_time": (now + timedelta(days=2, hours=10)).isoformat(),
                "max_end_time":   (now + timedelta(days=2, hours=23, minutes=59, seconds=59)).isoformat(),
                "can_overlap":    False,
                "recurring":      0,
                "place":          "Company HQ – Mitte",
                "people":         ["Product team"],
                "details":        "Kickoff workshop for new onboarding flow.",
                "cancelled": False
            },
            {
                "title":          "Tempelhofer evening cycling ride",
                "trigger":        "time",
                "start_time":     (now + timedelta(days=2, hours=17)).isoformat(),
                "end_time":       (now + timedelta(days=2, hours=19)).isoformat(),
                "min_start_time": (now + timedelta(days=2, hours=17)).isoformat(),
                "max_end_time":   (now + timedelta(days=2, hours=23, minutes=59, seconds=59)).isoformat(),
                "can_overlap":    False,
                "recurring":      604800,
                "place":          "Tempelhofer Feld",
                "people":         ["Berlin Cycling Club"],
                "details":        "40 km group ride (helmet required).",
                "cancelled": False
            },
        ],
    },
    {
        "tenant_id": "3",
        "general_information": (
            "Mei is a data-science master’s student in Shanghai, fascinated by NLP."
        ),
        "events": [
            {
                "title":          "NLP seminar: Transformers 101",
                "trigger":        "time",
                "start_time":     (now + timedelta(days=3, hours=14)).isoformat(),
                "end_time":       (now + timedelta(days=3, hours=16)).isoformat(),
                "min_start_time": (now + timedelta(days=3, hours=14)).isoformat(),
                "max_end_time":   (now + timedelta(days=3, hours=23, minutes=59, seconds=59)).isoformat(),
                "can_overlap":    False,
                "recurring":      0,
                "place":          "SJTU Eng. Bldg 301",
                "people":         ["Prof. Zhang", "Lab peers"],
                "details":        "Guest lecture + Q&A.",
                "cancelled": False
            },
            {
                "title":          "BERT fine-tuning experiment",
                "trigger":        "time",
                "start_time":     (now + timedelta(days=3, hours=18)).isoformat(),
                "end_time":       (now + timedelta(days=3, hours=20)).isoformat(),
                "min_start_time": (now + timedelta(days=3, hours=18)).isoformat(),
                "max_end_time":   (now + timedelta(days=3, hours=23, minutes=59, seconds=59)).isoformat(),
                "can_overlap":    True,
                "recurring":      259200,
                "place":          "University GPU cluster",
                "people":         [],
                "details":        "Log metrics in experiment notebook.",
                "cancelled": False
            },
        ],
    },
    {
        "tenant_id": "4",
        "general_information": (
            "Lars is a freelance photographer touring Scandinavian fjords."
        ),
        "events": [
            {
                "title":          "Sunrise shoot at Geirangerfjord",
                "trigger":        "location",
                "start_time":     (now + timedelta(days=4, hours=4)).isoformat(),
                "end_time":       (now + timedelta(days=4, hours=7)).isoformat(),
                "min_start_time": (now + timedelta(days=4, hours=3, minutes=30)).isoformat(),
                "max_end_time":   (now + timedelta(days=4, hours=23, minutes=59, seconds=59)).isoformat(),
                "can_overlap":    False,
                "recurring":      0,
                "place":          "Geirangerfjord viewpoint",
                "people":         [],
                "details":        "Golden-hour landscape capture.",
                "cancelled": False
            },
            {
                "title":          "Client deliverables editing session",
                "trigger":        "time",
                "start_time":     (now + timedelta(days=4, hours=15)).isoformat(),
                "end_time":       (now + timedelta(days=4, hours=18)).isoformat(),
                "min_start_time": (now + timedelta(days=4, hours=15)).isoformat(),
                "max_end_time":   (now + timedelta(days=4, hours=23, minutes=59, seconds=59)).isoformat(),
                "can_overlap":    False,
                "recurring":      0,
                "place":          "Camper-van workstation",
                "people":         ["Lars"],
                "details":        "Lightroom + Photoshop; upload proofs.",
                "cancelled": False
            },
        ],
    },
{
        "tenant_id": "5",
        "general_information": (
            "Jordan is a project manager who schedules back-to-back meetings "
            "and wants the assistant to prevent double-booking."
        ),
        "events": [
            {
                "title":          "Quarterly roadmap review",
                "trigger":        "time",
                "start_time":     (now + timedelta(days=1, hours=9)).isoformat(),
                "end_time":       (now + timedelta(days=1, hours=10)).isoformat(),
                "min_start_time": (now + timedelta(days=1, hours=9)).isoformat(),
                "max_end_time":   (now + timedelta(days=1, hours=23, minutes=59, seconds=59)).isoformat(),
                "can_overlap":    False,
                "recurring":      0,
                "place":          "Head Office – ConfRm A",
                "people":         ["Leadership Team"],
                "details":        "Review product roadmap and key milestones.",
                "cancelled": False
            },
            {
                "title":          "Client kickoff call",
                "trigger":        "time",
                "start_time":     (now + timedelta(days=1, hours=9, minutes=30)).isoformat(),
                "end_time":       (now + timedelta(days=1, hours=11)).isoformat(),
                "min_start_time": (now + timedelta(days=1, hours=9, minutes=30)).isoformat(),
                "max_end_time":   (now + timedelta(days=1, hours=23, minutes=59, seconds=59)).isoformat(),
                "can_overlap":    False,
                "recurring":      0,
                "place":          "Zoom",
                "people":         ["Client X stakeholders"],
                "details":        "Project kickoff; slides in shared drive.",
                "cancelled": False
            },
        ],
    },
]

# for tenant in synthetic_tenants:
#     tid = tenant["tenant_id"]
#     vs.add_user(tid)
#     uid = vs.add_user_general_information(tid, tenant["general_information"])
#     print(f"Inserted User {uid} into '{tid}'")
#
#     for ev in tenant["events"]:
#         eid = vs.add_event(tid, ev)
#         print(f"inserted Event {eid} into '{tid}'")

vs.add_user('2')

vs.client.close()
