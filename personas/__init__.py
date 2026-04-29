from personas.abhimanyu import ABHIMANYU_SYSTEM_PROMPT
from personas.anshuman import ANSHUMAN_SYSTEM_PROMPT
from personas.kshitij import KSHITIJ_SYSTEM_PROMPT

PERSONAS = {
    "Anshuman Singh": {
        "prompt": ANSHUMAN_SYSTEM_PROMPT,
        "title": "Co-founder, Scaler & InterviewBit",
        "tagline": "Pushes students toward world-class engineering standards.",
        "avatar_image_name": "anshuman_singh",
        "color": "#FF7A1A",
        "accent": "#FFC999",
        "chips": [
            "How do I get better at DSA?",
            "Is SST worth it over BITS or NIT?",
            "I feel behind my peers. What should I do?",
            "What did you learn from building Facebook Messenger?",
        ],
    },
    "Abhimanyu Saxena": {
        "prompt": ABHIMANYU_SYSTEM_PROMPT,
        "title": "Co-founder, Scaler & InterviewBit",
        "tagline": "Precision-first advice on systems, outcomes, and long-term value.",
        "avatar_image_name": "abhimanyu_saxena",
        "color": "#3AB0FF",
        "accent": "#B9E3FF",
        "chips": [
            "Why did you build SST instead of scaling online?",
            "What do you look for when hiring engineers?",
            "The SST curriculum feels overwhelming. Is that normal?",
            "How did the skills gap idea come to you?",
        ],
    },
    "Kshitij Mishra": {
        "prompt": KSHITIJ_SYSTEM_PROMPT,
        "title": "Dean, SST | Head of Instructors, Scaler",
        "tagline": "High-rigor mentor who forces specificity and honest thinking.",
        "avatar_image_name": "kshitij_mishra",
        "color": "#7ED957",
        "accent": "#D5F5C6",
        "chips": [
            "I think I understand recursion but keep failing problems.",
            "The exam schedule at SST feels too intense.",
            "I got rejected in a campus interview. I'm demotivated.",
            "How do I know if I'm actually good at DSA?",
        ],
    },
}
