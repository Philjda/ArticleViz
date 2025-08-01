import string, nltk, spacy, unicodedata, csv
from nltk.corpus import stopwords
from collections import Counter, defaultdict
from itertools import combinations
from gensim.models import FastText
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# 🔧 Préparations
nltk.download('stopwords')
stop_words = set(stopwords.words('french'))
nlp = spacy.load("fr_core_news_sm")
custom_stopwords = set(["ainsi", "toutefois", "également"])

def remove_accents(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c))

# 📄 Charger et nettoyer le texte
with open("art2.txt", "r", encoding="utf-8") as f:
    texte = f.read().lower()

texte_clean = ''.join([c for c in texte if c.isalpha() or c.isspace()])
texte_clean = remove_accents(texte_clean)
doc = nlp(texte_clean)

mots = [
    token.lemma_ for token in doc
    if isinstance(token.text, str)
    and isinstance(token.lemma_, str)
    and token.text not in stop_words
    and token.lemma_ not in custom_stopwords
    and token.is_alpha
]

# 🔁 Cooccurrences (fenêtre 5)
window_size = 5
edges = Counter()
for i in range(len(mots)):
    window = mots[i:i + window_size]
    for pair in combinations(window, 2):
        if pair[0] != pair[1]:
            edges[frozenset(pair)] += 1

# 🤖 Embeddings FastText
model = FastText(sentences=[mots], vector_size=100, window=5, min_count=2)
vectors = {word: model.wv[word] for word in mots if word in model.wv}

words = list(vectors.keys())
vec_matrix = np.array([vectors[w] for w in words])
similarities = cosine_similarity(vec_matrix)

# 🔀 Réseau hybride : cooccurrence + similarité
def normalize(counter):
    max_val = max(counter.values()) if counter else 1
    return {k: v / max_val for k, v in counter.items()}

hybrid_edges = defaultdict(float)
norm_cooc = normalize(edges)
for k, v in norm_cooc.items():
    hybrid_edges[k] += v

threshold = 0.7
for i in range(len(words)):
    for j in range(i + 1, len(words)):
        sim = similarities[i][j]
        if sim >= threshold:
            hybrid_edges[frozenset([words[i], words[j]])] += sim

# 📤 Export Gephi-ready CSV
with open("hybrid_network2.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Source", "Target", "Weight"])
    for pair, weight in hybrid_edges.items():
        source, target = tuple(pair)
        writer.writerow([source, target, round(weight, 3)])
