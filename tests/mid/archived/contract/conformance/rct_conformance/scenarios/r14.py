# Mid-tier source from contract/conformance/rct_conformance/scenarios/r14.py; see MID_TIER.md.
# Shared helpers and refusal entry points remain at the original path.

# TEST-TIER-DISABLED-BEGIN contract/conformance/rct_conformance/scenarios/r14.py::run
# def run(home: ScenarioHome) -> None:
#     home.part("earlier")
#     earlier = home.start("earlier message")
#     chat = finish(home, earlier)["chat"]
#     home.part("original")
#     first = home.start("send this again", request={"chat": chat})
#     first_answer = finish(home, first)
#     original_request = request(home, "original")
#     old = home.rows(f"SELECT * FROM exchanges WHERE id = '{first.exchange}'")[0]
#     old_runs = home.rows(f"SELECT * FROM runs WHERE exchange_id = '{first.exchange}' ORDER BY run_id")
#     check(old_runs, "The original Exchange has no usage to preserve.")
#
#     home.part("replacement")
#     second = home.start(None, request={"replaces": first.exchange})
#     answer = finish(home, second)
#     equal((answer["chat"], answer["number"]), (chat, first_answer["number"] + 1), "The replacement's chat and number")
#     equal(home.rows(f"SELECT text FROM messages WHERE exchange_id = '{second.exchange}' AND position = 0"),
#           [{"text": "send this again"}], "The copied message")
#     equal(home.rows(f"SELECT * FROM exchanges WHERE id = '{first.exchange}'"), [{**old, "replaced_by": second.exchange}],
#           "Only replaced_by changed in the old Exchange")
#     equal(home.rows(f"SELECT * FROM messages WHERE exchange_id = '{first.exchange}'"), [], "Old messages deleted")
#     equal(home.rows(f"SELECT * FROM tool_calls WHERE exchange_id = '{first.exchange}'"), [], "Old calls deleted")
#     equal(home.rows(f"SELECT * FROM runs WHERE exchange_id = '{first.exchange}' ORDER BY run_id"), old_runs,
#           "Old usage preserved")
#     new_request = request(home, "replacement")
#     equal(new_request["input"], original_request["input"], "The replacement's Driver input")
#     equal(new_request["history"], original_request["history"], "The history after the old answer is discarded")
#     check(new_request["history"], "The replacement discarded earlier Exchanges too.")
#
#     home.part("next")
#     next_message = home.start("a next message", request={"chat": chat})
#     finish(home, next_message)
#     following = request(home, "next")["history"]
#     equal(following[:len(new_request["history"])], new_request["history"], "Earlier history remains")
#     check("original answer" not in json.dumps(following) and "echo original" not in json.dumps(following),
#           "The next request contains the replaced answer or tool call.")
#     check("replacement answer" in json.dumps(following) and "echo replacement" in json.dumps(following),
#           "The next request lost the new answer or tool call.")
#     refused(home, earlier.exchange, "cannot_replace")
#     refused(home, first.exchange, "cannot_replace")
#     refused(home, next_message.exchange, "invalid_input", chat=str(uuid.uuid4()))
#     refused(home, next_message.exchange, "invalid_input", message="an edited message")
#     refused(home, str(uuid.uuid4()), "not_found")
#
#     last = race(home, next_message, chat, two_replacements=False)
#     last = race(home, last, chat, two_replacements=True)
#     home.part("open")
#     opened = home.start("still open", request={"chat": chat})
#     accepted(opened)
#     refused(home, opened.exchange, "cannot_replace")
#     home.release()
#     finish(home, opened)
# TEST-TIER-DISABLED-END contract/conformance/rct_conformance/scenarios/r14.py::run

# TEST-TIER-IMPORTS-BEGIN contract/conformance/rct_conformance/scenarios/r14.py:5
# import json
# TEST-TIER-IMPORTS-END contract/conformance/rct_conformance/scenarios/r14.py:5

raise RuntimeError("Mid-tier checks require an explicitly requested testing task; see MID_TIER.md.")
