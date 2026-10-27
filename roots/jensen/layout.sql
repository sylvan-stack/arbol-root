-- The second Root's own tables (RTM-1).
-- Kept in the arbol-root repository as roots/jensen/layout.sql; the second Root's arbol-root Builds carry it as layout/root-tables.sql.
-- arbol-roots runs it after the chat tables: psql --no-psqlrc --set ON_ERROR_STOP=1 --single-transaction --file root-tables.sql
-- Every statement can run again: on a database that already has everything, the file changes nothing.
-- Arbol's own tables, such as Drafts, are added to this file by Arbol's specification.

CREATE TABLE IF NOT EXISTS migrated_chats (
  chat_id        uuid        PRIMARY KEY REFERENCES chats (id) ON DELETE RESTRICT,
  from_root      text        NOT NULL,
  from_chat      uuid        NOT NULL,
  ended_through  integer     NOT NULL CHECK (ended_through >= 0),
  migrated_at    timestamptz NOT NULL
);
COMMENT ON TABLE migrated_chats IS 'One row for each chat that a migration brought into this Root: where it came from and how far the original had got. Written once, by the migration script.';
COMMENT ON COLUMN migrated_chats.chat_id IS 'The chat in this Root, for example c3d4e5f6-0718-4293-a4b5-c6d7e8f90a1b.';
COMMENT ON COLUMN migrated_chats.from_root IS 'The identifier of the Root it came from, for example sapling.';
COMMENT ON COLUMN migrated_chats.from_chat IS 'The chat''s identifier in that Root; the same as chat_id for a chat copied as it was.';
COMMENT ON COLUMN migrated_chats.ended_through IS 'How far the original had got when it was read: the number of its last Exchange that had ended, 0 when none had.';
COMMENT ON COLUMN migrated_chats.migrated_at IS 'When the older database was read: the moment of the snapshot the copy shows.';

-- Compatible addition for comparing and refreshing migrated copies (RTM-1.12).
ALTER TABLE migrated_chats ADD COLUMN IF NOT EXISTS stale boolean NOT NULL DEFAULT false;
COMMENT ON COLUMN migrated_chats.stale IS 'Whether the original has a later ended Exchange than ended_through; changed only by an explicit comparison or successful reimport.';

-- The Arbol backend's own tables (BKD-0). Written by the Arbol backend alone.

CREATE SEQUENCE IF NOT EXISTS drafts_revision;
COMMENT ON SEQUENCE drafts_revision IS 'The one counter of the revisions of every Draft, so that no revision is given twice, also after a Draft was removed.';

CREATE TABLE IF NOT EXISTS drafts (
  id              uuid        PRIMARY KEY,
  chat_id         uuid        UNIQUE REFERENCES chats (id) ON DELETE RESTRICT,
  folder          text        UNIQUE CHECK (folder IS NULL OR folder LIKE '/%'),
  text            text        NOT NULL,
  revision        bigint      NOT NULL CHECK (revision >= 1),
  sent_as         uuid,
  sent_request    jsonb       CHECK (sent_request IS NULL OR jsonb_typeof(sent_request) = 'object'),
  updated_at      timestamptz NOT NULL,
  CHECK ((chat_id IS NULL) <> (folder IS NULL)),
  CHECK ((sent_as IS NULL) = (sent_request IS NULL))
);
COMMENT ON TABLE drafts IS 'What the Leather Bag typed in a composer and has not sent: one Draft of the reply for each chat, and one Draft of a new chat for each repository folder. Written by the Arbol backend alone (BKD-0).';
COMMENT ON COLUMN drafts.id IS 'The Draft''s own identifier, a UUID the backend gives it.';
COMMENT ON COLUMN drafts.chat_id IS 'For the Draft of a reply: its chat, for example c3d4e5f6-0718-4293-a4b5-c6d7e8f90a1b; NULL for the Draft of a new chat.';
COMMENT ON COLUMN drafts.folder IS 'For the Draft of a new chat: the absolute folder of its repository, for example /Users/sam/repos/shop; NULL for the Draft of a reply.';
COMMENT ON COLUMN drafts.text IS 'The text as the Leather Bag typed it, exactly.';
COMMENT ON COLUMN drafts.revision IS 'A new value of drafts_revision each time the Draft is saved. A save names the revision it was made over and is refused when that is no longer the Draft''s.';
COMMENT ON COLUMN drafts.sent_as IS 'The Exchange this Draft was sent as and not yet accepted or refused, for example 9b3a2c1e-5c6d-4f70-9a1b-2c3d4e5f6a7b; NULL when it is not being sent. Cleared by a save, which brings new text. The Draft is removed once that Exchange is in the chat tables.';
COMMENT ON COLUMN drafts.sent_request IS 'With sent_as: what the Draft was sent with, so that a send left half done can be made again with the same Exchange, for example {"chat": "c3d4e5f6-…", "route": {"driver": "claude", "subscription": "anthropic", "model": "sonnet"}, "workingFolder": "/Users/sam/repos/sylvan-stack/readonly/shop"}.';
COMMENT ON COLUMN drafts.updated_at IS 'When the Draft was last saved.';

