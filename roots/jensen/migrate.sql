-- Optional modes are qualified by migration-modes.json (RTM-D28/D29/D30).
\if :{?arbol_migrate_chat}
\if :{?arbol_migrate_check}
-- A direct caller supplying both flags is refused before a connection or write.
SELECT 1/0;
\endif
\set to_database :DBNAME
\set QUIET on
\pset format unaligned
\pset tuples_only on

-- Resolve the requested target copy through its own provenance, never a caller-supplied source chat.
BEGIN READ ONLY;
SELECT set_config('arbol.requested_chat', :'arbol_migrate_chat', true), set_config('arbol.from_root', :'from_root', true) \gset
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM chats c JOIN migrated_chats m ON m.chat_id=c.id
                 WHERE c.id=current_setting('arbol.requested_chat')::uuid
                   AND m.from_root=current_setting('arbol.from_root')) THEN
    RAISE EXCEPTION 'Unknown migrated target chat' USING ERRCODE='P0002';
  END IF;
END $$;
SELECT from_chat AS source_chat FROM migrated_chats WHERE chat_id=:'arbol_migrate_chat'::uuid \gset
COMMIT;

\connect :from_database
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SELECT set_config('arbol.source_chat', :'source_chat', true), now() AS snapshot \gset
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM chats WHERE id=current_setting('arbol.source_chat')::uuid) THEN
    RAISE EXCEPTION 'Unknown original chat' USING ERRCODE='P0002';
  END IF;
END $$;
\copy (SELECT * FROM chats WHERE id=current_setting('arbol.source_chat')::uuid) TO 'chats.copy' WITH (FORMAT binary)
\copy (SELECT * FROM exchanges WHERE chat_id=current_setting('arbol.source_chat')::uuid) TO 'exchanges.copy' WITH (FORMAT binary)
\copy (SELECT m.* FROM messages m JOIN exchanges e ON e.id=m.exchange_id WHERE e.chat_id=current_setting('arbol.source_chat')::uuid) TO 'messages.copy' WITH (FORMAT binary)
\copy (SELECT t.* FROM tool_calls t JOIN exchanges e ON e.id=t.exchange_id WHERE e.chat_id=current_setting('arbol.source_chat')::uuid) TO 'tool_calls.copy' WITH (FORMAT binary)
\copy (SELECT r.* FROM runs r JOIN exchanges e ON e.id=r.exchange_id WHERE e.chat_id=current_setting('arbol.source_chat')::uuid) TO 'runs.copy' WITH (FORMAT binary)
COMMIT;

\connect :to_database
BEGIN;
SET LOCAL lock_timeout='2s';
SELECT set_config('arbol.requested_chat', :'arbol_migrate_chat', true), set_config('arbol.source_chat', :'source_chat', true), set_config('arbol.from_root', :'from_root', true), set_config('arbol.snapshot', :'snapshot', true) \gset
CREATE TEMP TABLE incoming_chats ON COMMIT DROP AS SELECT * FROM chats WITH NO DATA;
CREATE TEMP TABLE incoming_exchanges ON COMMIT DROP AS SELECT * FROM exchanges WITH NO DATA;
CREATE TEMP TABLE incoming_messages ON COMMIT DROP AS SELECT * FROM messages WITH NO DATA;
CREATE TEMP TABLE incoming_tool_calls ON COMMIT DROP AS SELECT * FROM tool_calls WITH NO DATA;
CREATE TEMP TABLE incoming_runs ON COMMIT DROP AS SELECT * FROM runs WITH NO DATA;
CREATE TEMP TABLE exchange_map (original uuid PRIMARY KEY, destination uuid NOT NULL UNIQUE) ON COMMIT DROP;
CREATE TEMP TABLE migration_result (value jsonb NOT NULL) ON COMMIT DROP;
\copy incoming_chats FROM 'chats.copy' WITH (FORMAT binary)
\copy incoming_exchanges FROM 'exchanges.copy' WITH (FORMAT binary)
\copy incoming_messages FROM 'messages.copy' WITH (FORMAT binary)
\copy incoming_tool_calls FROM 'tool_calls.copy' WITH (FORMAT binary)
\copy incoming_runs FROM 'runs.copy' WITH (FORMAT binary)
DO $$
DECLARE
  requested uuid := current_setting('arbol.requested_chat')::uuid;
  original uuid := current_setting('arbol.source_chat')::uuid;
  older text := current_setting('arbol.from_root');
  snapshot_at timestamptz := current_setting('arbol.snapshot')::timestamptz;
  provenance migrated_chats%ROWTYPE;
  continued boolean;
  result_chat uuid;
  ended integer;
