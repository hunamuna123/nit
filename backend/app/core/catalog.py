from typing import Literal

CATEGORIES: list[dict[str, str]] = [
    {
        "slug": "study",
        "title": "Учёба",
        "icon": "graduation-cap",
        "description": "Отчёты, курсовые, защиты и всё, что связано с учебным процессом",
    },
    {
        "slug": "docs",
        "title": "Документы",
        "icon": "file-text",
        "description": "Справки, заявления, Госуслуги и бюрократия без нервов",
    },
    {
        "slug": "hardware",
        "title": "Железо и ПК",
        "icon": "cpu",
        "description": "Сборка, апгрейд и обслуживание компьютеров и ноутбуков",
    },
    {
        "slug": "dev",
        "title": "Разработка",
        "icon": "code",
        "description": "Инструменты разработчика: Docker, Git, Python и окружение",
    },
    {
        "slug": "home",
        "title": "Дом и быт",
        "icon": "house",
        "description": "Общежитие, аренда, домашняя сеть и бытовые задачи",
    },
    {
        "slug": "career",
        "title": "Карьера",
        "icon": "briefcase",
        "description": "Резюме, стажировки, собеседования и первые шаги в профессии",
    },
    {
        "slug": "money",
        "title": "Финансы",
        "icon": "wallet",
        "description": "Налоги, вычеты, стипендии и самозанятость",
    },
]

CATEGORY_SLUGS = {c["slug"] for c in CATEGORIES}

Cover = Literal["torus", "peanut", "drop", "blob", "ring", "infinity"]
COVERS: tuple[str, ...] = ("torus", "peanut", "drop", "blob", "ring", "infinity")