CREATE TABLE IF NOT EXISTS chat_settings (
  chat_id         uuid        PRIMARY KEY REFERENCES chats (id) ON DELETE RESTRICT,
  route           jsonb       CHECK (route IS NULL OR jsonb_typeof(route) = 'object'),
  working_folder  text        CHECK (working_folder IS NULL OR working_folder LIKE '/%'),
  updated_at      timestamptz NOT NULL
);
COMMENT ON TABLE chat_settings IS 'What the Leather Bag picked for a chat''s next message, where it differs from the chat''s last Exchange. Written by the Arbol backend alone (BKD-0).';
COMMENT ON COLUMN chat_settings.chat_id IS 'The chat.';
COMMENT ON COLUMN chat_settings.route IS 'The route picked for the next message, in the form of ARC-0, for example {"driver": "claude", "subscription": "anthropic", "model": "sonnet", "effort": "high"}; NULL: the route of the last Exchange.';
COMMENT ON COLUMN chat_settings.working_folder IS 'The absolute folder picked for the next message, for example /Users/sam/repos/shop; NULL: the folder of the last Exchange.';
COMMENT ON COLUMN chat_settings.updated_at IS 'When a choice was last saved.';

CREATE TABLE IF NOT EXISTS chat_marks (
  chat_id      uuid        PRIMARY KEY REFERENCES chats (id) ON DELETE RESTRICT,
  ongoing      boolean     NOT NULL DEFAULT false,
  archived_at  timestamptz,
  updated_at   timestamptz NOT NULL
);
COMMENT ON TABLE chat_marks IS 'The marks the Leather Bag gives a chat in Elma Chat. Written by the Arbol backend alone (BKD-0).';
COMMENT ON COLUMN chat_marks.chat_id IS 'The chat.';
COMMENT ON COLUMN chat_marks.ongoing IS 'true while the Leather Bag marks the chat as one still being worked on (Elma Chat, Ongoing).';
COMMENT ON COLUMN chat_marks.archived_at IS 'When the Leather Bag archived the chat; NULL while it is not archived. An archived chat leaves the latest chats.';
COMMENT ON COLUMN chat_marks.updated_at IS 'When a mark was last changed.';

CREATE TABLE IF NOT EXISTS exchange_notes (
  exchange_id  uuid        NOT NULL REFERENCES exchanges (id) ON DELETE RESTRICT,
  kind         text        NOT NULL CHECK (kind IN ('ended_stuck')),
  at           timestamptz NOT NULL,
  PRIMARY KEY (exchange_id, kind)
);
COMMENT ON TABLE exchange_notes IS 'What Arbol says about an Exchange that the chat tables do not hold. Written by the Arbol backend alone (BKD-0).';
COMMENT ON COLUMN exchange_notes.exchange_id IS 'The Exchange the note is about.';
COMMENT ON COLUMN exchange_notes.kind IS 'ended_stuck: the backend ended the Exchange by force because its heartbeat stood still (ARC-3).';
COMMENT ON COLUMN exchange_notes.at IS 'When the backend decided it.';

-- Subscriptions Vigor's records (SGM-1, "The calculation record"). Written by the Arbol process alone, the backend and
-- `arbol vigor`. They belong to the Root where they were made and are not copied when the Root changes (SGM-D29).

