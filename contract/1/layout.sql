-- Root Contract, version 1: the chat tables (RCT-3).
-- Kept in the arbol-root repository as contract/1/layout.sql.
-- arbol-roots runs it with: psql --no-psqlrc --set ON_ERROR_STOP=1 --single-transaction --file layout.sql
-- Every statement can run again: on a database that already has everything, the file changes nothing.
-- No program creates or changes a table any other way. Each program writes its rows with SQL of its own.

CREATE TABLE IF NOT EXISTS chats (
  id          uuid        PRIMARY KEY,
  title       text        CHECK (title IS NULL OR char_length(title) BETWEEN 1 AND 240),
  created_at  timestamptz NOT NULL
);
COMMENT ON TABLE chats IS 'One row for each chat. Written by the Trunk that accepts its first message; the title also by Arbol.';
COMMENT ON COLUMN chats.id IS 'The chat''s identifier, a UUID chosen by the caller or by the Trunk, for example c3d4e5f6-0718-4293-a4b5-c6d7e8f90a1b.';
COMMENT ON COLUMN chats.title IS 'The chat''s one title, 1 to 240 characters; NULL while it has none. Arbol writes it when the Leather Bag changes it; a Trunk that makes titles writes it under the rule of its own specification.';
COMMENT ON COLUMN chats.created_at IS 'When the Trunk accepted the chat''s first message.';

CREATE TABLE IF NOT EXISTS exchanges (
  id                uuid        PRIMARY KEY,
  chat_id           uuid        NOT NULL REFERENCES chats (id) ON DELETE RESTRICT,
  number            integer     NOT NULL CHECK (number >= 1),
  state             text        NOT NULL CHECK (state IN ('open', 'completed', 'failed', 'cancelled', 'interrupted')),
  error             jsonb,
  trunk             text        NOT NULL CHECK (trunk ~ '^[a-z][a-z0-9]{0,31}$'),
  build             text        NOT NULL CHECK (build ~ '^(0|[1-9a-f][0-9a-f]*)$'),
  route             jsonb       NOT NULL CHECK (jsonb_typeof(route) = 'object'),
  small_call_route  jsonb       CHECK (small_call_route IS NULL OR jsonb_typeof(small_call_route) = 'object'),
  working_folder    text        NOT NULL CHECK (working_folder LIKE '/%'),
  accepted_at       timestamptz NOT NULL,
  ended_at          timestamptz,
  replaced_by       uuid        REFERENCES exchanges (id) ON DELETE RESTRICT,
  UNIQUE (chat_id, number),
  CHECK ((state = 'open') = (ended_at IS NULL)),
  CHECK ((state = 'failed') = (error IS NOT NULL)),
  CHECK (replaced_by IS NULL OR (replaced_by <> id AND state <> 'open'))
);
CREATE UNIQUE INDEX IF NOT EXISTS exchanges_one_open_per_chat ON exchanges (chat_id) WHERE state = 'open';
COMMENT ON TABLE exchanges IS 'One row for each accepted Chat Exchange. Written by the Trunk that accepted it, or by the Trunk Build that settles it.';
COMMENT ON INDEX exchanges_one_open_per_chat IS 'At most one open Exchange in a chat: a second message to a busy chat is refused with chat_busy.';
COMMENT ON COLUMN exchanges.id IS 'The Exchange''s identifier, a UUID, the same as the name of its folder, for example 7f3a2c1e-4b5d-4e6f-8a9b-0c1d2e3f4a5b.';
COMMENT ON COLUMN exchanges.chat_id IS 'The chat the Exchange belongs to.';
COMMENT ON COLUMN exchanges.number IS 'The Exchange''s place in its chat: 1 for the first, then 2, 3 and so on, including replaced Exchanges. Two messages to one chat at the same moment cannot both take the same number, so one of them is refused with chat_busy.';
COMMENT ON COLUMN exchanges.state IS 'open from acceptance until the end; then completed, failed, cancelled, or interrupted when its process died before it ended. An ended Exchange never changes state again.';
COMMENT ON COLUMN exchanges.error IS 'Why it failed, present exactly when state is failed: the Driver''s error object as the Driver wrote it (DRV-4), for example {"code": "rate_limited", "message": "…", "retryable": true}, or {"code", "message"} with a code of the Root Contract, such as events_file_full.';
COMMENT ON COLUMN exchanges.trunk IS 'The code name of the Trunk that accepted it, for example trivial. Never changes.';
COMMENT ON COLUMN exchanges.build IS 'The build number of the Trunk Build that accepted it, for example 3; 0 for a program outside a Build, as in development (BLD-0). Never changes.';
COMMENT ON COLUMN exchanges.route IS 'The route the Trunk was handed (ARC-0), for example {"driver": "claude", "subscription": "anthropic", "model": "sonnet", "effort": "high"}; only what was handed, so a Trunk started by hand may have fewer fields. What each run used is in runs.started.';
COMMENT ON COLUMN exchanges.small_call_route IS 'The small-call route the Trunk was handed, in the same form as route; NULL when none was handed, and then the Trunk made no small text call.';
COMMENT ON COLUMN exchanges.working_folder IS 'The absolute folder the agent worked in, for example /Users/sam/repos/shop.';
COMMENT ON COLUMN exchanges.accepted_at IS 'When the Trunk accepted the message.';
COMMENT ON COLUMN exchanges.ended_at IS 'When the Exchange ended; NULL exactly while it is open. For an interrupted Exchange, the time of the last line of its events.jsonl that carries one (the at of an event or a smallRun), or accepted_at when the file had none; for an Exchange that a migration wrote as interrupted, the time of the migration snapshot (RTM-1).';
COMMENT ON COLUMN exchanges.replaced_by IS 'When the Leather Bag sent the message again: the Exchange that runs it again. A replaced Exchange is never shown in the chat and never sent to an agent. Written once, by the Trunk that accepts the new Exchange, which in the same transaction deletes the replaced Exchange''s messages and tool calls; its runs stay, so its tokens still count.';