BEGIN
  -- The Trunk locks this row on acceptance; its FK also conflicts with FOR UPDATE.
  PERFORM 1 FROM chats WHERE id=requested FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Unknown migrated target chat' USING ERRCODE='P0002';
  END IF;
  SELECT * INTO provenance FROM migrated_chats WHERE chat_id=requested FOR UPDATE;
  IF NOT FOUND OR provenance.from_root<>older OR provenance.from_chat<>original THEN
    RAISE EXCEPTION 'The selected copy provenance changed' USING ERRCODE='P0002';
  END IF;
  IF (SELECT count(*) FROM incoming_chats)<>1
     OR NOT EXISTS (SELECT 1 FROM incoming_chats WHERE id=original)
     OR EXISTS (SELECT 1 FROM incoming_exchanges WHERE chat_id<>original)
     OR EXISTS (SELECT 1 FROM incoming_exchanges e WHERE e.replaced_by IS NOT NULL
                AND NOT EXISTS (SELECT 1 FROM incoming_exchanges x WHERE x.id=e.replaced_by)) THEN
    RAISE EXCEPTION 'The source chat or replacement references are inconsistent';
  END IF;
  SELECT coalesce(max(number) FILTER (WHERE state<>'open'),0) INTO ended FROM incoming_exchanges;
  IF ended<provenance.ended_through THEN
    RAISE EXCEPTION 'The original chat progress regressed';
  END IF;
  SELECT EXISTS (SELECT 1 FROM exchanges WHERE chat_id=requested
                 AND (state='open' OR accepted_at>provenance.migrated_at)) INTO continued;
  result_chat := CASE WHEN continued THEN gen_random_uuid() ELSE requested END;
  INSERT INTO exchange_map SELECT id,CASE WHEN NOT continued AND requested=original THEN id
                                        ELSE gen_random_uuid() END FROM incoming_exchanges;
  IF EXISTS (SELECT 1 FROM exchange_map m JOIN exchanges e ON e.id=m.destination
             WHERE continued OR e.chat_id<>requested) THEN
    RAISE EXCEPTION 'An Exchange identifier belongs to unrelated history';
  END IF;
  IF NOT continued THEN
    IF EXISTS (SELECT 1 FROM exchanges e JOIN exchanges old ON old.id=e.replaced_by
               WHERE old.chat_id=requested AND e.chat_id<>requested) THEN
      RAISE EXCEPTION 'Unrelated history refers to this copy';
    END IF;
    UPDATE exchanges SET replaced_by=NULL WHERE chat_id=requested;
    DELETE FROM messages m USING exchanges e WHERE m.exchange_id=e.id AND e.chat_id=requested;
    DELETE FROM tool_calls t USING exchanges e WHERE t.exchange_id=e.id AND e.chat_id=requested;
    DELETE FROM runs r USING exchanges e WHERE r.exchange_id=e.id AND e.chat_id=requested;
    DELETE FROM exchanges WHERE chat_id=requested;
    UPDATE chats c SET title=i.title,created_at=i.created_at FROM incoming_chats i WHERE c.id=requested;
  ELSE
    INSERT INTO chats SELECT result_chat,title,created_at FROM incoming_chats;
  END IF;
  -- Remap every relational UUID together. Driver run/call IDs and all payloads stay exact.
  UPDATE incoming_exchanges e SET replaced_by=m.destination FROM exchange_map m WHERE e.replaced_by=m.original;
  UPDATE incoming_exchanges e SET id=m.destination,chat_id=result_chat FROM exchange_map m WHERE e.id=m.original;
  UPDATE incoming_exchanges SET state='interrupted',ended_at=snapshot_at WHERE state='open';
  UPDATE incoming_messages t SET exchange_id=m.destination FROM exchange_map m WHERE t.exchange_id=m.original;
  UPDATE incoming_tool_calls t SET exchange_id=m.destination FROM exchange_map m WHERE t.exchange_id=m.original;
  UPDATE incoming_runs t SET exchange_id=m.destination FROM exchange_map m WHERE t.exchange_id=m.original;
  INSERT INTO exchanges SELECT * FROM incoming_exchanges;
  INSERT INTO messages SELECT * FROM incoming_messages;
  INSERT INTO tool_calls SELECT * FROM incoming_tool_calls;
  INSERT INTO runs SELECT * FROM incoming_runs;
  INSERT INTO migrated_chats (chat_id,from_root,from_chat,ended_through,migrated_at,stale)
    VALUES (result_chat,older,original,ended,snapshot_at,false)
    ON CONFLICT (chat_id) DO UPDATE SET ended_through=excluded.ended_through,
      migrated_at=excluded.migrated_at,stale=false;
  INSERT INTO migration_result VALUES (jsonb_build_object('mode','chat','fromRoot',older,'chat',requested,
    'fromChat',original,'resultChat',result_chat,'action',CASE WHEN continued THEN 'copied' ELSE 'replaced' END,
    'endedThrough',ended,'snapshotAt',snapshot_at));