CREATE TABLE IF NOT EXISTS vigor_profiles (
  version      integer          PRIMARY KEY CHECK (version >= 1),
  approval     text             NOT NULL CHECK (approval IN ('proposed', 'approved')),
  pace         text             NOT NULL,
  placeholder  double precision NOT NULL CHECK (placeholder >= 0 AND placeholder <= 1),
  gates        jsonb            NOT NULL CHECK (jsonb_typeof(gates) = 'array'),
  stale_rule   text             NOT NULL,
  recorded_at  timestamptz      NOT NULL
);
COMMENT ON TABLE vigor_profiles IS 'The versioned choices of a Vigor calculation, in the shape of SGM-0''s profile: the pace assumption, the gate weights and the stale rule. Version 1 is the first profile, proposed, with the placeholder 0.1. Written by the Arbol process alone (SGM-1).';
COMMENT ON COLUMN vigor_profiles.version IS 'The profile''s version, for example 1; a result names the version it was computed by.';
COMMENT ON COLUMN vigor_profiles.approval IS 'proposed until the owner approves the profile for operation, approved afterwards (SGM-D15, SGM-D17).';
COMMENT ON COLUMN vigor_profiles.pace IS 'The pace the loss assumes, for example even: the window''s even pace, which drains the bucket exactly by its reset.';
COMMENT ON COLUMN vigor_profiles.placeholder IS 'The weight of every gate without a learned weight, 0 to 1, marked placeholder: 0.1 until a learned weight is approved (SGM-D15).';
COMMENT ON COLUMN vigor_profiles.gates IS 'The learned gate weights with their marking, a list of objects such as [{"family": "anthropic", "label": "Five hours", "value": 0.12, "source": "learned"}]; empty while every gate uses the placeholder.';
COMMENT ON COLUMN vigor_profiles.stale_rule IS 'The rule that makes a result stale, for example shortest-window: the report is older than the Subscription''s shortest window that is summed or can exhaust it (SGM-D31).';
COMMENT ON COLUMN vigor_profiles.recorded_at IS 'When the profile was written into this Root.';

CREATE TABLE IF NOT EXISTS vigor_reports (
  id            uuid        PRIMARY KEY,
  driver        text        NOT NULL,
  subscription  text        NOT NULL,
  family        text        NOT NULL,
  outcome       text        NOT NULL CHECK (outcome IN ('ok', 'needs_sign_in', 'unavailable', 'unsupported')),
  fetched_at    timestamptz NOT NULL,
  message       text,
  windows       jsonb       NOT NULL CHECK (jsonb_typeof(windows) = 'array'),
  extra         jsonb       NOT NULL CHECK (jsonb_typeof(extra) = 'object'),
  arrived_at    timestamptz NOT NULL,
  run           uuid,
  UNIQUE (driver, subscription, fetched_at)
);
COMMENT ON TABLE vigor_reports IS 'Every usage report as it arrived from a Driver: one row for each report whose fetchedAt is newer than the last recorded one of its Subscription (SGM-1, SGM-D22). Written by the Arbol process alone.';
COMMENT ON COLUMN vigor_reports.id IS 'The report record''s own identifier, a UUID the Arbol process gives it; a result names the report it used by it.';
COMMENT ON COLUMN vigor_reports.driver IS 'The Driver that delivered the report, for example claude.';
COMMENT ON COLUMN vigor_reports.subscription IS 'The Subscription''s identifier within its Driver, for example anthropic (DRV-D21).';
COMMENT ON COLUMN vigor_reports.family IS 'The Subscription''s vendor family, for example anthropic or kimi-coding; it chooses the window scopes (SGM-D32).';
COMMENT ON COLUMN vigor_reports.outcome IS 'The report''s outcome as the Driver Contract names it: ok, needs_sign_in, unavailable or unsupported (DRV-1).';
COMMENT ON COLUMN vigor_reports.fetched_at IS 'When the Driver fetched the report from the vendor, its fetchedAt; the latest of a Subscription is its last recorded report.';
COMMENT ON COLUMN vigor_reports.message IS 'The Driver''s message, present unless the outcome is ok; NULL otherwise.';
COMMENT ON COLUMN vigor_reports.windows IS 'The windows as delivered, a list of the Driver Contract''s window objects, for example [{"kind": "session", "label": "Five hours", "resource": "tokens", "usedPercent": 35, "resetsAt": "2026-10-26T13:20:00Z", "windowMinutes": 300, "limitReached": false}].';
COMMENT ON COLUMN vigor_reports.extra IS 'The report''s extra as delivered, the vendor''s related fields, for example {"isUsingOverage": false}; an empty object when the Driver delivered none.';
COMMENT ON COLUMN vigor_reports.arrived_at IS 'When the Arbol process read the report from the Driver.';
COMMENT ON COLUMN vigor_reports.run IS 'The run that produced the report, when one did and the Arbol process matched it, for example 9b3a2c1e-5c6d-4f70-9a1b-2c3d4e5f6a7b; NULL until then.';

