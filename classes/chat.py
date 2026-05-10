import streamlit as st
from openai import OpenAI
from itertools import groupby
from types import GeneratorType
import pandas as pd
import json
import re
import unicodedata

from settings import USE_GEMINI, USE_LM_STUDIO

if USE_GEMINI:
    from settings import GEMINI_API_KEY, GEMINI_CHAT_MODEL
elif USE_LM_STUDIO:
    from settings import LM_STUDIO_API_KEY, LM_STUDIO_CHAT_MODEL, LM_STUDIO_API_BASE
else:
    from settings import (
        GPT_BASE,
        GPT_KEY,
        GPT_CHAT_MODEL,
        GPT_SUPPORTS_REASONING,
        GPT_AVAILABLE_REASONING_EFFORTS,
        GPT_SUPPORTS_TEMPERATURE,
    )

from classes.description import (
    PlayerDescription,
    CountryDescription,
    PersonDescription,
)
from classes.physical_description import PhysicalDescription
from classes.embeddings import (
    PlayerEmbeddings,
    CountryEmbeddings,
    PersonEmbeddings,
    PhysicalEmbeddings,
)

from classes.visual import Visual, DistributionPlot, DistributionPlotPersonality

import utils.sentences as sentences
from utils.gemini import convert_messages_format


class Chat:
    function_names = []

    def __init__(self, chat_state_hash, state="empty"):

        if (
            "chat_state_hash" not in st.session_state
            or chat_state_hash != st.session_state.chat_state_hash
        ):
            # st.write("Initializing chat")
            st.session_state.chat_state_hash = chat_state_hash
            st.session_state.messages_to_display = []
            st.session_state.chat_state = state
        if isinstance(self, PlayerChat):
            self.name = self.player.name
        elif isinstance(self, PersonChat):
            self.name = self.person.name
        else:
            pass

        # Set session states as attributes for easier access
        self.messages_to_display = st.session_state.messages_to_display
        self.state = st.session_state.chat_state

    def instruction_messages(self):
        """
        Sets up the instructions to the agent. Should be overridden by subclasses.
        """
        return []

    def add_message(self, content, role="assistant", user_only=True, visible=True):
        """
        Used by app.py to start off the conversation with plots and descriptions.
        """
        message = {"role": role, "content": content}
        self.messages_to_display.append(message)

    # def get_input(self):
    #     """
    #     Get input from streamlit."""

    #     if x := st.chat_input(
    #         placeholder=f"What else would you like to know about {self.player.name}?"
    #     ):
    #         if len(x) > 500:
    #             st.error(
    #                 f"Your message is too long ({len(x)} characters). Please keep it under 500 characters."
    #             )

    #         self.handle_input(x)

    def handle_input(self, input, reasoning_effort=None, temperature=1, stream=False):
        """
        The main function that calls the GPT-4 API and processes the response.
        """

        # Get the instruction messages.
        messages = self.instruction_messages()

        # Add a copy of the user messages. This is to give the assistant some context.
        messages = messages + self.messages_to_display.copy()

        # Get relevant information from the user input and then generate a response.
        # This is not added to messages_to_display as it is not a message from the assistant.
        get_relevant_info = self.get_relevant_info(input)

        # Now add the user input to the messages. Don't add system information and system messages to messages_to_display.
        self.messages_to_display.append({"role": "user", "content": input})

        messages.append(
            {
                "role": "user",
                "content": f"Here is the relevant information to answer the users query: {get_relevant_info}\n\n```User: {input}```",
            }
        )

        # Remove all items in messages where content is not a string
        messages = [
            message for message in messages if isinstance(message["content"], str)
        ]

        # Show the messages in an expander
        st.expander("Chat transcript", expanded=False).write(messages)

        # Check if use gemini is set to true
        if USE_GEMINI:
            import google.generativeai as genai

            converted_msgs = convert_messages_format(messages)

            # # save converted messages to json
            # with open("data/wvs/msgs_1.json", "w") as f:
            #     json.dump(converted_msgs, f)

            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel(
                model_name=GEMINI_CHAT_MODEL,
                system_instruction=converted_msgs["system_instruction"],
            )
            chat = model.start_chat(history=converted_msgs["history"])
            response = chat.send_message(content=converted_msgs["content"])

            answer = response.text
        elif USE_LM_STUDIO:
            client = OpenAI(api_key=LM_STUDIO_API_KEY, base_url=LM_STUDIO_API_BASE)
            if stream:
                # Collect chunks eagerly so the generator over the list is
                # near-instantaneous — preventing Streamlit re-runs from
                # hitting the same generator while it is still executing.
                chunks = [
                    chunk.choices[0].delta.content
                    for chunk in client.chat.completions.create(
                        model=LM_STUDIO_CHAT_MODEL,
                        messages=messages,
                        temperature=temperature,
                        stream=True,
                    )
                    if chunk.choices and chunk.choices[0].delta.content
                ]

                def streamed_chunks():
                    yield from chunks

                answer = streamed_chunks()
            else:
                response = client.chat.completions.create(
                    model=LM_STUDIO_CHAT_MODEL,
                    messages=messages,
                    temperature=temperature,
                )
                answer = response.choices[0].message.content
        else:
            client = OpenAI(api_key=GPT_KEY, base_url=GPT_BASE)
            if stream:
                if GPT_SUPPORTS_REASONING:
                    reasoning_effort = reasoning_effort if reasoning_effort in GPT_AVAILABLE_REASONING_EFFORTS else GPT_AVAILABLE_REASONING_EFFORTS[0]
                    response_stream = client.responses.create(
                        model=GPT_CHAT_MODEL,
                        input=messages,
                        reasoning={"effort": reasoning_effort},
                        stream=True,
                    )
                elif GPT_SUPPORTS_TEMPERATURE:
                    response_stream = client.responses.create(
                        model=GPT_CHAT_MODEL,
                        input=messages,
                        temperature=temperature,
                        stream=True,
                    )
                else:
                    response_stream = client.responses.create(
                        model=GPT_CHAT_MODEL,
                        input=messages,
                        stream=True,
                    )

                def streamed_chunks():
                    for event in response_stream:
                        if event.type == "response.output_text.delta":
                            yield event.delta

                answer = streamed_chunks()
            else:
                if GPT_SUPPORTS_REASONING:
                    reasoning_effort = reasoning_effort if reasoning_effort in GPT_AVAILABLE_REASONING_EFFORTS else GPT_AVAILABLE_REASONING_EFFORTS[0]
                    response = client.responses.create(
                        model=GPT_CHAT_MODEL,
                        input=messages,
                        reasoning={"effort": reasoning_effort},
                    )
                elif GPT_SUPPORTS_TEMPERATURE:
                    response = client.responses.create(
                        model=GPT_CHAT_MODEL,
                        input=messages,
                        temperature=temperature,
                    )
                else:
                    response = client.responses.create(
                        model=GPT_CHAT_MODEL,
                        input=messages,
                    )

                answer = response.output_text
        message = {"role": "assistant", "content": answer}

        # Add the returned value to the messages.
        self.messages_to_display.append(message)

    def display_content(self, content):
        """
        Displays the content of a message in streamlit. Handles plots, strings, and StreamingMessages.
        """
        if isinstance(content, str):
            st.write(content)

        # Visual
        elif isinstance(content, Visual):
            content.show()

        else:
            # So we do this in case
            try:
                content.show()
            except:
                try:
                    st.write(content.get_string())
                except:
                    raise ValueError(
                        f"Message content of type {type(content)} not supported."
                    )

    def display_messages(self):
        """
        Displays visible messages in streamlit. Messages are grouped by role.
        If message content is a Visual, it is displayed in a st.columns((1, 2, 1))[1].
        If the message is a list of strings/Visuals of length n, they are displayed in n columns.
        If a message is a generator, it is displayed with st.write_stream
        Special case: If there are N Visuals in one message, followed by N messages/StreamingMessages in the next, they are paired up into the same N columns.
        """
        # Group by role so user name and avatar is only displayed once

        # st.write(self.messages_to_display)

        for key, group in groupby(self.messages_to_display, lambda x: x["role"]):
            group = list(group)

            if key == "assistant":
                avatar = "data/ressources/img/twelve_chat_logo.svg"
            else:
                try:
                    avatar = st.session_state.user_info["picture"]
                except:
                    avatar = None

            message_block = st.chat_message(name=key, avatar=avatar)
            with message_block:
                for message in group:
                    content = message["content"]
                    if isinstance(content, GeneratorType):
                        final_text = st.write_stream(content)
                        message["content"] = final_text
                    else:
                        self.display_content(content)

    def save_state(self):
        """
        Saves the conversation to session state.
        """
        st.session_state.messages_to_display = self.messages_to_display
        st.session_state.chat_state = self.state


