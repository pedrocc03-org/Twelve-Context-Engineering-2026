import streamlit as st
from openai import OpenAI
from itertools import groupby
from types import GeneratorType
import pandas as pd
import json
import re

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
                    "Never infer tactics, technique, mentality, or team fit from physical data."
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
                    "Do not deviate from the physical information provided."
                ),
            },
        ]

    def resolve_player_context(self, query):
        if self.all_players_df is None:
            return None

        query_text = str(query).lower()
        candidates = []
        for _, row in self.all_players_df.iterrows():
            player_name = str(row["Player"])
            short_name = str(row.get("Short Name", ""))
            for candidate in {player_name, short_name}:
                candidate = candidate.strip()
                if candidate and candidate.lower() in query_text:
                    candidates.append((len(candidate), row))

        if not candidates:
            return None

        _, player_row = max(candidates, key=lambda item: item[0])
        position_df = self.all_players_df[
            self.all_players_df["Position Group"] == player_row["Position Group"]
        ].reset_index(drop=True)
        raw_position_df = self.all_raw_df[
            self.all_raw_df["Position Group"] == player_row["Position Group"]
        ].reset_index(drop=True)
        return player_row, position_df, raw_position_df

    def maybe_update_player_context(self, query):
        resolved = self.resolve_player_context(query)
        if resolved is not None:
            self.player_row, self.position_df, self.raw_position_df = resolved
            self.name = self.player_row["Player"]
        return resolved

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

    def get_relevant_info(self, query):
        self.maybe_update_player_context(query)
        scope = self.classify_scope(query)
        retrieved = self.embeddings.search(query, top_n=5)

        ret_val = ""
        if self.player_row is not None:
            description = PhysicalDescription(
                self.player_row,
                self.position_df,
                self.raw_position_df,
                detailed=self.detailed,
            )
            ret_val += "Here is a description of the player in terms of physical data:\n\n"
            ret_val += description.synthesize_text()
            ret_val += "\n\nActive player context:\n"
            ret_val += f"- Player: {self.player_row['Player']}\n"
            ret_val += f"- Position group peer set: {self.player_row['Position Group']}\n"
        else:
            ret_val += "No player is currently selected in the chat context.\n"

        ret_val += "\n\nScope rules for this chat:\n"
        ret_val += "- In scope: speed, acceleration, top speed, sprinting, agility, endurance, distance, intensity, and raw tracking metrics.\n"
        ret_val += "- Out of scope: tactical, technical, mental, and team-context questions.\n"
        if scope["matched_categories"]:
            ret_val += (
                f"- This query includes out-of-scope signals in: {', '.join(scope['matched_categories'])}. "
                "If needed, refuse that part and redirect to the nearest physical angle.\n"
            )

        if not retrieved.empty:
            ret_val += "\nRetrieved physical knowledge for this question:\n"
            for _, row in retrieved.iterrows():
                ret_val += f"- Q: {row['user']}\n  A: {row['assistant']}\n"

        ret_val += (
            "\n\nIf the user's question goes beyond this physical report, remind them that "
            "this chat can answer questions about the selected player's speed, acceleration, agility, endurance, "
            "and the supporting raw physical metrics shown on the page."
        )
        return ret_val

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

    def handle_input(self, input, reasoning_effort=None, temperature=1, stream=False):
        scope = self.classify_scope(input)
        self.messages_to_display.append({"role": "user", "content": input})
        self.maybe_update_player_context(input)

        if scope["should_refuse"]:
            self.messages_to_display.append(
                {
                    "role": "assistant",
                    "content": self.build_refusal_response(scope),
                }
            )
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
        relevant_info = self.get_relevant_info(input)
        messages.append(
            {
                "role": "user",
                "content": f"Here is the relevant information to answer the users query: {relevant_info}\n\n```User: {input}```",
            }
        )
        messages = [
            message for message in messages if isinstance(message["content"], str)
        ]
        st.expander("Chat transcript", expanded=False).write(messages)

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
            answer = response.text
        elif USE_LM_STUDIO:
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

        self.messages_to_display.append({"role": "assistant", "content": answer})
