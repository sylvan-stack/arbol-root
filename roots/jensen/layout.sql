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
