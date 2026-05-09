import pandas as pd
from utils.embeddings_utils import get_embedding, cosine_similarity
import re
from functools import lru_cache
import unicodedata

from settings import (
    GPT_EMBEDDINGS_MODEL,
    USE_GEMINI,
    GEMINI_EMBEDDING_MODEL,
    GEMINI_API_KEY,
)
from pages.physical.config import ATTRIBUTE_INFO, FRIENDLY_NAMES


class Embeddings:
    def __init__(self):
        self.df_dict = None

    def search(self, query, top_n=3):
        # type is the index into the various dataframes stored in the embeddings.
        # if type is not specified, it will search all dataframes
        # otherwise it will search those listed

        if USE_GEMINI:
            import google.generativeai as genai

            genai.configure(api_key=GEMINI_API_KEY)
            ENGINE = GEMINI_EMBEDDING_MODEL
        else:
            ENGINE = GPT_EMBEDDINGS_MODEL
        embedding = get_embedding(query, engine=ENGINE, use_gemini=USE_GEMINI)

        # An option for the future is to take the top from each dataframe, so we get a mixture of responses.
        df = self.df_dict
        df["similarities"] = df.user_embedded.apply(
            lambda x: cosine_similarity(x, embedding)
        )
        df = df[df.similarities > 0.7]

        res = df.sort_values("similarities", ascending=False).head(top_n)
        return res

    def compare_strings(self, string1, string2):
        # Use this function to compare two strings or words embeddings
        # Returns co-sine similarilty between the two strings
        ENGINE = GEMINI_EMBEDDING_MODEL if USE_GEMINI else GPT_EMBEDDINGS_MODEL
        embedding1 = get_embedding(string1, engine=ENGINE, use_gemini=USE_GEMINI)
        embedding2 = get_embedding(string2, engine=ENGINE, use_gemini=USE_GEMINI)

        return cosine_similarity(embedding1, embedding2)

    def return_embedding(self, query):
        if USE_GEMINI:
            import google.generativeai as genai

            genai.configure(api_key=GEMINI_API_KEY)
            ENGINE = GEMINI_EMBEDDING_MODEL
        else:
            ENGINE = GPT_EMBEDDINGS_MODEL
        embedding = get_embedding(query, engine=ENGINE, use_gemini=USE_GEMINI)

        return embedding


class PlayerEmbeddings(Embeddings):
    def __init__(self):
        self.df_dict = PlayerEmbeddings.get_embeddings()

    def get_embeddings():
        # Gets all relevant embeddings
        files = [
            "Interpretation",
            "Forward",
        ]

        df_embeddings = pd.DataFrame()
        for file in files:
            # Read in
            df_temp = pd.read_parquet(f"data/embeddings/{file}.parquet")
            if "category" not in df_temp:
                df_temp["category"] = None
            if "format" not in df_temp:
                df_temp["format"] = None
            df_temp = df_temp[
                ["user", "assistant", "category", "user_embedded", "format"]
            ]
            df_temp["user_embedded"] = df_temp.user_embedded.apply(eval).to_list()
            df_embeddings = pd.concat([df_embeddings, df_temp], ignore_index=True)

        return df_embeddings


class CountryEmbeddings(Embeddings):
    def __init__(self):
        self.df_dict = CountryEmbeddings.get_embeddings()

    def get_embeddings():
        # Gets all relevant embeddings
        files = [
            "WVS_qualities",
        ]

        df_embeddings = pd.DataFrame()
        for file in files:
            # Read in
            df_temp = pd.read_parquet(f"data/embeddings/{file}.parquet")
            if "category" not in df_temp:
                df_temp["category"] = None
            if "format" not in df_temp:
                df_temp["format"] = None
            df_temp = df_temp[
                ["user", "assistant", "category", "user_embedded", "format"]
            ]
            df_temp["user_embedded"] = df_temp.user_embedded.apply(eval).to_list()
            df_embeddings = pd.concat([df_embeddings, df_temp], ignore_index=True)

        return df_embeddings


class PersonEmbeddings(Embeddings):
    def __init__(self):
        self.df_dict = PersonEmbeddings.get_embeddings()

    def get_embeddings():
        # Gets all embeddings
        df_embeddings_dict = dict()

        files = [
            "Forward_bigfive",
        ]

        df_embeddings = pd.DataFrame()
        for file in files:
            # Read in
            df_temp = pd.read_parquet(f"data/embeddings/{file}.parquet")
            if "category" not in df_temp:
                df_temp["category"] = None
            if "format" not in df_temp:
                df_temp["format"] = None
            df_temp = df_temp[
                ["user", "assistant", "category", "user_embedded", "format"]
            ]
            df_temp["user_embedded"] = df_temp.user_embedded.apply(eval).to_list()
            df_embeddings = pd.concat([df_embeddings, df_temp], ignore_index=True)

        return df_embeddings


