-- The second Root's migration script (RTM-1): brings the chats of First Sapling into the second Root's database.
-- Kept in the arbol-root repository as roots/<second>/migrate.sql; the second Root's arbol-root Builds carry it as layout/migrate.sql.
-- arbol-roots runs it with psql, connected to the second Root's database just made from the second Root's layouts, in an empty folder of
-- its own (mode 0700) that it removes afterwards:
--   psql --no-psqlrc --set ON_ERROR_STOP=1 --set from_database=arbol_sapling --set from_root=sapling \
--        --file migrate.sql postgresql://arbol@127.0.0.1:5432/arbol_<second>
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
