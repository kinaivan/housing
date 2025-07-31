"""
Dutch names for household generation
"""

DUTCH_FIRST_NAMES = [
    "Jan", "Pieter", "Willem", "Johannes", "Hendrik", "Lars", "Thomas", "Lucas",
    "Liam", "Noah", "Daan", "Finn", "Sem", "Milan", "Levi", "Luuk", "Bram",
    "Emma", "Julia", "Sophie", "Lisa", "Anna", "Eva", "Mila", "Sara", "Nova",
    "Maria", "Sophia", "Lotte", "Elin", "Luna", "Nora", "Olivia", "Nina",
    "Sven", "Thijs", "Ruben", "Tim", "Simon", "David", "Daniel", "Max", "Sam",
    "Fleur", "Isa", "Noor", "Roos", "Tess", "Fenna", "Lynn", "Sofie", "Vera"
]

DUTCH_LAST_NAMES = [
    "de Jong", "Jansen", "de Vries", "van den Berg", "van Dijk", "Bakker",
    "Janssen", "Visser", "Smit", "Meijer", "de Boer", "Mulder", "de Groot",
    "Bos", "Vos", "Peters", "Hendriks", "van Leeuwen", "Dekker", "Brouwer",
    "de Wit", "Dijkstra", "Smits", "de Graaf", "van der Meer", "van der Linden",
    "Kok", "Jacobs", "de Haan", "Vermeulen", "van der Veen", "van der Berg",
    "van der Wal", "van der Pol", "Kuiper", "Veenstra", "Kramer", "van Wijk",
    "Scholten", "van der Heijden", "Prins", "Huisman", "Peeters", "Willems",
    "Verhoeven", "van der Velde", "Postma", "Hoekstra", "Koning", "Nguyen"
]

def generate_dutch_name():
    """Generate a random Dutch name"""
    import random
    first_name = random.choice(DUTCH_FIRST_NAMES)
    last_name = random.choice(DUTCH_LAST_NAMES)
    return f"{first_name} {last_name}" 