
# LOW TIER — DO NOT ENABLE OR RECREATE
# Historical examples only. Read before adding related tests; never execute.
# LOW-TIER-BEGIN: tests/mid/test_mid_vigor_tables.py::OperationalBoundary.test_default_preview_does_not_open_an_owner_folder_or_start_a_build
# Reason: Vigor column/default/constraint checks restate readable DDL or PostgreSQL behavior; retained packaged layout/migration gates already exercise the real schema and preservation boundary. Case reviewed: root.vigor-preview
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_vigor_tables.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_default_preview_does_not_open_an_owner_folder_or_start_a_build(self) -> None:
#         """root.vigor-preview"""
#         with tempfile.TemporaryDirectory(prefix="vigor-preview-") as home:
#             result = subprocess.run(
#                 [sys.executable, "-I", "-B", str(ROOT / "scripts/vigor_tables.py")],
#                 env={**os.environ, "HOME": home},
#                 capture_output=True,
#                 text=True,
#                 timeout=5,
#             )
#             self.assertEqual(result.returncode, 0, result.stderr)
#             self.assertEqual(
#                 json.loads(result.stdout), {"preflightOnly": True, "roots": ["sapling", "jensen"], "realMessages": 0}
#             )
#             self.assertFalse(list(Path(home).iterdir()))
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_vigor_tables.py::OperationalBoundary.test_operational_guard_detects_old_row_schema_backend_and_vigor_damage
# Reason: Vigor column/default/constraint checks restate readable DDL or PostgreSQL behavior; retained packaged layout/migration gates already exercise the real schema and preservation boundary. Case reviewed: root.vigor-preservation
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_vigor_tables.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_operational_guard_detects_old_row_schema_backend_and_vigor_damage(self) -> None:
#         """root.vigor-preservation"""
#         from drill_support import DrillError
#
#         before: dict[str, Any] = {
#             "history": {"tables": {"chats": {"encodedRows": ["exact old row"]}}},
#             "schema": {"relations": ["old relation"], "comments": ["old comment"]},
#             "backend": {
#                 "counts": {"drafts": 1},
#                 "counter": {"last_value": 7, "is_called": True},
#                 "rows": {"drafts": ["x"]},
#             },
#         }
#         after: dict[str, Any] = {**copy.deepcopy(before), "vigor": dict.fromkeys(TABLES, 0)}
#         preserved(before, after)
#         for fault in ("row", "schema", "backend", "counter", "filled", "present"):
#             bad, earlier = copy.deepcopy(after), copy.deepcopy(before)
#             if fault == "row":
#                 bad["history"]["tables"]["chats"]["encodedRows"] = ["different"]
#             elif fault == "schema":
#                 bad["schema"]["comments"] = []
#             elif fault == "backend":
#                 bad["backend"]["rows"]["drafts"] = ["changed"]
#             elif fault == "counter":
#                 bad["backend"]["counter"]["last_value"] = 8
#             elif fault == "filled":
#                 bad["vigor"]["vigor_reports"] = 1
#             else:
#                 earlier["vigor"] = dict.fromkeys(TABLES, 0)
#             with self.subTest(fault=fault), self.assertRaises(DrillError):
#                 preserved(earlier, bad)
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_vigor_tables.py::VigorTables.test_both_layouts_carry_the_same_vigor_tables_and_repeat_fully_commented
# Reason: Vigor column/default/constraint checks restate readable DDL or PostgreSQL behavior; retained packaged layout/migration gates already exercise the real schema and preservation boundary. Case reviewed: root.vigor-layouts
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_vigor_tables.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_both_layouts_carry_the_same_vigor_tables_and_repeat_fully_commented(self) -> None:
#         """root.vigor-layouts"""
#         jensen = (ROOT / "roots/jensen/layout.sql").read_text(encoding="utf-8")
#         self.assertTrue(jensen.endswith(VIGOR))  # the same text, appended after the backend's tables
#         self.assertLess(jensen.index("exchange_notes"), jensen.index("vigor_profiles"))
#         for root in ("sapling", "jensen"):
#             shutil.copy2(ROOT / "roots" / root / "layout.sql", self.inputs.folder / "layout/root-tables.sql")
#             report = run_layout(self.inputs, self.lab)
#             self.assertTrue(report["repeated"])
#             database = self.database(root)
#             self.assertTrue(present(self.lab.server, database))
#             self.assertEqual(
#                 self.lab.server.value(database, f"SELECT to_json(obj_description('{INDEX}'::regclass,'pg_class'))"),
#                 "Finds the latest result of a Subscription, and every result of it in the order of its moments, "
#                 "for the read and the replay.",
#             )
#             self.lab.server.execute(database, "DROP TABLE vigor_results")
#             with self.assertRaisesRegex(ValueError, "partial"):
#                 present(self.lab.server, database)
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_vigor_tables.py::VigorTables.test_fictional_rows_are_exact_and_survive_a_repeated_layout
# Reason: Vigor column/default/constraint checks restate readable DDL or PostgreSQL behavior; retained packaged layout/migration gates already exercise the real schema and preservation boundary. Case reviewed: root.vigor-rows
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_vigor_tables.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_fictional_rows_are_exact_and_survive_a_repeated_layout(self) -> None:
#         """root.vigor-rows"""
#         database = self.database("sapling")
#         seed(self.lab.server, database)
#         before = rows(self.lab.server, database)
#         self.assertEqual([len(before[name]) for name in TABLES], [1, 2, 2])
#         self.lab.run_file(database, ROOT / "roots/sapling/layout.sql")
#         self.assertEqual(rows(self.lab.server, database), before)
#         report = next(row for row in before["vigor_reports"] if row["id"] == REPORTS[0])
#         self.assertEqual(str(report["windows"][1]["usedPercent"]), "20.123456789012345678901234567890")
#         unknown = next(row for row in before["vigor_results"] if row["id"] == RESULTS[1])
#         self.assertEqual(
#             (unknown["vigor"], unknown["unknown"], unknown["stale"]),
#             (None, "allowance not supported for zai", "05:05:00"),
#         )
#         self.assertEqual(unknown["notes"], ["why 🌲"])
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_vigor_tables.py::VigorTables.test_the_tables_refuse_a_repeated_report_and_an_inconsistent_result
# Reason: Vigor column/default/constraint checks restate readable DDL or PostgreSQL behavior; retained packaged layout/migration gates already exercise the real schema and preservation boundary. Case reviewed: root.vigor-constraints
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_vigor_tables.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_the_tables_refuse_a_repeated_report_and_an_inconsistent_result(self) -> None:
#         """root.vigor-constraints"""
#         database = self.database("jensen")
#         seed(self.lab.server, database)
#         before = rows(self.lab.server, database)
#         refused = [
#             # the same Subscription's report with the same fetchedAt is one report (SGM-1.10)
#             f"INSERT INTO vigor_reports VALUES ('{uuid.uuid4()}','claude','anthropic','anthropic','ok',"
#             "'2026-10-26T09:55:00Z',NULL,'[]','{}','2026-10-26T10:05:00Z',NULL)",
#             # a known result has a Vigor and no reason; an unknown one a reason and no Vigor (SGM-1.9)
#             f"INSERT INTO vigor_results VALUES ('{uuid.uuid4()}','claude','anthropic','anthropic','2026-10-26T10:01:00Z',"
#             f"'{REPORTS[0]}',1,'[]',NULL,false,false,NULL,NULL,'[]',NULL,NULL)",
#             f"INSERT INTO vigor_results VALUES ('{uuid.uuid4()}','claude','anthropic','anthropic','2026-10-26T10:01:00Z',"
#             f"'{REPORTS[0]}',1,'[]',0.5,false,false,NULL,'why','[]',NULL,NULL)",
#             # the next change's moment and value come together (SGM-1.6)
#             f"INSERT INTO vigor_results VALUES ('{uuid.uuid4()}','claude','anthropic','anthropic','2026-10-26T10:01:00Z',"
#             f"'{REPORTS[0]}',1,'[]',0.5,false,false,NULL,NULL,'[]','2026-10-26T13:20:00Z',NULL)",
#             # a result names a profile and a report that exist
#             f"INSERT INTO vigor_results VALUES ('{uuid.uuid4()}','claude','anthropic','anthropic','2026-10-26T10:01:00Z',"
#             f"'{REPORTS[0]}',2,'[]',0.5,false,false,NULL,NULL,'[]',NULL,NULL)",
#             f"INSERT INTO vigor_results VALUES ('{uuid.uuid4()}','claude','anthropic','anthropic','2026-10-26T10:01:00Z',"
#             f"'{uuid.uuid4()}',1,'[]',0.5,false,false,NULL,NULL,'[]',NULL,NULL)",
#             # a Vigor lies within 0 and 1, an outcome is one of the contract's four
#             f"INSERT INTO vigor_results VALUES ('{uuid.uuid4()}','claude','anthropic','anthropic','2026-10-26T10:01:00Z',"
#             f"'{REPORTS[0]}',1,'[]',1.5,false,false,NULL,NULL,'[]',NULL,NULL)",
#             f"INSERT INTO vigor_reports VALUES ('{uuid.uuid4()}','claude','anthropic','anthropic','partial',"
#             "'2026-10-26T09:57:00Z',NULL,'[]','{}','2026-10-26T10:05:00Z',NULL)",
#             # a report a result rests on stays
#             f"DELETE FROM vigor_reports WHERE id='{REPORTS[0]}'",
#         ]
#         for statement in refused:
#             with self.subTest(statement=statement[:70]), self.assertRaises(SqlError):
#                 self.lab.server.execute(database, statement)
#         self.assertEqual(rows(self.lab.server, database), before)
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_vigor_tables.py::VigorTables.test_whole_migration_still_passes_and_copies_no_vigor_row
# Reason: Vigor column/default/constraint checks restate readable DDL or PostgreSQL behavior; retained packaged layout/migration gates already exercise the real schema and preservation boundary. Case reviewed: root.vigor-migration
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_vigor_tables.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_whole_migration_still_passes_and_copies_no_vigor_row(self) -> None:
#         """root.vigor-migration"""
#         older = Origin(
#             "sapling", 1, self.inputs.file("chat-tables.sql"), self.inputs.folder / "roots/sapling/layout.sql"
#         )
#         report = run_migration(self.inputs, self.lab, older)
#         # The three tables exist, empty, in the older and the new database alike: the fixture seeds none, since the
#         # migration script does not copy them (SGM-D29), and the generic check compares every table of the older one.
#         self.assertEqual((report["unchangedTables"], report["sourceRows"]), (12, 28))
#         self.assertEqual(report["backendTables"]["exact"], True)
# LOW-TIER-SOURCE-END
# LOW-TIER-END
