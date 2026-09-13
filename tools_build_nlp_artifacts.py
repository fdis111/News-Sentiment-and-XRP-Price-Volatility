#!/usr/bin/env python
"""W4: build the small vendored NLP artefacts the notebook needs to run offline.

WordNet is ~10 MB zipped and cannot ship inside a 10 MB deliverable. It IS used - once,
here, at authoring time - to derive a lemma map restricted to this corpus's vocabulary,
which is small enough to vendor. The notebook then lemmatises without WordNet present.
"""
import collections
import json
import pathlib
import re

import pandas as pd
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

OUT = pathlib.Path("data_sample/nlp")
OUT.mkdir(parents=True, exist_ok=True)

URL = re.compile(r"http\S+|www\.\S+")
KEEP = re.compile(r"[^A-Za-z0-9\s.,!?'$%-]")
DEC = re.compile(r"(\d)\s+\.\s+(\d)")
SPC = re.compile(r"\s+([.,:;!?%])")
WORD = re.compile(r"[A-Za-z][A-Za-z'-]+")


def clean(v):
    if not isinstance(v, str):
        return ""
    v = URL.sub(" ", v)
    v = DEC.sub(r"\1.\2", v)
    v = SPC.sub(r"\1", v)
    v = KEEP.sub(" ", v)
    return re.sub(r"\s+", " ", v).strip()


news = pd.read_csv("data_sample/xrp_gdelt_news.csv")
texts = news["headline"].map(clean)

# ---------------------------------------------------------------- vocabulary
tf = collections.Counter()
df = collections.Counter()
for t in texts:
    toks = [w.lower() for w in WORD.findall(t)]
    tf.update(toks)
    df.update(set(toks))
print(f"corpus {len(texts)} headlines, {len(tf)} distinct tokens")

# ---------------------------------------------------------------- lemma map
lem = WordNetLemmatizer()


def best_lemma(word: str) -> str:
    """
    Lemma without a POS tagger.

    A tagger would cost another ~2 MB of model and buy little on headlines, so both the
    verb and noun readings are tried and the one that actually reduces the token is
    taken, preferring the verb (headlines are verb-heavy: "surges", "files", "plunges").
    The known failure is a noun that looks like an inflected verb - "holdings" reduces to
    "holding" - which is recorded here rather than hidden.
    """
    v = lem.lemmatize(word, "v")
    n = lem.lemmatize(word, "n")
    if v != word:
        return v
    if n != word:
        return n
    return word


# Two artefacts, not one. The map holds the words WordNet REDUCES; the companion list
# holds the words WordNet inspected and left alone. Both are needed: without the second,
# a word that is already its own lemma is indistinguishable from a word the map never saw,
# and the notebook's crude suffix fallback fires on it. Measured cost of that conflation
# before the list existed: 279 corpus types mangled ("across" -> "acros", "analysis" ->
# "analysi", "focus" -> "focu"), 277 of them pure damage. See §4.0.6.
lemma_map = {}
known_lemmas = []
for w in tf:
    l = best_lemma(w)
    if l != w:
        lemma_map[w] = l
    else:
        known_lemmas.append(w)
(OUT / "lemma_map.json").write_text(json.dumps(lemma_map, sort_keys=True, indent=0))
(OUT / "known_lemmas.txt").write_text("\n".join(sorted(known_lemmas)) + "\n")
print(f"lemma map: {len(lemma_map)} reductions "
      f"({len(lemma_map)/len(tf):.0%} of vocabulary)")
print(f"known lemmas (inspected, unchanged): {len(known_lemmas)}")

# ---------------------------------------------------------------- stopwords
en = sorted(set(stopwords.words("english")))
(OUT / "stopwords_en.txt").write_text("\n".join(en) + "\n")
print(f"english stopwords vendored: {len(en)}")

# Domain stop-words, derived rather than guessed: tokens appearing in a large share of
# documents carry almost no power to distinguish one day's coverage from another's.
n_docs = len(texts)
ubiquitous = {w: df[w] / n_docs for w in df if df[w] / n_docs >= 0.03 and w not in en}
# Crypto-native slang and SEO boilerplate that survive the frequency filter but are
# still noise for sentiment. Curated, and marked as such.
CURATED = [
    "hodl", "moon", "mooning", "fud", "rekt", "wen", "ser", "gm", "ath", "dyor",
    "wagmi", "ngmi", "bagholder", "degen", "shill", "altcoin", "altcoins", "memecoin",
    "presale", "airdrop", "whale", "whales", "pump", "prediction", "predictions",
    "forecast", "analyst", "analysts", "outlook", "roundup", "explained", "heres",
    "todays", "week", "weekly", "daily", "update", "updates",
]
domain_stop = sorted(set(list(ubiquitous) + CURATED))
(OUT / "stopwords_domain.txt").write_text("\n".join(domain_stop) + "\n")
print(f"domain stopwords: {len(domain_stop)} "
      f"({len(ubiquitous)} derived by document frequency >= 3%, {len(CURATED)} curated)")