class PlayerChat(Chat):
    def __init__(self, chat_state_hash, player, players, state="empty"):
        self.embeddings = PlayerEmbeddings()
        self.player = player
        self.players = players
        super().__init__(chat_state_hash, state=state)

    def get_input(self):
        """
        Get input from streamlit."""

        if x := st.chat_input(
            placeholder=f"What else would you like to know about {self.player.name}?"
        ):
            if len(x) > 500:
                st.error(
                    f"Your message is too long ({len(x)} characters). Please keep it under 500 characters."
                )

            self.handle_input(x, stream=True)

    def instruction_messages(self):
        """
        Instruction for the agent.
        """
        first_messages = [
            {"role": "system", "content": "You are a UK-based football scout."},
            {
                "role": "user",
                "content": (
                    "After these messages you will be interacting with a user of a football scouting platform. "
                    f"The user has selected the player {self.player.name}, and the conversation will be about them. "
                    "You will receive relevant information to answer a user's questions and then be asked to provide a response. "
                    "All user messages will be prefixed with 'User:' and enclosed with ```. "
                    "When responding to the user, speak directly to them. "
                    "Use the information provided before the query  to provide 2 sentence answers."
                    " Do not deviate from this information or provide additional information that is not in the text returned by the functions."
                ),
            },
        ]
        return first_messages

    def get_relevant_info(self, query):

        # If there is no query then use the last message from the user
        if query == "":
            query = self.visible_messages[-1]["content"]

        ret_val = "Here is a description of the player in terms of data: \n\n"
        description = PlayerDescription(self.player)
        ret_val += description.synthesize_text()

        # This finds some relevant information
        results = self.embeddings.search(query, top_n=5)
        ret_val += "\n\nHere is a description of some relevant information for answering the question:  \n"
        ret_val += "\n".join(results["assistant"].to_list())

        ret_val += f"\n\nIf none of this information is relevent to the users's query then use the information below to remind the user about the chat functionality: \n"
        ret_val += "This chat can answer questions about a player's statistics and what they mean for how they play football."
        ret_val += "The user can select the player they are interested in using the menu to the left."

        return ret_val


