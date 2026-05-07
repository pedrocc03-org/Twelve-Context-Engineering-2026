import pandas as pd
from utils.embeddings_utils import get_embedding, cosine_similarity
import re
from functools import lru_cache

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


def _normalize_tokens(text):
    return set(re.findall(r"[a-z0-9]+", str(text).lower()))


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
                }
            )

        for attr, info in ATTRIBUTE_INFO.items():
            docs.append(
                {
                    "user": f"What does {attr.lower()} mean in the physical analyst?",
                    "assistant": info["definition"],
                    "category": "attribute_definition",
                    "format": "attribute",
                }
            )

            for metric in info["metrics"]:
                raw_metric = metric.replace(" (INV)", "")
                friendly = FRIENDLY_NAMES.get(raw_metric, raw_metric)
                docs.append(
                    {
                        "user": f"What does {friendly} mean?",
                        "assistant": (
                            f"{friendly.capitalize()} sits under {attr.lower()} in the physical analyst. "
                            f"Underlying metric: {raw_metric}."
                        ),
                        "category": attr.lower(),
                        "format": "metric_alias",
                    }
                )

        df = pd.DataFrame(docs).drop_duplicates(subset=["user", "assistant"]).reset_index(drop=True)
        df["tokens"] = (
            df["user"].fillna("").astype(str) + " " + df["assistant"].fillna("").astype(str)
        ).apply(_normalize_tokens)
        return df

    def search(self, query, top_n=5):
        query_tokens = _normalize_tokens(query)
        if not query_tokens:
            return self.df_dict.head(0).copy()

        df = self.df_dict.copy()

        def score_row(row):
            overlap = len(query_tokens & row["tokens"])
            if overlap == 0:
                return 0.0

            coverage = overlap / len(query_tokens)
            query_text = str(query).lower()
            user_text = str(row["user"]).lower()
            phrase_bonus = 0.2 if user_text in query_text or query_text in user_text else 0.0
            return coverage + phrase_bonus

        df["similarities"] = df.apply(score_row, axis=1)
        return df[df["similarities"] > 0].sort_values("similarities", ascending=False).head(top_n)