CREATE TABLE IF NOT EXISTS vigor_results (
  id            uuid             PRIMARY KEY,
  driver        text             NOT NULL,
  subscription  text             NOT NULL,
  family        text             NOT NULL,
  moment        timestamptz      NOT NULL,
  report        uuid             REFERENCES vigor_reports (id) ON DELETE RESTRICT,
  profile       integer          NOT NULL REFERENCES vigor_profiles (version) ON DELETE RESTRICT,
  losses        jsonb            NOT NULL CHECK (jsonb_typeof(losses) = 'array'),
  vigor         double precision CHECK (vigor IS NULL OR (vigor >= 0 AND vigor <= 1)),
  exhausted     boolean          NOT NULL,
  predicted     boolean          NOT NULL,
  stale         interval,
  unknown       text,
  notes         jsonb            NOT NULL CHECK (jsonb_typeof(notes) = 'array'),
  next_change   timestamptz,
  next_value    double precision,
  CHECK ((vigor IS NULL) = (unknown IS NOT NULL)),
  CHECK ((next_change IS NULL) = (next_value IS NULL))
);
CREATE INDEX IF NOT EXISTS vigor_results_subscription ON vigor_results (driver, subscription, moment);
COMMENT ON TABLE vigor_results IS 'Every calculation of a Subscription''s Vigor with its inputs, the weights'' profile version, each window''s loss, the result, its state and its next change (SGM-1, SGM-D22). Written by the Arbol process alone.';
COMMENT ON COLUMN vigor_results.id IS 'The calculation record''s own identifier, a UUID the Arbol process gives it.';
COMMENT ON COLUMN vigor_results.driver IS 'The Driver of the Subscription, for example claude.';
COMMENT ON COLUMN vigor_results.subscription IS 'The Subscription''s identifier within its Driver, for example anthropic.';
COMMENT ON COLUMN vigor_results.family IS 'The Subscription''s vendor family, for example anthropic.';
COMMENT ON COLUMN vigor_results.moment IS 'The moment the calculation was made for: the clock it was given.';
COMMENT ON COLUMN vigor_results.report IS 'The report record the calculation used; NULL while there is no report yet (SGM-1.9).';
COMMENT ON COLUMN vigor_results.profile IS 'The version of the profile whose pace, weights and stale rule the calculation used, for example 1.';
COMMENT ON COLUMN vigor_results.losses IS 'Each window''s part in the result, in the order of the report: the window as used, which differs from the delivered one after a prediction, its role and its loss, for example [{"label": "Seven days", "resource": "tokens", "countedAs": "tokens", "assumed": false, "role": "store", "reached": false, "loss": 0.37, "weight": 1, "contribution": 0.37, "reason": null, "predicted": false, "usedPercent": 20, "resetsAt": "2026-10-29T10:00:00Z", "windowMinutes": 10080}].';
COMMENT ON COLUMN vigor_results.vigor IS 'The Subscription''s Vigor, 0 to 1; NULL when the result is unknown (SGM-1.9).';
COMMENT ON COLUMN vigor_results.exhausted IS 'true while a reached inference-gating window without overage exhausts the Subscription (SGM-1.5).';
COMMENT ON COLUMN vigor_results.predicted IS 'true when the calculation used a window predicted fresh after a reset without a newer report (SGM-1.7).';
COMMENT ON COLUMN vigor_results.stale IS 'The report''s age when the result is stale, the report being older than the profile''s stale rule allows; NULL when it is not (SGM-1.8).';
COMMENT ON COLUMN vigor_results.unknown IS 'The reason when the Vigor cannot be computed, shown after unknown: , for example allowance not supported for zai; NULL when it is known (SGM-1.9).';
COMMENT ON COLUMN vigor_results.notes IS 'What the calculation says on the result, a list of texts, for example ["5-hour window: the chatgpt report names no resource; counted as tokens"].';
COMMENT ON COLUMN vigor_results.next_change IS 'The next change of the Vigor: the earliest reset among the windows, or, while exhausted, the moment the last reached inference-gating window resets; NULL when no window names a reset time or the result is unknown (SGM-1.6).';
COMMENT ON COLUMN vigor_results.next_value IS 'The Vigor at the next change, computed on the windows predicted for that moment; NULL with next_change.';
COMMENT ON INDEX vigor_results_subscription IS 'Finds the latest result of a Subscription, and every result of it in the order of its moments, for the read and the replay.';