class WVSChat(Chat):
    def __init__(
        self,
        chat_state_hash,
        country,
        countries,
        description_dict,
        thresholds_dict,
        state="empty",
    ):
        # TODO:
        self.embeddings = CountryEmbeddings()
        self.country = country
        self.countries = countries
        self.description_dict = description_dict
        self.thresholds_dict = thresholds_dict
        super().__init__(chat_state_hash, state=state)

    def get_input(self):
        """
        Get input from streamlit."""

        if x := st.chat_input(
            placeholder=f"What else would you like to know about {self.country.name}?"
        ):
            if len(x) > 500:
                st.error(
                    f"Your message is too long ({len(x)} characters). Please keep it under 500 characters."
                )

            self.handle_input(x, stream=True)

    def instruction_messages(self):
        """
        Instruction for the agent.
        """
        # TODO: Update first_messages
        first_messages = [
            {"role": "system", "content": "You are a researcher."},
            {
                "role": "user",
                "content": (
                    "After these messages you will be interacting with a user of a data analysis platform. "
                    f"The user has selected the country {self.country.name}, and the conversation will be about different core value measured in the World Value Survey study. "
                    # "You will receive relevant information to answer a user's questions and then be asked to provide a response. "
                    "All user messages will be prefixed with 'User:' and enclosed with ```. "
                    "When responding to the user, speak directly to them. "
                    "Use the information provided before the query to provide 2 sentence answers."
                    " Do not deviate from this information or provide additional information that is not in the text returned by the functions."
                ),
            },
        ]
        return first_messages

    def get_relevant_info(self, query):

        # If there is no query then use the last message from the user
        if query == "":
            query = self.visible_messages[-1]["content"]

        ret_val = "Here is a description of the country in terms of data: \n\n"
        description = CountryDescription(
            self.country, self.description_dict, self.thresholds_dict
        )
        ret_val += description.synthesize_text()

        # This finds some relevant information
        results = self.embeddings.search(query, top_n=5)
        ret_val += "\n\nHere is a description of some relevant information for answering the question:  \n"
        ret_val += "\n".join(results["assistant"].to_list())

        ret_val += f"\n\nIf none of this information is relevant to the users's query then use the information below to remind the user about the chat functionality: \n"
        ret_val += "This chat can answer questions about a country's core values."
        ret_val += "The user can select the country they are interested in using the menu to the left."

        return ret_val


class PersonChat(Chat):
    def __init__(self, chat_state_hash, person, persons, state="empty"):
        self.embeddings = PersonEmbeddings()
        self.person = person
        self.persons = persons
        super().__init__(chat_state_hash, state=state)

    def instruction_messages(self):
        """
        Instruction for the agent.
        """
        first_messages = [
            {"role": "system", "content": "You are a recruiter."},
            {
                "role": "user",
                "content": (
                    "After these messages you will be interacting with a user of personality test platform. "
                    f"The user has selected the person {self.person.name}, and the conversation will be about them. "
                    "You will receive relevant information to answer a user's questions and then be asked to provide a response. "
                    "All user messages will be prefixed with 'User:' and enclosed with ```. "
                    "When responding to the user, speak directly to them. "
                    "Use the information provided before the query  to provide 2 sentence answers."
                    " Do not deviate from this information or provide additional information that is not in the text returned by the functions."
                ),
            },
        ]
        return first_messages

    def get_relevant_info(self, query):

        # If there is no query then use the last message from the user
        if query == "":
            query = self.visible_messages[-1]["content"]

        ret_val = "Here is a description of the person in terms of data: \n\n"
        description = PersonDescription(self.person)
        ret_val += description.synthesize_text()

        # This finds some relevant information
        results = self.embeddings.search(query, top_n=5)
        ret_val += "\n\nHere is a description of some relevant information for answering the question:  \n"
        ret_val += "\n".join(results["assistant"].to_list())

        ret_val += f"\n\nIf none of this information is relevent to the users's query then use the information below to remind the user about the chat functionality: \n"
        ret_val += "This chat can answer questions about person's statistics and what they mean about their personality."
        ret_val += "The user can select the persons they are interested in using the menu to the left."

        return ret_val

    def get_input(self):
        """
        Get input from streamlit."""

        if x := st.chat_input(
            placeholder=f"What else would you like to know about {self.person.name}?"
        ):
            if len(x) > 500:
                st.error(
                    f"Your message is too long ({len(x)} characters). Please keep it under 500 characters."
                )

            self.handle_input(x, stream=True)