END $$;
SELECT value FROM migration_result;
COMMIT;
\elif :{?arbol_migrate_check}
\set to_database :DBNAME
\set QUIET on
\pset format unaligned
\pset tuples_only on
\connect :from_database
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
\copy (SELECT c.id,coalesce(max(e.number) FILTER (WHERE e.state<>'open'),0)::integer FROM chats c LEFT JOIN exchanges e ON e.chat_id=c.id GROUP BY c.id) TO 'progress.copy' WITH (FORMAT binary)
COMMIT;
\connect :to_database
BEGIN;
SET LOCAL lock_timeout='2s';
SELECT set_config('arbol.from_root', :'from_root', true) \gset
CREATE TEMP TABLE source_progress (chat_id uuid PRIMARY KEY,ended_through integer NOT NULL) ON COMMIT DROP;
\copy source_progress FROM 'progress.copy' WITH (FORMAT binary)
DO $$
BEGIN
  -- Lock every affected provenance row before validating; one missing/regressed original refuses all marks.
  PERFORM 1 FROM migrated_chats WHERE from_root=current_setting('arbol.from_root') ORDER BY chat_id FOR UPDATE;
  IF EXISTS (SELECT 1 FROM migrated_chats m LEFT JOIN source_progress s ON s.chat_id=m.from_chat
             WHERE m.from_root=current_setting('arbol.from_root')
               AND (s.chat_id IS NULL OR s.ended_through<m.ended_through)) THEN
    RAISE EXCEPTION 'An original chat is missing or its progress regressed';
  END IF;
  UPDATE migrated_chats m SET stale=(s.ended_through>m.ended_through)
    FROM source_progress s WHERE m.from_chat=s.chat_id AND m.from_root=current_setting('arbol.from_root');
END $$;
SELECT jsonb_build_object('mode','check','fromRoot',current_setting('arbol.from_root'),
  'checked',count(*),'stale',coalesce(jsonb_agg(chat_id ORDER BY chat_id) FILTER (WHERE stale),'[]'::jsonb))
  FROM migrated_chats WHERE from_root=current_setting('arbol.from_root');
COMMIT;
\else
-- The second Root's migration script (RTM-1): brings the chats of First Sapling into the second Root's database.
-- Kept in the arbol-root repository as roots/jensen/migrate.sql; the second Root's arbol-root Builds carry it as layout/migrate.sql.
-- arbol-roots runs it with psql, connected to the second Root's database just made from the second Root's layouts, in an empty folder of
-- its own (mode 0700) that it removes afterwards:
--   psql --no-psqlrc --set ON_ERROR_STOP=1 --set from_database=arbol_sapling --set from_root=sapling \
--        --file migrate.sql postgresql://arbol@127.0.0.1:5432/arbol_jensen
-- First Sapling and the second Root use Root Contract version 1, so every chat table is copied as it is.

\set to_database :DBNAME

-- 1. Read First Sapling's tables in one transaction that cannot write, so the copy is one moment and nothing there changes.
\connect :from_database
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SELECT now() AS snapshot \gset
\copy (SELECT * FROM chats) TO 'chats.copy' WITH (FORMAT binary)
\copy (SELECT * FROM exchanges) TO 'exchanges.copy' WITH (FORMAT binary)
\copy (SELECT * FROM messages) TO 'messages.copy' WITH (FORMAT binary)
\copy (SELECT * FROM tool_calls) TO 'tool_calls.copy' WITH (FORMAT binary)
\copy (SELECT * FROM runs) TO 'runs.copy' WITH (FORMAT binary)
COMMIT;

-- 2. Write the second Root's tables in one transaction, so that a failure leaves no row.
\connect :to_database
BEGIN;
\copy chats FROM 'chats.copy' WITH (FORMAT binary)
\copy exchanges FROM 'exchanges.copy' WITH (FORMAT binary)
\copy messages FROM 'messages.copy' WITH (FORMAT binary)
\copy tool_calls FROM 'tool_calls.copy' WITH (FORMAT binary)
\copy runs FROM 'runs.copy' WITH (FORMAT binary)

-- Where each chat came from and how far it had got, counted before open Exchanges change.
INSERT INTO migrated_chats (chat_id, from_root, from_chat, ended_through, migrated_at)
SELECT c.id, :'from_root', c.id, coalesce(max(e.number) FILTER (WHERE e.state <> 'open'), 0), :'snapshot'
FROM chats c LEFT JOIN exchanges e ON e.chat_id = c.id
GROUP BY c.id;

-- An Exchange still open in First Sapling is only history here: interrupted, at the moment of the snapshot.
UPDATE exchanges SET state = 'interrupted', ended_at = :'snapshot' WHERE state = 'open';
COMMIT;
\endif
