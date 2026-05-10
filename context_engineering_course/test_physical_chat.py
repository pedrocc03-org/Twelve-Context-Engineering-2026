"""
Deterministic regression checks for the Physical Analyst chat stack.

Purpose:
- Verify physical-only scope routing.
- Verify player resolution and ambiguity handling.
- Verify physical retrieval ranks the right evidence first.

Usage:
- Run: `python context_engineering_course/test_physical_chat.py`
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from classes.chat import PhysicalChat
from classes.embeddings import PhysicalEmbeddings
from pages.physical.data import load_data, load_raw_data


def make_chat():
    return PhysicalChat(
        chat_state_hash=1,
        player_row=None,
        position_df=None,
        raw_position_df=None,
        all_players_df=load_data(),
        all_raw_df=load_raw_data(),
        detailed=False,
    )


def assert_equal(actual, expected, message):
    if actual != expected:
        raise AssertionError(f"{message}: expected {expected!r}, got {actual!r}")


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_scope_routing():
    chat = make_chat()

    routed = chat.route_query("What does top speed mean?")
    assert_equal(routed["route"], chat.QUERY_ROUTE_PHYSICAL_ONLY, "Top speed query should be physical")

    routed = chat.route_query("Is he a good finisher?")
    assert_equal(routed["route"], chat.QUERY_ROUTE_NON_PHYSICAL, "Finishing query should be non-physical")

    routed = chat.route_query("How quick is he and would he fit a high press?")
    assert_equal(routed["route"], chat.QUERY_ROUTE_MIXED, "Mixed query should be routed as mixed")
    assert_equal(routed["query"], "How quick is he", "Mixed query should retain only the physical clause")

    routed = chat.route_query("Tell me about him")
    assert_equal(routed["route"], chat.QUERY_ROUTE_UNCLEAR, "Vague query should be unclear")

    routed = chat.route_query("Compare Adam Armstrong vs Sinclair Armstrong physically")
    assert_equal(routed["route"], chat.QUERY_ROUTE_COMPARISON, "Comparison query should route as comparison")
    assert_equal(
        routed["comparison"]["left"]["player_row"]["Player"],
        "Adam Armstrong",
        "Left comparison player should be Adam Armstrong",
    )
    assert_equal(
        routed["comparison"]["right"]["player_row"]["Player"],
        "Sinclair Armstrong",
        "Right comparison player should be Sinclair Armstrong",
    )


def test_player_resolution():
    chat = make_chat()

    chat.maybe_update_player_context("Acceleration and agility for Adam Armstrong")
    assert_equal(chat.player_resolution_status, chat.PLAYER_RESOLUTION_RESOLVED, "Adam Armstrong should resolve")
    assert_equal(chat.player_row["Player"], "Adam Armstrong", "Resolved player should be Adam Armstrong")

    chat.maybe_update_player_context("How does Armstrong look physically?")
    assert_equal(
        chat.player_resolution_status,
        chat.PLAYER_RESOLUTION_AMBIGUOUS,
        "Surname-only Armstrong should be ambiguous",
    )
    pending_players = [row["Player"] for _, row in chat.pending_player_matches]
    assert_true("Adam Armstrong" in pending_players, "Ambiguous candidates should include Adam Armstrong")
    assert_true("Sinclair Armstrong" in pending_players, "Ambiguous candidates should include Sinclair Armstrong")

    chat.maybe_update_player_context("Tell me about A. Cresswell speed")
    assert_equal(chat.player_resolution_status, chat.PLAYER_RESOLUTION_RESOLVED, "A. Cresswell should resolve")
    assert_equal(chat.player_row["Player"], "Aaron Cresswell", "Resolved player should be Aaron Cresswell")


def test_retrieval_ranking():
    embeddings = PhysicalEmbeddings()

    results = embeddings.search("What does top speed mean?", top_n=1)
    assert_true(not results.empty, "Top speed retrieval should return at least one result")
    assert_equal(results.iloc[0]["user"], "What does top speed mean?", "Top speed query should rank exact metric first")

    results = embeddings.search("Explain acceleration in the physical analyst", top_n=1)
    assert_true(not results.empty, "Acceleration retrieval should return at least one result")
    assert_equal(
        results.iloc[0]["user"],
        "What does acceleration mean in the physical analyst?",
        "Acceleration query should rank attribute definition first",
    )

    results = embeddings.search("Define high-speed running distance", top_n=1)
    assert_true(not results.empty, "HSR distance retrieval should return at least one result")
    assert_equal(
        results.iloc[0]["user"],
        "What does high-speed running distance mean?",
        "HSR distance query should rank the exact metric definition first",
    )


def test_answer_contract_inference():
    chat = make_chat()

    answer_type = chat.infer_answer_type("What does top speed mean?")
    assert_equal(answer_type, "definition", "Definition query should infer definition answer type")

    chat.maybe_update_player_context("Acceleration and agility for Adam Armstrong")
    answer_type = chat.infer_answer_type("How quick is he?")
    assert_equal(answer_type, "player_summary", "Named-player follow-up should infer player summary answer type")

    answer_type = chat.infer_answer_type("Compare Adam Armstrong vs Sinclair Armstrong physically")
    assert_equal(answer_type, "comparison", "Comparison query should infer comparison answer type")


def test_comparison_context():
    chat = make_chat()
    routed = chat.route_query("Compare Adam Armstrong vs Sinclair Armstrong physically")
    context = chat.build_comparison_context(routed["comparison"])
    assert_true("Player A physical profile" in context, "Comparison context should include player A profile")
    assert_true("Player B physical profile" in context, "Comparison context should include player B profile")


def main():
    test_scope_routing()
    test_player_resolution()
    test_retrieval_ranking()
    test_answer_contract_inference()
    test_comparison_context()
    print("Physical chat regression checks passed.")


if __name__ == "__main__":
    main()