PHYSICAL_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "about",
    "can",
    "do",
    "does",
    "for",
    "from",
    "get",
    "give",
    "he",
    "her",
    "him",
    "his",
    "how",
    "i",
    "in",
    "is",
    "it",
    "like",
    "mean",
    "me",
    "of",
    "on",
    "or",
    "player",
    "physical",
    "profile",
    "tell",
    "that",
    "the",
    "this",
    "to",
    "what",
}


def _normalize_text(text):
    text = str(text).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _normalize_tokens(text):
    return {
        token
        for token in re.findall(r"[a-z0-9]+", _normalize_text(text))
        if len(token) > 1 and token not in PHYSICAL_STOPWORDS
    }


def _phrase_in_text(phrase, text):
    if not phrase or not text:
        return False
    pattern = r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])"
    return re.search(pattern, text) is not None


class PhysicalEmbeddings(Embeddings):
    def __init__(self):
        self.df_dict = PhysicalEmbeddings.get_embeddings()

    @staticmethod
    @lru_cache(maxsize=1)
    def get_embeddings():
        docs = []

        describe_df = pd.read_excel("data/describe/Physical.xlsx")
        for _, row in describe_df.iterrows():
            docs.append(
                {
                    "user": row["user"],
                    "assistant": row["assistant"],
                    "category": "metric_definition",
                    "format": "qa",
                    "attribute": None,
                    "metric": None,
                    "aliases": tuple(),
                }
            )

        for attr, info in ATTRIBUTE_INFO.items():
            attr_normalized = _normalize_text(attr)
            docs.append(
                {
                    "user": f"What does {attr.lower()} mean in the physical analyst?",
                    "assistant": info["definition"],
                    "category": "attribute_definition",
                    "format": "attribute",
                    "attribute": attr,
                    "metric": None,
                    "aliases": (attr_normalized,),
                }
            )

            for metric in info["metrics"]:
                raw_metric = metric.replace(" (INV)", "")
                friendly = FRIENDLY_NAMES.get(raw_metric, raw_metric)
                alias_phrases = tuple(
                    dict.fromkeys(
                        filter(
                            None,
                            (
                                _normalize_text(friendly),
                                _normalize_text(raw_metric),
                                attr_normalized,
                            ),
                        )
                    )
                )
                docs.append(
                    {
                        "user": f"What does {friendly} mean?",
                        "assistant": (
                            f"{friendly.capitalize()} sits under {attr.lower()} in the physical analyst. "
                            f"Underlying metric: {raw_metric}."
                        ),
                        "category": attr.lower(),
                        "format": "metric_alias",
                        "attribute": attr,
                        "metric": raw_metric,
                        "aliases": alias_phrases,
                    }
                )

        df = pd.DataFrame(docs).drop_duplicates(subset=["user", "assistant"]).reset_index(drop=True)
        df["normalized_user"] = df["user"].fillna("").astype(str).apply(_normalize_text)
        df["normalized_assistant"] = df["assistant"].fillna("").astype(str).apply(_normalize_text)
        df["normalized_text"] = (
            df["normalized_user"].fillna("") + " " + df["normalized_assistant"].fillna("")
        ).str.strip()
        df["tokens"] = (
            df["normalized_text"]
        ).apply(_normalize_tokens)
        return df

    def search(self, query, top_n=5):
        query_text = _normalize_text(query)
        query_tokens = _normalize_tokens(query)
        if not query_tokens:
            return self.df_dict.head(0).copy()

        df = self.df_dict.copy()
        asks_for_definition = any(phrase in query_text for phrase in ("what does", "mean", "definition", "explain"))
        explicit_attribute_queries = set()
        for attr in ATTRIBUTE_INFO:
            normalized_attr = _normalize_text(attr)
            if (
                query_text == normalized_attr
                or _phrase_in_text(f"what does {normalized_attr} mean", query_text)
                or _phrase_in_text(f"define {normalized_attr}", query_text)
                or _phrase_in_text(f"explain {normalized_attr}", query_text)
                or _phrase_in_text(f"{normalized_attr} in the physical analyst", query_text)
            ):
                explicit_attribute_queries.add(attr)

        def score_row(row):
            overlap = len(query_tokens & row["tokens"])
            coverage = overlap / max(len(query_tokens), 1)
            precision = overlap / max(len(row["tokens"]), 1)
            score = 0.65 * coverage + 0.15 * precision

            alias_hits = 0
            for alias in row["aliases"]:
                if _phrase_in_text(alias, query_text):
                    alias_hits += 1

            if row["normalized_user"] and _phrase_in_text(row["normalized_user"], query_text):
                score += 1.2
            if alias_hits:
                score += 0.45 * alias_hits

            if asks_for_definition and row["format"] in {"metric_alias", "attribute", "qa"}:
                score += 0.2

            if row["attribute"] in explicit_attribute_queries:
                score += 0.35
                if row["format"] == "attribute":
                    score += 1.0

            if row["format"] == "metric_alias" and alias_hits:
                score += 0.2

            return score

        df["similarities"] = df.apply(score_row, axis=1)
        return (
            df[df["similarities"] > 0.2]
            .sort_values(
                ["similarities", "format", "category"],
                ascending=[False, True, True],
            )
            .head(top_n)
        )