CREATE TABLE IF NOT EXISTS messages (
  exchange_id  uuid    NOT NULL REFERENCES exchanges (id) ON DELETE RESTRICT,
  position     integer NOT NULL CHECK (position >= 0),
  role         text    NOT NULL CHECK (role IN ('user', 'assistant')),
  text         text    NOT NULL,
  PRIMARY KEY (exchange_id, position),
  CHECK ((position = 0) = (role = 'user'))
);
COMMENT ON TABLE messages IS 'The Leather Bag''s message and the agent''s answer, one row for each block of text. Written by the Trunk, or by the Trunk Build that settles the Exchange.';
COMMENT ON COLUMN messages.exchange_id IS 'The Exchange the message belongs to.';
COMMENT ON COLUMN messages.position IS 'Where the message stands in its Exchange: 0 for the Leather Bag''s message; for a block of the answer, the number n of the line of events.jsonl that carried it, for example 17.';
COMMENT ON COLUMN messages.role IS 'user for the Leather Bag''s message, assistant for a block of the answer.';
COMMENT ON COLUMN messages.text IS 'The text exactly as it was sent, or exactly as the Driver''s text event carried it (DRV-2), except that the character U+0000 and every half of a surrogate pair that stands alone are replaced with U+FFFD (RCT-3).';