class PhysicalChat(Chat):
    QUERY_ROUTE_PHYSICAL_ONLY = "physical_only"
    QUERY_ROUTE_MIXED = "mixed"
    QUERY_ROUTE_NON_PHYSICAL = "non_physical"
    QUERY_ROUTE_UNCLEAR = "unclear"
    QUERY_ROUTE_COMPARISON = "comparison"
    PLAYER_RESOLUTION_NONE = "none"
    PLAYER_RESOLUTION_RESOLVED = "resolved"
    PLAYER_RESOLUTION_AMBIGUOUS = "ambiguous"

    IN_SCOPE_KEYWORDS = {
        "physical",
        "speed",
        "pace",
        "quick",
        "quickness",
        "fast",
        "sprint",
        "sprinting",
        "acceleration",
        "accelerate",
        "deceleration",
        "burst",
        "bursts",
        "explosive",
        "agility",
        "agile",
        "recovery",
        "turning",
        "turn",
        "cod",
        "endurance",
        "stamina",
        "distance",
        "running",
        "hsr",
        "intensity",
        "volume",
        "engine",
        "workrate",
        "metrics",
        "metric",
        "velocity",
        "psv",
        "profile",
    }
    OUT_OF_SCOPE_KEYWORDS = {
        "tactical": {
            "positioning",
            "marking",
            "pressing",
            "system",
            "shape",
            "role",
            "roles",
            "tactics",
            "tactical",
            "structure",
            "line",
            "block",
            "fit",
            "transition",
            "offball",
        },
        "technical": {
            "first",
            "touch",
            "shooting",
            "shot",
            "shots",
            "passing",
            "pass",
            "passes",
            "crossing",
            "cross",
            "dribbling",
            "dribble",
            "finishing",
            "finisher",
            "technique",
            "technical",
            "ball",
            "ballplaying",
        },
        "mental": {
            "leadership",
            "leader",
            "composure",
            "decision",
            "decisions",
            "mindset",
            "mentality",
            "mental",
            "focus",
            "concentration",
            "aggression",
            "confidence",
        },
        "team_context": {
            "manager",
            "coach",
            "teammates",
            "teammate",
            "club",
            "dressing",
            "room",
            "chemistry",
            "style",
            "systemfit",
            "environment",
            "squad",
        },
    }

    def __init__(
        self,
        chat_state_hash,
        player_row=None,
        position_df=None,
        raw_position_df=None,
        all_players_df=None,
        all_raw_df=None,
        detailed=False,
        state="empty",
    ):
        self.embeddings = PhysicalEmbeddings()
        self.player_row = player_row
        self.position_df = position_df
        self.raw_position_df = raw_position_df
        self.all_players_df = all_players_df if all_players_df is not None else position_df
        self.all_raw_df = all_raw_df if all_raw_df is not None else raw_position_df
        self.detailed = detailed
        self.pending_player_matches = []
        self.player_resolution_status = self.PLAYER_RESOLUTION_NONE
        super().__init__(chat_state_hash, state=state)
        self.name = self.player_row["Player"] if self.player_row is not None else "physical analyst"

    def get_input(self):
        """
        Get input from streamlit.
        """
        if x := st.chat_input(
            placeholder="Ask about a player, a physical metric, or the physical analyst scope"
        ):
            if len(x) > 500:
                st.error(
                    f"Your message is too long ({len(x)} characters). Please keep it under 500 characters."
                )

            self.handle_input(x, stream=True)

    def instruction_messages(self):
        """
        Instruction for the agent.
        """
        return [
            {
                "role": "system",
                "content": (
                    "You are a UK-based physical performance analyst working in elite football. "
                    "You explain player physical data clearly and directly in British English. "
                    "You operate in a strict physical tracking-data lane. "
                    "In scope: speed, acceleration, deceleration, top speed, sprinting, high-speed running, "
                    "distance, intensity, endurance, agility, and the four physical pillars and raw tracking metrics. "
                    "Out of scope: tactical positioning or system fit, technical quality such as shooting or passing, "
                    "mental traits such as leadership or composure, and team-context questions such as manager fit or teammates. "
                    "If a question is out of scope, use this pattern: acknowledge briefly, state the limit directly, "
                    "and redirect to the nearest physical angle. "
                    "If a question mixes in-scope and out-of-scope parts, answer only the physical part and clearly mark the rest as outside scope. "
                    "Never infer tactics, technique, mentality, or team fit from physical data. "
                    "Allowed answer types only: metric definition, attribute definition, player physical summary, "
                    "player-to-player physical comparison, clarification request, or scope refusal. "
                    "Do not answer with tactical advice, technical scouting, mental assessment, role fit, or general football opinion."
                ),
            },
            {
                "role": "user",
                "content": (
                    "After these messages you will be interacting with a user of a football physical analysis platform. "
                    "No player is selected by default. "
                    "If the user names a player, answer about that player's physical profile only. "
                    "If the user does not name a player, you can still answer generic questions about physical metrics, tracking definitions, and scope. "
                    "All user messages will be prefixed with 'User:' and enclosed with ```. "
                    "When responding to the user, speak directly to them. "
                    "Keep answers to 2 to 4 short sentences. "
                    "Do not deviate from the physical information provided. "
                    "If the available evidence does not support a safe physical-only answer, ask a short clarification question instead."
                ),
            },
        ]

    def resolve_player_context(self, query):
        if self.all_players_df is None:
            return None

        query_text = self.normalize_player_text(query)
        query_tokens = self.player_tokens(query)
        matches = []

        for _, row in self.all_players_df.iterrows():
            match_score = self.score_player_match(row, query_text, query_tokens)
            if match_score is None:
                continue

            matches.append((match_score, row))

        if not matches:
            self.pending_player_matches = []
            self.player_resolution_status = self.PLAYER_RESOLUTION_NONE
            return None

        matches.sort(
            key=lambda item: (
                item[0],
                str(item[1].get("Player", "")),
                str(item[1].get("Team", "")),
            ),
            reverse=True,
        )
        self.pending_player_matches = matches[:3]

        if self.is_ambiguous_player_match(matches):
            self.player_resolution_status = self.PLAYER_RESOLUTION_AMBIGUOUS
            return None

        _, player_row = matches[0]
        self.player_resolution_status = self.PLAYER_RESOLUTION_RESOLVED
        position_df = self.all_players_df[
            self.all_players_df["Position Group"] == player_row["Position Group"]
        ].reset_index(drop=True)
        raw_position_df = self.all_raw_df[
            self.all_raw_df["Position Group"] == player_row["Position Group"]
        ].reset_index(drop=True)
        return player_row, position_df, raw_position_df

    @staticmethod
    def normalize_player_text(text):
        text = str(text).strip().lower()
        text = unicodedata.normalize("NFKD", text)
        text = "".join(char for char in text if not unicodedata.combining(char))
        text = re.sub(r"[^a-z0-9]+", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def player_tokens(self, text):
        normalized = self.normalize_player_text(text)
        return {token for token in normalized.split() if len(token) > 1}

    def player_aliases(self, row):
        aliases = set()
        raw_names = [
            row.get("Player", ""),
            row.get("Short Name", ""),
        ]

        for raw_name in raw_names:
            normalized = self.normalize_player_text(raw_name)
            if not normalized:
                continue

            aliases.add(normalized)
            parts = normalized.split()
            if len(parts) >= 2:
                aliases.add(parts[-1])
                aliases.add(" ".join(parts[-2:]))
                aliases.add(f"{parts[0]} {parts[-1]}")

            if parts:
                initials = " ".join(part[0] for part in parts[:-1] if part)
                if initials:
                    aliases.add(f"{initials} {parts[-1]}")

        return {alias for alias in aliases if alias}

    def score_player_match(self, row, query_text, query_tokens):
        best_score = None

        for alias in self.player_aliases(row):
            alias_tokens = alias.split()
            if not alias_tokens:
                continue

            alias_pattern = r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])"
            if re.search(alias_pattern, query_text):
                score = (4, len(alias_tokens), len(alias))
            elif len(alias_tokens) >= 2 and all(token in query_tokens for token in alias_tokens):
                score = (3, len(alias_tokens), len(alias))
            elif len(alias_tokens) == 1 and len(alias_tokens[0]) >= 4 and alias_tokens[0] in query_tokens:
                score = (2, len(alias_tokens), len(alias))
            else:
                continue

            if best_score is None or score > best_score:
                best_score = score

        return best_score

    def maybe_update_player_context(self, query):
        resolved = self.resolve_player_context(query)
        if resolved is not None:
            self.player_row, self.position_df, self.raw_position_df = resolved
            self.name = self.player_row["Player"]
        else:
            self.name = self.player_row["Player"] if self.player_row is not None else "physical analyst"
        return resolved

    def is_ambiguous_player_match(self, matches):
        if len(matches) < 2:
            return False

        top_score = matches[0][0]
        second_score = matches[1][0]
        return top_score == second_score

    def needs_named_player(self, query):
        query_text = str(query).lower()
        player_specific_signals = [
            "his ",
            "he ",
            "player",
            "profile",
            "this guy",
            "this player",
            "is he",
            "does he",
            "can he",
        ]
        return any(signal in query_text for signal in player_specific_signals)

    def build_missing_player_response(self):
        return (
            "I do not have a player selected in this chat yet. "
            "Name a player if you want a player-specific physical profile, or ask a general question about the physical metrics."
        )

    def build_ambiguous_player_response(self):
        if not self.pending_player_matches:
            return self.build_missing_player_response()

        options = []
        for _, row in self.pending_player_matches[:3]:
            player = str(row.get("Player", "")).strip()
            team = str(row.get("Team", "")).strip()
            competition = str(row.get("Competition", "")).strip()
            details = ", ".join(part for part in [team, competition] if part)
            options.append(f"{player} ({details})" if details else player)

        return (
            "I can see more than one player matching that name. "
            f"Please specify which one you mean: {'; '.join(options)}."
        )

    def build_active_player_context(self):
        if self.player_row is None:
            return "No player is currently selected in the chat context."

        description = PhysicalDescription(
            self.player_row,
            self.position_df,
            self.raw_position_df,
            detailed=self.detailed,
        )
        return (
            "Active player context:\n"
            f"- Player: {self.player_row['Player']}\n"
            f"- Position group peer set: {self.player_row['Position Group']}\n\n"
            "Physical profile summary:\n"
            f"{description.synthesize_text()}"
        )

    def build_scope_context(self, scope):
        context = (
            "Scope rules:\n"
            "- In scope: speed, acceleration, top speed, sprinting, agility, endurance, distance, intensity, and raw tracking metrics.\n"
            "- Out of scope: tactical, technical, mental, and team-context questions.\n"
            "- Use only physical tracking data in the answer.\n"
        )
        if scope["matched_categories"]:
            context += (
                f"- This query also contains out-of-scope signals in: {', '.join(scope['matched_categories'])}.\n"
            )
        return context

    def infer_answer_type(self, query):
        query_text = self.normalize_player_text(query)
        if any(phrase in query_text for phrase in ("what does", "define", "explain", "mean")):
            return "definition"
        if "compare" in query_text or "vs" in query_text or "versus" in query_text:
            return "comparison"
        if self.player_row is not None:
            return "player_summary"
        return "generic_physical"

    def build_answer_contract_context(self, query):
        answer_type = self.infer_answer_type(query)
        return (
            "Answer contract:\n"
            f"- Expected answer type: {answer_type}\n"
            "- Allowed outputs: metric definition, attribute definition, player physical summary, player-to-player physical comparison, clarification request, or scope refusal.\n"
            "- Forbidden outputs: tactics, role fit, technical quality, mentality, team fit, manager fit, or general football opinion.\n"
            "- If uncertain, ask for clarification instead of inferring beyond the physical data."
        )

    def build_retrieved_evidence(self, query):
        retrieved = self.embeddings.search(query, top_n=5)
        if retrieved.empty:
            return "Retrieved physical evidence:\n- No additional retrieved physical evidence."

        evidence_lines = ["Retrieved physical evidence:"]
        for idx, (_, row) in enumerate(retrieved.iterrows(), start=1):
            evidence_lines.append(f"[{idx}] User question: {row['user']}")
            evidence_lines.append(f"[{idx}] Physical answer: {row['assistant']}")
        return "\n".join(evidence_lines)

    def build_comparison_context(self, comparison_query):
        left = comparison_query["left"]
        right = comparison_query["right"]

        left_description = PhysicalDescription(
            left["player_row"],
            left["position_df"],
            left["raw_position_df"],
            detailed=self.detailed,
        ).synthesize_text()
        right_description = PhysicalDescription(
            right["player_row"],
            right["position_df"],
            right["raw_position_df"],
            detailed=self.detailed,
        ).synthesize_text()

        return (
            "Comparison context:\n"
            f"- Player A: {left['player_row']['Player']} | {left['player_row']['Position Group']} | {left['player_row']['Team']}\n"
            f"- Player B: {right['player_row']['Player']} | {right['player_row']['Position Group']} | {right['player_row']['Team']}\n\n"
            f"Player A physical profile:\n{left_description}\n\n"
            f"Player B physical profile:\n{right_description}"
        )

    def classify_scope(self, query):
        tokens = set(re.findall(r"[a-z0-9]+", str(query).lower()))
        matched_categories = [
            category
            for category, keywords in self.OUT_OF_SCOPE_KEYWORDS.items()
            if tokens & keywords
        ]
        in_scope_hits = tokens & self.IN_SCOPE_KEYWORDS
        should_refuse = bool(matched_categories) and not bool(in_scope_hits)
        return {
            "matched_categories": matched_categories,
            "in_scope_hits": sorted(in_scope_hits),
            "should_refuse": should_refuse,
        }

    def route_query(self, query):
        scope = self.classify_scope(query)
        query_text = str(query).strip()
        if not query_text:
            return {
                "route": self.QUERY_ROUTE_UNCLEAR,
                "query": query_text,
                "scope": scope,
            }

        if self.is_comparison_query(query_text):
            comparison = self.resolve_comparison_players(query_text)
            if comparison["route"] != self.QUERY_ROUTE_UNCLEAR:
                return comparison

        if scope["in_scope_hits"] and not scope["matched_categories"]:
            return {
                "route": self.QUERY_ROUTE_PHYSICAL_ONLY,
                "query": query_text,
                "scope": scope,
            }

        if scope["matched_categories"] and not scope["in_scope_hits"]:
            return {
                "route": self.QUERY_ROUTE_NON_PHYSICAL,
                "query": query_text,
                "scope": scope,
            }

        if scope["matched_categories"] and scope["in_scope_hits"]:
            physical_query = self.extract_physical_subquery(query_text)
            if physical_query:
                return {
                    "route": self.QUERY_ROUTE_MIXED,
                    "query": physical_query,
                    "scope": scope,
                }
            return {
                "route": self.QUERY_ROUTE_UNCLEAR,
                "query": query_text,
                "scope": scope,
            }

        return {
            "route": self.QUERY_ROUTE_UNCLEAR,
            "query": query_text,
            "scope": scope,
        }

    def is_comparison_query(self, query_text):
        query_text = str(query_text).lower()
        if any(token in query_text for token in (" vs ", " versus ", " against ")):
            return True
        if any(token in query_text for token in (" compare ", " compared ")):
            return any(token in query_text for token in (" with ", " against ", " vs ", " versus "))
        return False

    def strip_comparison_preface(self, text):
        cleaned = self.normalize_player_text(text)
        cleaned = re.sub(r"^(compare|compared|vs|versus)\s+", "", cleaned).strip()
        cleaned = re.sub(r"^(the\s+)?physical\s+", "", cleaned).strip()
        return cleaned

    def resolve_player_from_fragment(self, fragment):
        fragment = self.strip_comparison_preface(fragment)
        if not fragment:
            return None
        return self.resolve_player_context(fragment)

    def resolve_comparison_players(self, query):
        cleaned_query = re.sub(r"\s+", " ", str(query)).strip()
        parts = re.split(r"\bvs\b|\bversus\b|\bagainst\b|\bwith\b", cleaned_query, flags=re.IGNORECASE)
        if len(parts) < 2:
            return {
                "route": self.QUERY_ROUTE_UNCLEAR,
                "query": cleaned_query,
                "scope": self.classify_scope(cleaned_query),
            }

        left_fragment = parts[0]
        right_fragment = " vs ".join(parts[1:])
        left_resolved = self.resolve_player_from_fragment(left_fragment)
        right_resolved = self.resolve_player_from_fragment(right_fragment)

        if left_resolved is None or right_resolved is None:
            return {
                "route": self.QUERY_ROUTE_UNCLEAR,
                "query": cleaned_query,
                "scope": self.classify_scope(cleaned_query),
            }

        left_player_row, left_position_df, left_raw_position_df = left_resolved
        right_player_row, right_position_df, right_raw_position_df = right_resolved

        if left_player_row["Player"] == right_player_row["Player"]:
            return {
                "route": self.QUERY_ROUTE_UNCLEAR,
                "query": cleaned_query,
                "scope": self.classify_scope(cleaned_query),
            }

        if (
            left_player_row is None
            or right_player_row is None
            or not str(left_player_row.get("Player", "")).strip()
            or not str(right_player_row.get("Player", "")).strip()
        ):
            return {
                "route": self.QUERY_ROUTE_UNCLEAR,
                "query": cleaned_query,
                "scope": self.classify_scope(cleaned_query),
            }

        return {
            "route": self.QUERY_ROUTE_COMPARISON,
            "query": cleaned_query,
            "scope": self.classify_scope(cleaned_query),
            "comparison": {
                "left": {
                    "player_row": left_player_row,
                    "position_df": left_position_df,
                    "raw_position_df": left_raw_position_df,
                },
                "right": {
                    "player_row": right_player_row,
                    "position_df": right_position_df,
                    "raw_position_df": right_raw_position_df,
                },
            },
        }

    def extract_physical_subquery(self, query):
        cleaned = re.sub(r"\s+", " ", str(query)).strip()
        if not cleaned:
            return None

        segments = [
            segment.strip(" ,.")
            for segment in re.split(r"\bbut\b|\band\b|[?.!;]", cleaned, flags=re.IGNORECASE)
            if segment.strip(" ,.")
        ]
        if not segments:
            segments = [cleaned]

        physical_segments = []
        for segment in segments:
            segment_scope = self.classify_scope(segment)
            if segment_scope["in_scope_hits"]:
                physical_segments.append(segment)

        if not physical_segments:
            return None

        return ". ".join(dict.fromkeys(physical_segments))

    def build_refusal_response(self, scope):
        category = scope["matched_categories"][0]
        category_labels = {
            "tactical": "tactical",
            "technical": "technical",
            "mental": "mental",
            "team_context": "team-context",
        }
        redirect_map = {
            "tactical": (
                "I can help with whether the player has the speed, recovery pace, agility, or endurance profile "
                "to support that job physically."
            ),
            "technical": (
                "I can help with the physical side instead, such as burst speed, acceleration, turning speed, "
                "or endurance."
            ),
            "mental": (
                "I can help with the physical engine and explosiveness profile, but not mentality or leadership."
            ),
            "team_context": (
                "I can help with the player's physical profile and how demanding the role looks physically, "
                "but not manager or dressing-room fit."
            ),
        }
        return (
            f"That is a {category_labels[category]} question, and I only have physical tracking data here. "
            f"{redirect_map[category]}"
        )

    def build_mixed_scope_response(self, scope, physical_query):
        category_labels = {
            "tactical": "tactical",
            "technical": "technical",
            "mental": "mental",
            "team_context": "team-context",
        }
        categories = ", ".join(category_labels[category] for category in scope["matched_categories"])
        return (
            f"Part of that question is outside scope because it moves into {categories}. "
            f"I will answer only the physical part: {physical_query}."
        )

    def build_unclear_scope_response(self):
        return (
            "I can only answer questions about physical tracking data here. "
            "Ask about speed, acceleration, agility, endurance, distance, intensity, or another physical metric."
        )

    def generate_response(self, messages, reasoning_effort=None, temperature=1, stream=False):
        if USE_GEMINI:
            import google.generativeai as genai

            converted_msgs = convert_messages_format(messages)
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel(
                model_name=GEMINI_CHAT_MODEL,
                system_instruction=converted_msgs["system_instruction"],
            )
            chat = model.start_chat(history=converted_msgs["history"])
            response = chat.send_message(content=converted_msgs["content"])
            return response.text

        if USE_LM_STUDIO:
            client = OpenAI(api_key=LM_STUDIO_API_KEY, base_url=LM_STUDIO_API_BASE)
            if stream:
                chunks = [
                    chunk.choices[0].delta.content
                    for chunk in client.chat.completions.create(
                        model=LM_STUDIO_CHAT_MODEL,
                        messages=messages,
                        temperature=temperature,
                        stream=True,
                    )
                    if chunk.choices and chunk.choices[0].delta.content
                ]

                def streamed_chunks():
                    yield from chunks

                return streamed_chunks()

            response = client.chat.completions.create(
                model=LM_STUDIO_CHAT_MODEL,
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content

        client = OpenAI(api_key=GPT_KEY, base_url=GPT_BASE)
        if stream:
            if GPT_SUPPORTS_REASONING:
                reasoning_effort = reasoning_effort if reasoning_effort in GPT_AVAILABLE_REASONING_EFFORTS else GPT_AVAILABLE_REASONING_EFFORTS[0]
                response_stream = client.responses.create(
                    model=GPT_CHAT_MODEL,
                    input=messages,
                    reasoning={"effort": reasoning_effort},
                    stream=True,
                )
            elif GPT_SUPPORTS_TEMPERATURE:
                response_stream = client.responses.create(
                    model=GPT_CHAT_MODEL,
                    input=messages,
                    temperature=temperature,
                    stream=True,
                )
            else:
                response_stream = client.responses.create(
                    model=GPT_CHAT_MODEL,
                    input=messages,
                    stream=True,
                )

            def streamed_chunks():
                for event in response_stream:
                    if event.type == "response.output_text.delta":
                        yield event.delta

            return streamed_chunks()

        if GPT_SUPPORTS_REASONING:
            reasoning_effort = reasoning_effort if reasoning_effort in GPT_AVAILABLE_REASONING_EFFORTS else GPT_AVAILABLE_REASONING_EFFORTS[0]
            response = client.responses.create(
                model=GPT_CHAT_MODEL,
                input=messages,
                reasoning={"effort": reasoning_effort},
            )
        elif GPT_SUPPORTS_TEMPERATURE:
            response = client.responses.create(
                model=GPT_CHAT_MODEL,
                input=messages,
                temperature=temperature,
            )
        else:
            response = client.responses.create(
                model=GPT_CHAT_MODEL,
                input=messages,
            )

        return response.output_text

    def handle_input(self, input, reasoning_effort=None, temperature=1, stream=False):
        routed_query = self.route_query(input)
        scope = routed_query["scope"]
        model_query = routed_query["query"]
        self.messages_to_display.append({"role": "user", "content": input})

        if routed_query["route"] == self.QUERY_ROUTE_NON_PHYSICAL:
            self.messages_to_display.append(
                {
                    "role": "assistant",
                    "content": self.build_refusal_response(scope),
                }
            )
            return

        if routed_query["route"] == self.QUERY_ROUTE_UNCLEAR:
            self.messages_to_display.append(
                {
                    "role": "assistant",
                    "content": self.build_unclear_scope_response(),
                }
            )
            return

        if routed_query["route"] == self.QUERY_ROUTE_MIXED:
            self.messages_to_display.append(
                {
                    "role": "assistant",
                    "content": self.build_mixed_scope_response(scope, model_query),
                }
            )

        self.maybe_update_player_context(model_query)

        if scope["should_refuse"]:
            self.messages_to_display.append(
                {
                    "role": "assistant",
                    "content": self.build_refusal_response(scope),
                }
            )
            return

        if self.player_resolution_status == self.PLAYER_RESOLUTION_AMBIGUOUS:
            self.messages_to_display.append(
                {
                    "role": "assistant",
                    "content": self.build_ambiguous_player_response(),
                }
            )
            return

        if routed_query["route"] == self.QUERY_ROUTE_COMPARISON:
            comparison = routed_query["comparison"]
            messages = self.instruction_messages()
            messages = messages + self.messages_to_display[:-1].copy()
            scope_context = self.build_scope_context(scope)
            answer_contract = self.build_answer_contract_context(model_query)
            comparison_context = self.build_comparison_context(comparison)
            retrieved_evidence = self.build_retrieved_evidence(model_query)
            messages.extend(
                [
                    {"role": "system", "content": scope_context},
                    {"role": "system", "content": answer_contract},
                    {"role": "system", "content": comparison_context},
                    {"role": "system", "content": retrieved_evidence},
                    {"role": "user", "content": f"```User: {model_query}```"},
                ]
            )
            messages = [
                message for message in messages if isinstance(message["content"], str)
            ]
            st.expander("Chat transcript", expanded=False).write(messages)
            answer = self.generate_response(messages, reasoning_effort, temperature, stream)
            self.messages_to_display.append({"role": "assistant", "content": answer})
            return

        if self.player_row is None and self.needs_named_player(input):
            self.messages_to_display.append(
                {
                    "role": "assistant",
                    "content": self.build_missing_player_response(),
                }
            )
            return

        messages = self.instruction_messages()
        messages = messages + self.messages_to_display[:-1].copy()
        scope_context = self.build_scope_context(scope)
        answer_contract = self.build_answer_contract_context(model_query)
        player_context = self.build_active_player_context()
        retrieved_evidence = self.build_retrieved_evidence(model_query)
        messages.extend(
            [
                {
                    "role": "system",
                    "content": scope_context,
                },
                {
                    "role": "system",
                    "content": answer_contract,
                },
                {
                    "role": "system",
                    "content": player_context,
                },
                {
                    "role": "system",
                    "content": retrieved_evidence,
                },
                {
                    "role": "user",
                    "content": f"```User: {model_query}```",
                },
            ]
        )
        messages = [
            message for message in messages if isinstance(message["content"], str)
        ]
        st.expander("Chat transcript", expanded=False).write(messages)
        answer = self.generate_response(messages, reasoning_effort, temperature, stream)
        self.messages_to_display.append({"role": "assistant", "content": answer})