print("  derived:", sorted(ubiquitous, key=ubiquitous.get, reverse=True)[:18])

# ---------------------------------------------------------------- finance lexicon
# VADER valences run -4..+4. Only terms with a genuine DIRECTION are added. Topic markers
# that a naive list would include - sec, etf, volatility, leverage, settlement,
# regulation - are deliberately excluded: they say what an article is about, not whether
# it is good or bad news, and scoring them would inject the analyst's priors into the
# measurement. That exclusion list is shipped too, so the choice is inspectable.
FINANCE = {
    # downside
    "bearish": -2.0, "selloff": -2.5, "sell-off": -2.5, "plunge": -3.0, "plunges": -3.0,
    "plummet": -3.2, "plummets": -3.2, "slump": -2.3, "slumps": -2.3, "tumble": -2.5,
    "tumbles": -2.5, "capitulation": -2.8, "liquidation": -2.4, "liquidations": -2.4,
    "drawdown": -2.0, "outflow": -1.5, "outflows": -1.5, "delisting": -2.8,
    "delisted": -2.8, "subpoena": -2.2, "injunction": -2.0, "downgrade": -2.0,
    "downgrades": -2.0, "bankruptcy": -3.5, "insolvency": -3.4, "fraud": -3.2,
    "halt": -1.8, "halted": -1.8, "ban": -2.5, "banned": -2.5, "probe": -1.8,
    "sue": -2.2, "sued": -2.2, "hack": -3.0, "hacked": -3.0, "exploit": -2.6,
    "breach": -2.6, "slide": -1.8, "slides": -1.8, "sink": -2.2, "sinks": -2.2,
    "bearishness": -2.0, "correction": -1.2, "pullback": -1.4, "bear": -1.5,
    # upside
    "bullish": 2.0, "bullishness": 2.0, "rally": 2.0, "rallies": 2.0, "surge": 2.5,
    "surges": 2.5, "soar": 2.8, "soars": 2.8, "inflow": 1.5, "inflows": 1.5,
    "upgrade": 2.0, "upgrades": 2.0, "approval": 2.2, "approved": 2.2,
    "adoption": 1.8, "breakout": 1.8, "bull": 1.5, "outperform": 2.0,
    "rebound": 1.8, "rebounds": 1.8, "recovery": 1.6, "jump": 1.5, "jumps": 1.5,
    "climb": 1.5, "climbs": 1.5, "gain": 1.5, "gains": 1.5, "surging": 2.5,
    "skyrocket": 3.0, "skyrockets": 3.0,
}
EXCLUDED = {
    "sec": "a regulator, not a sentiment - appears in both good and bad news",
    "etf": "a product; 'ETF approval' is positive, 'ETF rejected' is not",
    "volatility": "the dependent variable - scoring it would be circular",
    "leverage": "a mechanism, directionally neutral",
    "settlement": "resolves a dispute; outcome-dependent, not inherently good or bad",
    "regulation": "a topic marker; direction depends entirely on the ruling",
    "lawsuit": "already in VADER at -0.9; not overridden",
    "court": "an institution, not a valence",
    "ruling": "outcome-dependent",
}
(OUT / "finance_lexicon.json").write_text(
    json.dumps({"valences": FINANCE, "excluded_with_reasons": EXCLUDED},
               sort_keys=True, indent=1))
print(f"finance lexicon: {len(FINANCE)} terms added, "
      f"{len(EXCLUDED)} topic markers deliberately excluded")

# coverage: how much of the corpus do the new terms actually touch?
hit = sum(tf[w] for w in FINANCE if w in tf)
print(f"  new terms account for {hit:,} token instances "
      f"({hit/sum(tf.values()):.2%} of the corpus)")
print(f"  of {len(FINANCE)} added terms, {sum(1 for w in FINANCE if w in tf)} occur here")

total = sum(f.stat().st_size for f in OUT.glob("*"))
print(f"\nvendored artefacts: {total/1024:.0f} KB total")
for f in sorted(OUT.glob("*")):
    print(f"  {f.name:24} {f.stat().st_size/1024:7.1f} KB")