CREATE TABLE IF NOT EXISTS tool_calls (
  exchange_id     uuid    NOT NULL REFERENCES exchanges (id) ON DELETE RESTRICT,
  position        integer NOT NULL CHECK (position >= 1),
  run_id          text    NOT NULL,
  call_id         text    NOT NULL,
  parent_call_id  text,
  name            text    NOT NULL,
  input           jsonb   NOT NULL,
  ok              boolean NOT NULL,
  result          jsonb,
  error           text,
  truncated       boolean NOT NULL DEFAULT false,
  interrupted     boolean NOT NULL DEFAULT false,
  ask             jsonb,
  answer          jsonb,
  PRIMARY KEY (exchange_id, position)
);
COMMENT ON TABLE tool_calls IS 'One row for each tool call the agent made, with its result; a question to the Leather Bag is a tool call too. Written by the Trunk when the call has finished, or by the Trunk Build that settles the Exchange.';
COMMENT ON COLUMN tool_calls.exchange_id IS 'The Exchange the call belongs to.';
COMMENT ON COLUMN tool_calls.position IS 'Where the call stands in its Exchange: the number n of the line of events.jsonl that carried its tool_started event, for example 18.';
COMMENT ON COLUMN tool_calls.run_id IS 'The Driver run that made the call (DRV-2 runId).';
COMMENT ON COLUMN tool_calls.call_id IS 'The call''s identifier within its run, as the Driver gave it (DRV-2 callId).';
COMMENT ON COLUMN tool_calls.parent_call_id IS 'For a call a sub-agent made: the call that started the sub-agent (DRV-3 parentCallId); NULL for the agent''s own calls.';
COMMENT ON COLUMN tool_calls.name IS 'The tool''s name, for example shell or Read (DRV-3).';
COMMENT ON COLUMN tool_calls.input IS 'The input as the Driver''s tool_started event carried it, for example {"command": "ls"}.';
COMMENT ON COLUMN tool_calls.ok IS 'As tool_finished said: true when the call succeeded. false for a call that the end of its Exchange cut off before its tool_finished.';
COMMENT ON COLUMN tool_calls.result IS 'The result as the Driver''s tool_finished event carried it, for example {"output": "build.sh\n", "exitCode": 0}; NULL when the event had none.';
COMMENT ON COLUMN tool_calls.error IS 'The error text of a failed call, as tool_finished carried it; NULL when it had none.';
COMMENT ON COLUMN tool_calls.truncated IS 'true when the Driver cut the result to its size limit (DRV-2).';
COMMENT ON COLUMN tool_calls.interrupted IS 'true when the call was cut off: as tool_finished said after a stop, or because the Exchange ended before the call finished.';
COMMENT ON COLUMN tool_calls.ask IS 'For a question the agent asked the Leather Bag: the question as the ask_opened event carried it (DRV-3), for example {"callId": "call_7", "questions": [{"id": "branch", "question": "Which branch should I push to?", "multiple": false, "options": [{"label": "main"}, {"label": "dev"}]}]}; NULL for any other call.';
COMMENT ON COLUMN tool_calls.answer IS 'For a question: the Leather Bag''s answer as the answer line carried it (DRV-3), for example {"type": "answers", "answers": {"branch": ["main"]}} or {"type": "decline"}; NULL for any other call, and for a question that was withdrawn before it was answered.';

CREATE TABLE IF NOT EXISTS runs (
  exchange_id  uuid        NOT NULL REFERENCES exchanges (id) ON DELETE RESTRICT,
  run_id       text        NOT NULL,
  kind         text        NOT NULL DEFAULT 'agent' CHECK (kind IN ('agent', 'small')),
  outcome      text        NOT NULL CHECK (outcome IN ('completed', 'failed', 'cancelled', 'interrupted')),
  usage        jsonb       NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(usage) = 'object'),
  error        jsonb,
  started      jsonb,
  ended_at     timestamptz NOT NULL,
  PRIMARY KEY (exchange_id, run_id),
  CHECK ((outcome = 'failed') = (error IS NOT NULL))
);
COMMENT ON TABLE runs IS 'One row for each Driver run of the Exchange, the agent''s runs and the runs of its small calls, with its token usage. Written by the Trunk when the run has ended, or by the Trunk Build that settles the Exchange.';
COMMENT ON COLUMN runs.exchange_id IS 'The Exchange the run belongs to.';
COMMENT ON COLUMN runs.run_id IS 'The run''s identifier, as the Trunk gave it to the Driver (DRV-2 runId).';
COMMENT ON COLUMN runs.kind IS 'agent for a run of the agent''s work; small for a small call, such as a title, made on the small-call route (ARC-0).';
COMMENT ON COLUMN runs.outcome IS 'completed, failed or cancelled, as the Driver''s finished event said; interrupted when no finished event reached the Trunk.';
COMMENT ON COLUMN runs.usage IS 'The run''s token and cost totals in the Driver''s form (DRV-2 RunUsage), for example {"model": "sonnet", "inputTokens": 5120, "outputTokens": 812}; {} when the Driver reported none.';
COMMENT ON COLUMN runs.error IS 'The Driver''s error object of a failed run (DRV-4); present exactly when outcome is failed.';
COMMENT ON COLUMN runs.started IS 'The run''s started event as the Driver wrote it, which names the Subscription, the model, the effort and the Driver Build the run used (DRV-2); NULL for a small call, and when no started event reached the Trunk.';
COMMENT ON COLUMN runs.ended_at IS 'The time of the run''s finished event, or of its last event when it had none.';
