# Test inventory: arbol-root

Reviewed source revision: `c5a544ec3a254ad64588a0cb7940f65b2ae26455`. Static inventory dated 28 October 2026. See [TESTS.md](../TESTS.md) for execution and restoration rules.

**Top** means individually reviewed and active. **Mid*** means commented and provisionally reserved for a separate testing task; usefulness still needs assessment before restoration. **Low** means removed in the preceding pruning review. A function/program count is not an assertion count or a discovery result.

## contract/conformance/rct_conformance/runner.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`run_suite`](../contract/conformance/rct_conformance/runner.py#L13) | Mid* / refuses | Broad qualification or diagnostic entry point. Its original implementation is commented and the callable refuses, so disabled checks cannot yield a passing release claim. |

## contract/conformance/rct_conformance/scenarios/r1.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`run`](../contract/conformance/rct_conformance/scenarios/r1.py#L46) | Mid* / commented | Contract scenario with a multi-step fixture and compatibility assertions. Reserved for explicit qualification; this reset does not establish a reason to keep the whole scenario active. |

## contract/conformance/rct_conformance/scenarios/r10.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`run`](../contract/conformance/rct_conformance/scenarios/r10.py#L17) | Mid* / commented | Contract scenario with a multi-step fixture and compatibility assertions. Reserved for explicit qualification; this reset does not establish a reason to keep the whole scenario active. |

## contract/conformance/rct_conformance/scenarios/r11.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`run`](../contract/conformance/rct_conformance/scenarios/r11.py#L15) | Mid* / commented | Contract scenario with a multi-step fixture and compatibility assertions. Reserved for explicit qualification; this reset does not establish a reason to keep the whole scenario active. |

## contract/conformance/rct_conformance/scenarios/r12.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`run`](../contract/conformance/rct_conformance/scenarios/r12.py#L13) | Mid* / commented | Contract scenario with a multi-step fixture and compatibility assertions. Reserved for explicit qualification; this reset does not establish a reason to keep the whole scenario active. |

## contract/conformance/rct_conformance/scenarios/r13.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`run`](../contract/conformance/rct_conformance/scenarios/r13.py#L41) | Mid* / commented | Contract scenario with a multi-step fixture and compatibility assertions. Reserved for explicit qualification; this reset does not establish a reason to keep the whole scenario active. |

## contract/conformance/rct_conformance/scenarios/r14.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`run`](../contract/conformance/rct_conformance/scenarios/r14.py#L54) | Mid* / commented | Contract scenario with a multi-step fixture and compatibility assertions. Reserved for explicit qualification; this reset does not establish a reason to keep the whole scenario active. |

## contract/conformance/rct_conformance/scenarios/r15.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`run`](../contract/conformance/rct_conformance/scenarios/r15.py#L14) | Mid* / commented | Contract scenario with a multi-step fixture and compatibility assertions. Reserved for explicit qualification; this reset does not establish a reason to keep the whole scenario active. |

## contract/conformance/rct_conformance/scenarios/r17.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`run`](../contract/conformance/rct_conformance/scenarios/r17.py#L13) | Mid* / commented | Contract scenario with a multi-step fixture and compatibility assertions. Reserved for explicit qualification; this reset does not establish a reason to keep the whole scenario active. |

## contract/conformance/rct_conformance/scenarios/r18.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`run`](../contract/conformance/rct_conformance/scenarios/r18.py#L10) | Mid* / commented | Contract scenario with a multi-step fixture and compatibility assertions. Reserved for explicit qualification; this reset does not establish a reason to keep the whole scenario active. |

## contract/conformance/rct_conformance/scenarios/r19.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`run`](../contract/conformance/rct_conformance/scenarios/r19.py#L31) | Mid* / commented | Contract scenario with a multi-step fixture and compatibility assertions. Reserved for explicit qualification; this reset does not establish a reason to keep the whole scenario active. |

## contract/conformance/rct_conformance/scenarios/r2.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`run`](../contract/conformance/rct_conformance/scenarios/r2.py#L15) | Mid* / commented | Contract scenario with a multi-step fixture and compatibility assertions. Reserved for explicit qualification; this reset does not establish a reason to keep the whole scenario active. |

## contract/conformance/rct_conformance/scenarios/r3.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`run`](../contract/conformance/rct_conformance/scenarios/r3.py#L32) | Mid* / commented | Contract scenario with a multi-step fixture and compatibility assertions. Reserved for explicit qualification; this reset does not establish a reason to keep the whole scenario active. |

## contract/conformance/rct_conformance/scenarios/r4.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`run`](../contract/conformance/rct_conformance/scenarios/r4.py#L41) | Mid* / commented | Contract scenario with a multi-step fixture and compatibility assertions. Reserved for explicit qualification; this reset does not establish a reason to keep the whole scenario active. |

## contract/conformance/rct_conformance/scenarios/r5.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`run`](../contract/conformance/rct_conformance/scenarios/r5.py#L27) | Mid* / commented | Contract scenario with a multi-step fixture and compatibility assertions. Reserved for explicit qualification; this reset does not establish a reason to keep the whole scenario active. |

## contract/conformance/rct_conformance/scenarios/r6.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`run`](../contract/conformance/rct_conformance/scenarios/r6.py#L37) | Mid* / commented | Contract scenario with a multi-step fixture and compatibility assertions. Reserved for explicit qualification; this reset does not establish a reason to keep the whole scenario active. |

## contract/conformance/rct_conformance/scenarios/r7.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`run`](../contract/conformance/rct_conformance/scenarios/r7.py#L8) | Mid* / commented | Contract scenario with a multi-step fixture and compatibility assertions. Reserved for explicit qualification; this reset does not establish a reason to keep the whole scenario active. |

## contract/conformance/rct_conformance/scenarios/r8.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`run`](../contract/conformance/rct_conformance/scenarios/r8.py#L29) | Mid* / commented | Contract scenario with a multi-step fixture and compatibility assertions. Reserved for explicit qualification; this reset does not establish a reason to keep the whole scenario active. |

## contract/conformance/rct_conformance/scenarios/r9.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`run`](../contract/conformance/rct_conformance/scenarios/r9.py#L19) | Mid* / commented | Contract scenario with a multi-step fixture and compatibility assertions. Reserved for explicit qualification; this reset does not establish a reason to keep the whole scenario active. |

## contract/conformance/tests/test_cli.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`Cli.test_without_initdb_on_the_search_path_it_ends_with_2_and_names_it`](../contract/conformance/tests/test_cli.py#L28) | Mid* / commented | Scenario: cli.programs: with psql, pg_ctl and createdb but no initdb on the search path, the suite ends with 2 before any scenario starts and names initdb.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Cli.test_wrong_input_ends_with_2_and_says_what_is_wrong`](../contract/conformance/tests/test_cli.py#L42) | Mid* / commented | Scenario: cli.input: an unknown option, a missing or doubled option, a Trunk that cannot be run, a version without layout.sql, an unknown scenario, or R16 alone.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Cli.test_a_whole_run_lists_every_scenario_and_reports_failures`](../contract/conformance/tests/test_cli.py#L69) | Mid* / commented | Scenario: cli.whole-run: without --only every scenario of RCT-4 runs and every failed check is reported.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Runner.test_failure_descriptions_can_print_lone_surrogates_as_valid_utf8`](../contract/conformance/tests/test_cli.py#L86) | Mid* / commented | Scenario: failure descriptions can print lone surrogates as valid utf8. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Runner.test_reports_each_scenario_and_runs_r16_after_each`](../contract/conformance/tests/test_cli.py#L94) | Mid* / commented | Scenario: runner.report: PASS for a scenario whose checks and R16 pass, FAIL with what was expected and received for one whose check fails, FAIL naming R16 for one that changes the tables, and the status 1.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Runner.test_every_scenario_passing_is_status_0`](../contract/conformance/tests/test_cli.py#L130) | Mid* / commented | Scenario: every scenario passing is status 0. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Runner.test_only_chooses_scenarios_in_the_order_of_the_registry`](../contract/conformance/tests/test_cli.py#L137) | Mid* / commented | Scenario: only chooses scenarios in the order of the registry. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## contract/conformance/tests/test_layout.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`Layout.test_the_file_is_the_interface_of_rct_3`](../contract/conformance/tests/test_layout.py#L66) | Mid* / commented | Scenario: layout.the-interface: contract/1/layout.sql is, byte for byte, the file in RCT-3's Interface.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Layout.test_runs_twice_and_the_second_run_changes_nothing`](../contract/conformance/tests/test_layout.py#L76) | Mid* / commented | Scenario: layout.runs-twice: every statement can run again, and the second run changes nothing.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Layout.test_every_table_and_column_has_a_comment`](../contract/conformance/tests/test_layout.py#L87) | Mid* / commented | Scenario: layout.comments: every table, every column and the index of the open Exchanges have a comment.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Layout.test_a_second_open_exchange_in_a_chat_is_refused`](../contract/conformance/tests/test_layout.py#L106) | Mid* / commented | Scenario: layout.one-open-exchange: the unique index on the open Exchanges refuses a second one in its chat.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Layout.test_a_second_exchange_with_the_same_number_is_refused`](../contract/conformance/tests/test_layout.py#L115) | Mid* / commented | Scenario: layout.unique-number: the key on (chat_id, number) refuses a second Exchange with the same number.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Layout.test_a_failed_exchange_without_a_cause_is_refused`](../contract/conformance/tests/test_layout.py#L125) | Mid* / commented | Scenario: layout.failed-has-a-cause: a failed Exchange without an error, and a cause without a failure, are refused.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Layout.test_a_run_of_an_unknown_kind_is_refused`](../contract/conformance/tests/test_layout.py#L135) | Mid* / commented | Scenario: layout.run-kind: a run of a kind other than agent and small is refused.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Layout.test_the_deletion_of_a_chat_that_has_exchanges_is_refused`](../contract/conformance/tests/test_layout.py#L148) | Mid* / commented | Scenario: layout.no-cascade: a chat that has Exchanges, and an Exchange that has messages, cannot be deleted.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Layout.test_nul_and_a_lone_half_of_a_surrogate_pair_are_refused_and_u_fffd_is_stored`](../contract/conformance/tests/test_layout.py#L159) | Mid* / commented | Scenario: layout.characters: U+0000 and a lone half of a surrogate pair are refused with errors of the SQLSTATE class 22, in the text of a message and inside jsonb; U+FFFD in their place is stored as it was sent.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Layout.test_the_readers_query_leaves_out_a_replaced_exchange_and_a_sub_agents_call`](../contract/conformance/tests/test_layout.py#L183) | Mid* / commented | Scenario: layout.reader: RCT-3's query of a chat leaves out a replaced Exchange and the calls of a sub-agent.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## contract/conformance/tests/test_setup.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`Setup.test_setup_makes_the_home_the_server_the_root_record_and_the_database`](../contract/conformance/tests/test_setup.py#L51) | Mid* / commented | Scenario: setup.makes: a temporary home; a server of its own made with initdb in it, trusting the role rct and listening only on a socket in a short folder under /tmp; the Root record with the version under test and arbol_rct; an empty exchanges/ of the mode 0700; the database made from layout.sql; database.json with the socket's address.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Setup.test_closing_leaves_nothing_behind`](../contract/conformance/tests/test_setup.py#L83) | Mid* / commented | Scenario: setup.leaves-nothing: closing ends the Trunk's process group and the stand-in's children, stops the server and removes its socket folder and the home.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Setup.test_the_starter_starts_run_detach_as_arbol_root_does`](../contract/conformance/tests/test_setup.py#L108) | Mid* / commented | Scenario: setup.starter: `--root rct run --detach --exchange <id> --request <file>`, in a process group and session of its own, with standard input from /dev/null, from the home's work folder; the request file names the Driver, the Subscription and the model, and is removed once the one line is read.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Setup.test_the_starter_names_another_root_when_a_scenario_asks`](../contract/conformance/tests/test_setup.py#L134) | Mid* / commented | Scenario: setup.starter: a scenario may start the Trunk for another Root identifier, such as `../rct`.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Setup.test_naming_a_part_takes_back_the_release_of_a_held_run`](../contract/conformance/tests/test_setup.py#L142) | Mid* / commented | Scenario: naming a part takes back the release of a held run. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Setup.test_the_trunk_gets_only_home_path_lang_and_the_tests_own_variables`](../contract/conformance/tests/test_setup.py#L152) | Mid* / commented | Scenario: setup.environment: HOME is the home, the stand-in comes first on PATH under both launcher names, and ARBOL_TEST_TIME_SCALE is 10 unless a scenario says otherwise; ARBOL_TEST_HANG=1 where a scenario asks.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Setup.test_the_owners_postgresql_settings_reach_neither_the_suite_nor_the_trunk`](../contract/conformance/tests/test_setup.py#L171) | Mid* / commented | Scenario: setup.isolated: PG… variables of the owner's shell change nothing, and the Trunk gets none of them.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Setup.test_a_command_runs_to_its_end`](../contract/conformance/tests/test_setup.py#L183) | Mid* / commented | Scenario: setup.command: a command such as settle runs in the foreground, and its exit status and lines are read.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Setup.test_the_stand_in_is_what_the_trunk_starts_as_its_driver`](../contract/conformance/tests/test_setup.py#L193) | Mid* / commented | Scenario: setup.stand-in: a Trunk that starts arbol-claude-driver from its search path starts the stand-in, which plays the scenario's script and records the start in received.jsonl.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Starts.test_a_foreground_start_keeps_the_pipe_and_the_lines_after_acceptance`](../contract/conformance/tests/test_setup.py#L213) | Mid* / commented | Scenario: a foreground start keeps the pipe and the lines after acceptance. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Starts.test_starts_from_several_threads_at_once_each_get_files_of_their_own`](../contract/conformance/tests/test_setup.py#L225) | Mid* / commented | Scenario: setup.threads: request files made from several threads at once never share a name.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Starts.test_meanwhile_runs_once_the_trunk_is_started_and_before_its_line_is_read`](../contract/conformance/tests/test_setup.py#L234) | Mid* / commented | Scenario: setup.meanwhile: start() runs its meanwhile with the Trunk's process started and its line not read yet.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Starts.test_held_acceptances_wait_until_the_hold_is_released_and_rows_can_be_read_meanwhile`](../contract/conformance/tests/test_setup.py#L244) | Mid* / commented | Scenario: setup.hold: while acceptances are held, a Trunk's insert into chats waits and the tables can be read; once the hold is released, the acceptance goes on.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`R16.test_passes_when_every_row_belongs_to_an_exchange_the_scenario_ran`](../contract/conformance/tests/test_setup.py#L266) | Mid* / commented | Scenario: r16.passes: the rows of the Exchanges the scenario's acceptance lines named, and an unchanged layout.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`R16.test_finds_a_table_a_column_and_an_index_that_layout_sql_did_not_make`](../contract/conformance/tests/test_setup.py#L276) | Mid* / commented | Scenario: r16.layout: a table, a column and an index added by the Trunk are each named.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`R16.test_finds_rows_of_an_exchange_the_scenario_did_not_run`](../contract/conformance/tests/test_setup.py#L289) | Mid* / commented | Scenario: r16.rows: a chat and an Exchange that no acceptance line named are found.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`R16.test_starts_the_server_again_when_a_scenario_left_it_stopped`](../contract/conformance/tests/test_setup.py#L302) | Mid* / commented | Scenario: r16.server: a scenario that stops the server, such as R12, still gets R16.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Readers.test_readers_skip_dot_folders_and_an_unfinished_last_line`](../contract/conformance/tests/test_setup.py#L314) | Mid* / commented | Scenario: setup.readers: a folder whose name starts with a dot is not listed, and the last line of events.jsonl without its newline is not read.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Readers.test_wait_until_gives_the_first_value_or_fails`](../contract/conformance/tests/test_setup.py#L335) | Mid* / commented | Scenario: wait until gives the first value or fails. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## contract/conformance/tests/test_standin.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`StandIn.test_plays_a_script_and_records_what_it_received`](../contract/conformance/tests/test_standin.py#L80) | Mid* / commented | Scenario: standin.plays: the script of the scenario named in <home>/standin/scenario, as a Driver writes events: one runId, seq from 1 without gaps, the labels on every event, text before the tool call that follows it, and finished last; the record holds the arguments, the request as read, the control lines, the lines it wrote and the signals.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`StandIn.test_a_stop_line_stops_the_run_as_a_driver_does`](../contract/conformance/tests/test_standin.py#L110) | Mid* / commented | Scenario: standin.stop: a stop line on the control input finishes the open tool call as interrupted and the run as cancelled, with the exit status 2, and the line is recorded unchanged.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`StandIn.test_a_held_run_goes_on_once_the_suite_lets_it_go`](../contract/conformance/tests/test_standin.py#L128) | Mid* / commented | Scenario: standin.hold: a run held open writes no event until <home>/standin/release exists, then goes on.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`StandIn.test_sigterm_stops_the_run_and_ends_its_child`](../contract/conformance/tests/test_standin.py#L145) | Mid* / commented | Scenario: standin.sigterm: a child started in a process group of its own is ended when the stand-in gets SIGTERM, and the signal is recorded.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`StandIn.test_the_end_of_the_control_input_stops_the_run`](../contract/conformance/tests/test_standin.py#L164) | Mid* / commented | Scenario: standin.eof: the run's control input ending stops the run, as DRV-2.26 says.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`StandIn.test_an_answer_reaches_the_open_question`](../contract/conformance/tests/test_standin.py#L176) | Mid* / commented | Scenario: standin.answer: an answer line for the open question closes it, and the run goes on to its end.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`StandIn.test_a_run_without_tools_and_chat_session_is_a_title`](../contract/conformance/tests/test_standin.py#L199) | Mid* / commented | Scenario: standin.title: a run with "tools": "none" and no chat session gets one text, "Stand-in title".. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`StandIn.test_a_scenario_without_a_script_fails_the_run`](../contract/conformance/tests/test_standin.py#L212) | Mid* / commented | Scenario: standin.no-script: a run of a scenario the stand-in has no script for fails, and says so.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`StandIn.test_a_failed_run_keeps_the_drivers_error_whole`](../contract/conformance/tests/test_standin.py#L223) | Mid* / commented | Scenario: standin.fail: a script's failure is the Driver's error object, retryAfterSeconds included.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`StandIn.test_runs_stop_stops_a_run_from_another_invocation`](../contract/conformance/tests/test_standin.py#L235) | Mid* / commented | Scenario: standin.runs-stop: `runs stop <run>` stops the run of that identifier; an unknown run is no error.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`StandIn.test_an_unknown_option_is_refused_as_the_only_event`](../contract/conformance/tests/test_standin.py#L250) | Mid* / commented | Scenario: standin.refuses: an option a Driver does not take is refused in one finished event with invalid_input.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## scripts/chat_migration_check.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`check_modes`](../scripts/chat_migration_check.py#L93) | Mid* / refuses | Broad qualification or diagnostic entry point. Its original implementation is commented and the callable refuses, so disabled checks cannot yield a passing release claim. |
| [`backend_modes`](../scripts/chat_migration_check.py#L264) | Mid* / refuses | Broad qualification or diagnostic entry point. Its original implementation is commented and the callable refuses, so disabled checks cannot yield a passing release claim. |

## scripts/check_build.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`main`](../scripts/check_build.py#L12) | Mid* / refuses | Broad qualification or diagnostic entry point. Its original implementation is commented and the callable refuses, so disabled checks cannot yield a passing release claim. |

## scripts/check_layout.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`run_layout`](../scripts/check_layout.py#L34) | Mid* / refuses | Broad qualification or diagnostic entry point. Its original implementation is commented and the callable refuses, so disabled checks cannot yield a passing release claim. |
| [`main`](../scripts/check_layout.py#L62) | Mid* / refuses | Broad qualification or diagnostic entry point. Its original implementation is commented and the callable refuses, so disabled checks cannot yield a passing release claim. |

## scripts/check_migration.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`run_migration`](../scripts/check_migration.py#L116) | Mid* / refuses | Broad qualification or diagnostic entry point. Its original implementation is commented and the callable refuses, so disabled checks cannot yield a passing release claim. |
| [`check_migration`](../scripts/check_migration.py#L201) | Mid* / refuses | Broad qualification or diagnostic entry point. Its original implementation is commented and the callable refuses, so disabled checks cannot yield a passing release claim. |
| [`main`](../scripts/check_migration.py#L220) | Mid* / refuses | Broad qualification or diagnostic entry point. Its original implementation is commented and the callable refuses, so disabled checks cannot yield a passing release claim. |

## scripts/verify_build.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`verify_build`](../scripts/verify_build.py#L1) | Mid* / commented | Standalone browser, native, installation or qualification program. Its combined checks need a dedicated testing task; the whole program has no individually justified top-tier selection. |

## scripts/verify_sql_build.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`verify_sql_build`](../scripts/verify_sql_build.py#L1) | Mid* / commented | Standalone browser, native, installation or qualification program. Its combined checks need a dedicated testing task; the whole program has no individually justified top-tier selection. |

## tests/test_backend_tables.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`OperationalBoundary.test_default_preview_does_not_open_an_owner_folder_or_start_a_build`](../tests/test_backend_tables.py#L21) | Mid* / commented | Scenario: sapling.backend-layout-preview. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`OperationalBoundary.test_operational_guard_detects_old_row_schema_and_new_counter_damage`](../tests/test_backend_tables.py#L39) | Mid* / commented | Scenario: sapling.backend-layout-preservation. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`BackendTables.test_both_layouts_repeat_with_every_table_column_and_sequence_commented`](../tests/test_backend_tables.py#L110) | Mid* / commented | Scenario: both layouts repeat with every table column and sequence commented. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`BackendTables.test_whole_copy_is_exact_and_never_reuses_deleted_revisions`](../tests/test_backend_tables.py#L119) | Mid* / commented | Scenario: whole copy is exact and never reuses deleted revisions. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`BackendTables.test_empty_drafts_keep_consumed_and_not_yet_consumed_counter_states`](../tests/test_backend_tables.py#L132) | Mid* / commented | Scenario: root.backend-empty-counter. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`BackendTables.test_counter_rollback_exhaustion_missing_layout_and_late_failure`](../tests/test_backend_tables.py#L148) | Mid* / commented | Scenario: root.backend-counter-rollback. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`BackendTables.test_target_counter_never_moves_back_and_concurrent_allocator_waits_for_commit`](../tests/test_backend_tables.py#L177) | Mid* / commented | Scenario: root.backend-counter-lock. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`BackendTables.test_reimport_notes_and_local_input_are_preserved_and_pending_send_refuses`](../tests/test_backend_tables.py#L206) | Mid* / commented | Scenario: reimport notes and local input are preserved and pending send refuses. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`BackendTables.test_counter_restart_fault_is_detected_by_saved_draft_probe`](../tests/test_backend_tables.py#L261) | Mid* / commented | Scenario: root.backend-counter-fault. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## tests/test_chat_migration.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`Capabilities.test_explicit_capabilities_are_regular_versioned_and_complete`](../tests/test_chat_migration.py#L19) | Mid* / commented | Scenario: root.migration-mode-capability. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Capabilities.test_only_documented_branches_execute_and_legacy_protocol_stays_strict`](../tests/test_chat_migration.py#L41) | Mid* / commented | Scenario: root.migration-mode-protocol. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Capabilities.test_build_input_refuses_boolean_or_mismatched_advertised_versions`](../tests/test_chat_migration.py#L57) | Mid* / commented | Scenario: root.migration-mode-input. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`ChatModes.test_advertised_modes_preserve_history_and_refuse_without_partial_writes`](../tests/test_chat_migration.py#L105) | Mid* / commented | Scenario: root.migration-chat-modes. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`ChatModes.test_source_writes_and_unsafe_copy_metadata_fail_before_sql_execution`](../tests/test_chat_migration.py#L115) | Mid* / commented | Scenario: root.migration-mode-protocol-refusal. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`ChatModes.test_planted_history_and_stale_faults_are_detected_by_qualification`](../tests/test_chat_migration.py#L130) | Mid* / commented | Scenario: root.migration-chat-faults. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`ChatModes.test_failure_after_target_deletion_or_stale_update_rolls_back_all_rows`](../tests/test_chat_migration.py#L147) | Mid* / commented | Scenario: root.migration-chat-rollback. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## tests/test_cleanup.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`Cleaning.test_committed_old_folder_goes_without_reading_any_payload`](../tests/test_cleanup.py#L23) | Mid* / commented | Scenario: committed old folder goes without reading any payload. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Cleaning.test_new_age_is_strict_and_future_and_living_folders_stay`](../tests/test_cleanup.py#L34) | Mid* / commented | Scenario: new age is strict and future and living folders stay. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Cleaning.test_uncertain_new_record_never_authorizes_removal`](../tests/test_cleanup.py#L52) | Mid* / commented | Scenario: uncertain new record never authorizes removal. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Cleaning.test_symlink_and_non_uuid_names_cannot_remove_an_outside_folder`](../tests/test_cleanup.py#L78) | Mid* / commented | Scenario: symlink and non uuid names cannot remove an outside folder. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Cleaning.test_named_settle_keeps_dot_folders_but_empty_all_settle_cleans_without_a_launcher`](../tests/test_cleanup.py#L94) | Mid* / commented | Scenario: named settle keeps dot folders but empty all settle cleans without a launcher. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Cleaning.test_failed_cleanup_is_reported_and_makes_all_settle_unsuccessful`](../tests/test_cleanup.py#L105) | Mid* / commented | Scenario: failed cleanup is reported and makes all settle unsuccessful. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Cleaning.test_cleanup_still_runs_before_a_no_fit_refusal`](../tests/test_cleanup.py#L116) | Mid* / commented | Scenario: cleanup still runs before a no fit refusal. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Cleaning.test_disappeared_name_is_harmless_but_unavailable_catalogue_refuses`](../tests/test_cleanup.py#L127) | Mid* / commented | Scenario: root.cleanup-disappearance. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## tests/test_commands.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`Commands.test_trunks_forwards_reply_bytes_exact_arguments_and_launcher_path`](../tests/test_commands.py#L55) | Mid* / commented | Scenario: trunks forwards reply bytes exact arguments and launcher path. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Commands.test_refusal_available_and_stderr_pass_through`](../tests/test_commands.py#L67) | Mid* / commented | Scenario: refusal available and stderr pass through. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Commands.test_first_object_line_is_the_reply_and_nonzero_status_is_not_success`](../tests/test_commands.py#L76) | Mid* / commented | Scenario: first object line is the reply and nonzero status is not success. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Commands.test_missing_unexecutable_and_no_object_are_unavailable`](../tests/test_commands.py#L85) | Mid* / commented | Scenario: missing unexecutable and no object are unavailable. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Commands.test_options_accept_both_forms_and_either_side_but_reject_duplicates`](../tests/test_commands.py#L98) | Mid* / commented | Scenario: options accept both forms and either side but reject duplicates. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Commands.test_root_selection_is_explicit_and_root_dir_requires_bin_dir`](../tests/test_commands.py#L110) | Mid* / commented | Scenario: root selection is explicit and root dir requires bin dir. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Commands.test_damaged_missing_nonregular_or_mismatched_root_is_unknown`](../tests/test_commands.py#L122) | Mid* / commented | Scenario: damaged missing nonregular or mismatched root is unknown. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Commands.test_build_identity_is_adjacent_and_not_from_environment`](../tests/test_commands.py#L138) | Mid* / commented | Scenario: build identity is adjacent and not from environment. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Commands.test_no_settings_or_exchange_payload_is_opened`](../tests/test_commands.py#L164) | Mid* / commented | Scenario: no settings or exchange payload is opened. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## tests/test_groups.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`GroupIdentity.test_group_reader_has_clean_environment_absolute_times_and_excludes_zombies`](../tests/test_groups.py#L31) | Mid* / commented | Scenario: group reader has clean environment absolute times and excludes zombies. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`GroupIdentity.test_full_escalation_uses_awake_five_second_deadlines_and_refuses_survivors`](../tests/test_groups.py#L49) | Mid* / commented | Scenario: root.stop-escalation-clock. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`GroupIdentity.test_complete_stop_uses_20_5_5_with_an_in_process_moved_clock`](../tests/test_groups.py#L68) | Mid* / commented | Scenario: complete stop uses 20 5 5 with an in process moved clock. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`GroupIdentity.test_reused_or_unanchored_group_is_never_killed_after_term`](../tests/test_groups.py#L91) | Top / active | Changes the process table between TERM and escalation. Requires refusal without a second signal when the leader is reused or no previously verified member remains. |
| [`GroupIdentity.test_new_members_are_owned_only_while_a_verified_member_continues`](../tests/test_groups.py#L103) | Mid* / commented | Scenario: new members are owned only while a verified member continues. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`GroupIdentity.test_wrong_group_or_process_failure_refuses_before_a_signal`](../tests/test_groups.py#L112) | Mid* / commented | Scenario: wrong group or process failure refuses before a signal. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`GroupIdentity.test_process_reader_failure_after_term_is_not_ended_without_another_signal`](../tests/test_groups.py#L135) | Mid* / commented | Scenario: process reader failure after term is not ended without another signal. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`NativeForce.test_private_group_that_obeys_term`](../tests/test_groups.py#L165) | Mid* / commented | Scenario: private group that obeys term. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`NativeForce.test_private_group_that_ignores_term_is_killed`](../tests/test_groups.py#L171) | Mid* / commented | Scenario: private group that ignores term is killed. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`NativeForce.test_ignored_child_is_killed_after_its_leader_exits`](../tests/test_groups.py#L177) | Mid* / commented | Scenario: ignored child is killed after its leader exits. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`NativeForce.test_changed_record_and_unreadable_record_cannot_signal_a_replacement`](../tests/test_groups.py#L183) | Mid* / commented | Scenario: changed record and unreadable record cannot signal a replacement. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## tests/test_layout_check.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`Statements.test_semicolons_comments_case_and_quoted_contents_have_distinct_meanings`](../tests/test_layout_check.py#L19) | Mid* / commented | Scenario: semicolons comments case and quoted contents have distinct meanings. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Statements.test_incomplete_statements_client_commands_and_data_writes_are_refused`](../tests/test_layout_check.py#L32) | Mid* / commented | Scenario: incomplete statements client commands and data writes are refused. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`LayoutCheck.test_both_packaged_files_run_twice_with_stable_dump_and_comments`](../tests/test_layout_check.py#L69) | Mid* / commented | Scenario: both packaged files run twice with stable dump and comments. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`LayoutCheck.test_a_nonrepeatable_statement_fails_on_its_second_run`](../tests/test_layout_check.py#L76) | Mid* / commented | Scenario: root.layout-not-repeatable. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`LayoutCheck.test_a_sequence_requires_its_comment_and_a_repeatable_create`](../tests/test_layout_check.py#L85) | Mid* / commented | Scenario: root.layout-sequence-comments. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`LayoutCheck.test_every_table_and_column_needs_a_comment`](../tests/test_layout_check.py#L97) | Mid* / commented | Scenario: every table and column needs a comment. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`LayoutCheck.test_a_client_command_cannot_create_a_database_or_connect_elsewhere`](../tests/test_layout_check.py#L106) | Mid* / commented | Scenario: a client command cannot create a database or connect elsewhere. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`LayoutCheck.test_check_entry_bootstraps_its_own_source_path_before_refusing_an_incomplete_image`](../tests/test_layout_check.py#L115) | Mid* / commented | Scenario: check entry bootstraps its own source path before refusing an incomplete image. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## tests/test_layout_compatibility.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`LayoutCompatibility.test_nullable_defaulted_columns_nonunique_index_and_new_table_are_compatible`](../tests/test_layout_compatibility.py#L58) | Mid* / commented | Scenario: root.layout-compatible-additions. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`LayoutCompatibility.test_editing_an_earlier_statement_is_refused`](../tests/test_layout_compatibility.py#L79) | Mid* / commented | Scenario: root.layout-edited-statement. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`LayoutCompatibility.test_required_column_without_default_is_refused_on_an_older_table`](../tests/test_layout_compatibility.py#L87) | Mid* / commented | Scenario: root.layout-required-column. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`LayoutCompatibility.test_unique_index_and_new_check_on_an_older_table_are_refused`](../tests/test_layout_compatibility.py#L96) | Mid* / commented | Scenario: root.layout-new-constraints. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`LayoutCompatibility.test_appending_a_comment_override_cannot_change_an_older_object`](../tests/test_layout_compatibility.py#L105) | Mid* / commented | Scenario: appending a comment override cannot change an older object. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`LayoutCompatibility.test_statement_presentation_changes_preserve_the_same_schema`](../tests/test_layout_compatibility.py#L112) | Mid* / commented | Scenario: statement presentation changes preserve the same schema. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`LayoutCompatibility.test_baseline_is_highest_earlier_matching_working_build_with_both_files`](../tests/test_layout_compatibility.py#L118) | Mid* / commented | Scenario: baseline is highest earlier matching working build with both files. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## tests/test_layout_copy.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`LayoutCopy.test_exact_version_and_root_files_and_no_migration_without_lineage`](../tests/test_layout_copy.py#L40) | Mid* / commented | Scenario: exact version and root files and no migration without lineage. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`LayoutCopy.test_lineage_requires_and_copies_migration_exactly`](../tests/test_layout_copy.py#L52) | Mid* / commented | Scenario: lineage requires and copies migration exactly. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`LayoutCopy.test_every_missing_file_fails_before_any_copy`](../tests/test_layout_copy.py#L64) | Mid* / commented | Scenario: every missing file fails before any copy. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`LayoutCopy.test_bad_root_contract_lineage_and_identity_cannot_escape_source`](../tests/test_layout_copy.py#L77) | Mid* / commented | Scenario: bad root contract lineage and identity cannot escape source. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`LayoutCopy.test_optional_modes_copy_exactly_and_bad_or_lineageless_capabilities_write_nothing`](../tests/test_layout_copy.py#L97) | Mid* / commented | Scenario: root.layout-migration-modes. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## tests/test_listing.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`Listing.test_all_six_states_are_read_from_records_alone_in_deterministic_order`](../tests/test_listing.py#L48) | Mid* / commented | Scenario: all six states are read from records alone in deterministic order. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Listing.test_unknown_values_are_kept_unknown_fields_ignored_and_end_errors_whole`](../tests/test_listing.py#L71) | Mid* / commented | Scenario: root.list-forward-compatible. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Listing.test_missing_malformed_fifo_symlink_records_are_isolated_without_following`](../tests/test_listing.py#L88) | Mid* / commented | Scenario: missing malformed fifo symlink records are isolated without following. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Listing.test_bad_record_fields_and_process_check_failure_are_unreadable`](../tests/test_listing.py#L113) | Mid* / commented | Scenario: root.list-record-validation. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Listing.test_directory_gone_before_record_read_is_left_out_and_missing_record_is_unreadable`](../tests/test_listing.py#L134) | Mid* / commented | Scenario: directory gone before record read is left out and missing record is unreadable. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Listing.test_missing_catalogue_is_empty_but_file_symlink_or_enumeration_error_refuses`](../tests/test_listing.py#L149) | Mid* / commented | Scenario: missing catalogue is empty but file symlink or enumeration error refuses. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Listing.test_cli_lists_with_own_identity_and_no_launcher_settings_or_payload_access`](../tests/test_listing.py#L171) | Mid* / commented | Scenario: cli lists with own identity and no launcher settings or payload access. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`ProcessIdentity.test_native_live_gone_and_reused_pid_identity`](../tests/test_listing.py#L190) | Mid* / commented | Scenario: native live gone and reused pid identity. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`ProcessIdentity.test_clean_c_utc_ps_environment_and_two_second_tolerance`](../tests/test_listing.py#L202) | Mid* / commented | Scenario: root.list-process-environment. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## tests/test_listing_form.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`ListingForm.test_published_listing_fields_and_meanings_are_kept_with_only_additions`](../tests/test_listing_form.py#L28) | Mid* / commented | Scenario: published listing fields and meanings are kept with only additions. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## tests/test_management_boundary.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`Boundary.test_every_command_uses_private_root_identity_without_payload_settings_or_retained_manager_files`](../tests/test_management_boundary.py#L13) | Mid* / commented | Scenario: every command uses private root identity without payload settings or retained manager files. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Boundary.test_a_failed_record_stat_is_a_structured_refusal`](../tests/test_management_boundary.py#L46) | Mid* / commented | Scenario: a failed record stat is a structured refusal. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## tests/test_management_input.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`ManagementInput.test_invalid_arguments_and_force_are_refused`](../tests/test_management_input.py#L15) | Mid* / commented | Scenario: invalid arguments and force are refused. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`ProcessFixture.test_private_leader_and_ignored_child_share_an_isolated_group`](../tests/test_management_input.py#L29) | Mid* / commented | Scenario: private leader and ignored child share an isolated group. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## tests/test_migration_check.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`MigrationCheck.test_whole_protocol_preserves_rows_text_snapshot_provenance_rollback_and_repeat`](../tests/test_migration_check.py#L51) | Mid* / commented | Scenario: whole protocol preserves rows text snapshot provenance rollback and repeat. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`MigrationCheck.test_a_root_without_lineage_passes_without_a_server_or_tools`](../tests/test_migration_check.py#L77) | Mid* / commented | Scenario: root.migration-no-lineage. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`MigrationCheck.test_parent_identity_and_layout_inputs_are_required_before_starting_a_server`](../tests/test_migration_check.py#L88) | Mid* / commented | Scenario: parent identity and layout inputs are required before starting a server. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`MigrationCheck.test_corrupting_copied_text_fails_the_actual_row_judgment`](../tests/test_migration_check.py#L105) | Mid* / commented | Scenario: root.migration-text-fault. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`MigrationCheck.test_wrong_provenance_fails_the_actual_row_judgment`](../tests/test_migration_check.py#L116) | Mid* / commented | Scenario: root.migration-provenance-fault. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`MigrationCheck.test_an_open_exchange_must_be_interrupted_at_the_snapshot`](../tests/test_migration_check.py#L127) | Mid* / commented | Scenario: root.migration-open-fault. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`MigrationCheck.test_a_snapshot_outside_the_run_is_rejected_even_if_both_times_match`](../tests/test_migration_check.py#L137) | Mid* / commented | Scenario: root.migration-snapshot-fault. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## tests/test_migration_drills.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`MigrationHelpers.test_repeatable_read_fingerprints_preserve_exact_text_numbers_and_order`](../tests/test_migration_drills.py#L46) | Mid* / commented | Scenario: sapling.migration-fingerprint. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`MigrationHelpers.test_a_concurrent_transaction_never_splits_the_multi_table_snapshot`](../tests/test_migration_drills.py#L67) | Mid* / commented | Scenario: sapling.migration-snapshot-consistency. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`MigrationHelpers.test_observed_owned_copy_is_frozen_thawed_and_its_lock_client_is_reaped`](../tests/test_migration_drills.py#L116) | Mid* / commented | Scenario: sapling.migration-owned-copy. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`MigrationHelpers.test_frozen_source_copy_fails_after_private_shutdown_and_service_is_restored`](../tests/test_migration_drills.py#L145) | Mid* / commented | Scenario: sapling.migration-private-outage. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`MigrationHelpers.test_copy_judgment_checks_actual_private_sql_bytes_snapshot_and_provenance`](../tests/test_migration_drills.py#L174) | Mid* / commented | Scenario: sapling.migration-copy-judgment. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`MigrationHelpers.test_source_lock_constructor_failure_cleans_its_private_client`](../tests/test_migration_drills.py#L213) | Mid* / commented | Scenario: sapling.migration-lock-failure. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Creation.test_second_root_creation_uses_three_merged_checks_and_never_migrates_or_readies`](../tests/test_migration_drills.py#L227) | Mid* / commented | Scenario: sapling.second-root-creation. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`RootOwnership.test_jensen_owned_commands_and_snapshots_never_fall_back_to_sapling`](../tests/test_migration_drills.py#L291) | Mid* / commented | Scenario: sapling.migration-root-exchange. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`ContinuationJudgment.test_saved_chat_history_has_exact_order_word_and_next_number_and_refuses_busy`](../tests/test_migration_drills.py#L330) | Mid* / commented | Scenario: sapling.migration-history-judgment. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`ContinuationJudgment.test_history_judgment_selects_the_single_run_among_discovery_records`](../tests/test_migration_drills.py#L344) | Mid* / commented | Scenario: sapling.migration-driver-records. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`ContinuationJudgment.test_saved_timestamp_offsets_compare_as_instants_without_normalizing_text_or_json`](../tests/test_migration_drills.py#L359) | Mid* / commented | Scenario: sapling.migration-saved-timezones. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`ContinuationJudgment.test_usage_refusal_prevents_reservation_and_ambiguous_acceptance_is_counted_once`](../tests/test_migration_drills.py#L372) | Mid* / commented | Scenario: sapling.migration-real-budget. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`ReadyJudgment.test_ready_changes_cleanup_root_only_from_observed_catalogue_even_after_ambiguous_reply`](../tests/test_migration_drills.py#L407) | Mid* / commented | Scenario: sapling.migration-ready-judgment. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`ReimportJudgment.test_exact_encoded_history_remaps_only_relational_uuid_fields_and_keeps_json_digits`](../tests/test_migration_drills.py#L452) | Mid* / commented | Scenario: sapling.chat-reimport-judgment. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`ReimportJudgment.test_reimport_phase_preview_and_started_phase_guard_make_no_owner_call`](../tests/test_migration_drills.py#L489) | Mid* / commented | Scenario: sapling.chat-reimport-guard. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## tests/test_migration_protocol.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`MigrationProtocol.test_prescribed_script_uses_two_private_connections_and_relative_binary_copies`](../tests/test_migration_protocol.py#L13) | Mid* / commented | Scenario: prescribed script uses two private connections and relative binary copies. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`MigrationProtocol.test_connection_file_and_transaction_faults_are_refused_before_execution`](../tests/test_migration_protocol.py#L20) | Mid* / commented | Scenario: root.migration-protocol-refusal. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## tests/test_package.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`Package.test_package_contains_only_own_assets_runtime_and_complete_file_hashes`](../tests/test_package.py#L51) | Mid* / commented | Scenario: package contains only own assets runtime and complete file hashes. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Package.test_relocated_shell_entry_execs_own_python_with_arguments_and_same_pid`](../tests/test_package.py#L68) | Mid* / commented | Scenario: relocated shell entry execs own python with arguments and same pid. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Package.test_numbered_image_is_verified_after_sql_copy_and_tampering_is_detected`](../tests/test_package.py#L82) | Mid* / commented | Scenario: numbered image is verified after sql copy and tampering is detected. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Package.test_bad_cached_digest_and_untrusted_archive_pin_are_refused`](../tests/test_package.py#L113) | Mid* / commented | Scenario: bad cached digest and untrusted archive pin are refused. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Package.test_metadata_overlap_and_bad_numbered_identity_are_refused`](../tests/test_package.py#L128) | Mid* / commented | Scenario: metadata overlap and bad numbered identity are refused. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## tests/test_sapling_drills.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`Outage.test_installed_stop_completes_smart_shutdown_with_an_established_private_connection`](../tests/test_sapling_drills.py#L22) | Mid* / commented | Scenario: sapling.connected-shutdown: refusing new clients alone is not a database outage.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Outage.test_private_server_is_restored_after_success_failure_partial_stop_and_real_signals`](../tests/test_sapling_drills.py#L69) | Mid* / commented | Scenario: sapling.restore: success, errors, partial stops and real SIGINT/SIGTERM all restore and prove health.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Outage.test_failed_restore_is_reported_and_original_handlers_are_still_restored`](../tests/test_sapling_drills.py#L103) | Mid* / commented | Scenario: sapling.restore-failure: an unverified restoration cannot produce a passing receipt.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Outage.test_run_directory_watch_detects_a_file_that_was_created_and_already_removed`](../tests/test_sapling_drills.py#L121) | Mid* / commented | Scenario: sapling.no-driver-run: two empty snapshots cannot hide a fleeting run file.. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Frame.test_receipts_are_private_and_never_overwrite_an_earlier_attempt`](../tests/test_sapling_drills.py#L147) | Mid* / commented | Scenario: receipts are private and never overwrite an earlier attempt. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Frame.test_json_commands_preserve_arguments_and_reject_bad_status_or_non_json`](../tests/test_sapling_drills.py#L158) | Mid* / commented | Scenario: json commands preserve arguments and reject bad status or non json. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Frame.test_wait_has_a_deadline_and_never_retries_after_that_deadline`](../tests/test_sapling_drills.py#L183) | Mid* / commented | Scenario: wait has a deadline and never retries after that deadline. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Frame.test_budget_reserves_before_submission_caps_ten_and_never_replays_an_exchange`](../tests/test_sapling_drills.py#L198) | Mid* / commented | Scenario: budget reserves before submission caps ten and never replays an exchange. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Frame.test_torn_or_unknown_budget_history_refuses_new_spending`](../tests/test_sapling_drills.py#L219) | Mid* / commented | Scenario: torn or unknown budget history refuses new spending. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Frame.test_two_processes_cannot_both_spend_the_last_available_message`](../tests/test_sapling_drills.py#L231) | Mid* / commented | Scenario: sapling.budget-concurrent. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`ReadOnly.test_inspection_uses_its_private_server_and_cannot_write`](../tests/test_sapling_drills.py#L258) | Mid* / commented | Scenario: inspection uses its private server and cannot write. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Creation.test_creation_runs_the_named_steps_and_preserves_receipts`](../tests/test_sapling_drills.py#L311) | Mid* / commented | Scenario: creation runs the named steps and preserves receipts. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Creation.test_existing_or_unpublished_root_is_never_migrated_or_removed`](../tests/test_sapling_drills.py#L327) | Mid* / commented | Scenario: existing or unpublished root is never migrated or removed. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Creation.test_failed_build_stops_before_migration_and_keeps_created_receipt`](../tests/test_sapling_drills.py#L343) | Mid* / commented | Scenario: failed build stops before migration and keeps created receipt. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Creation.test_branch_source_is_refused_before_create`](../tests/test_sapling_drills.py#L359) | Mid* / commented | Scenario: branch source is refused before create. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Messages.test_preflight_does_not_submit_and_two_explicit_submissions_keep_the_same_chat`](../tests/test_sapling_drills.py#L421) | Mid* / commented | Scenario: preflight does not submit and two explicit submissions keep the same chat. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Messages.test_ambiguous_start_counts_and_is_never_automatically_retried`](../tests/test_sapling_drills.py#L437) | Mid* / commented | Scenario: sapling.messages-ambiguous. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Messages.test_no_two_message_allowance_means_no_submission`](../tests/test_sapling_drills.py#L449) | Mid* / commented | Scenario: sapling.messages-allowance. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Messages.test_known_vendor_retry_deadline_blocks_even_a_cached_report_showing_available_capacity`](../tests/test_sapling_drills.py#L459) | Mid* / commented | Scenario: sapling.messages-retry-deadline. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Messages.test_reached_or_unavailable_usage_never_submits`](../tests/test_sapling_drills.py#L472) | Mid* / commented | Scenario: reached or unavailable usage never submits. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Messages.test_elapsed_cached_limit_permits_one_explicit_same_chat_pair`](../tests/test_sapling_drills.py#L490) | Mid* / commented | Scenario: sapling.messages-expired-usage. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Messages.test_elapsed_window_does_not_hide_unknown_future_or_other_active_limits`](../tests/test_sapling_drills.py#L510) | Mid* / commented | Scenario: sapling.messages-unproved-reset. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Messages.test_judgement_refuses_lost_history_wrong_route_or_missing_usage`](../tests/test_sapling_drills.py#L538) | Mid* / commented | Scenario: sapling.messages-judgement. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## tests/test_settle.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`Settling.test_named_settle_delegates_missing_or_living_exchange_to_exact_chosen_build`](../tests/test_settle.py#L15) | Mid* / commented | Scenario: named settle delegates missing or living exchange to exact chosen build. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Settling.test_all_settle_is_lexical_skips_living_and_selects_only_once`](../tests/test_settle.py#L33) | Mid* / commented | Scenario: all settle is lexical skips living and selects only once. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Settling.test_empty_or_only_living_needs_no_launcher`](../tests/test_settle.py#L49) | Mid* / commented | Scenario: empty or only living needs no launcher. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Settling.test_database_refusal_stops_before_the_next_exchange_and_keeps_extra_fields`](../tests/test_settle.py#L60) | Mid* / commented | Scenario: root.settle-database-refusal. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Settling.test_no_fit_and_selection_refusal_never_start_settling`](../tests/test_settle.py#L78) | Mid* / commented | Scenario: no fit and selection refusal never start settling. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Settling.test_missing_or_nonobject_settle_reply_is_a_per_exchange_refusal`](../tests/test_settle.py#L93) | Mid* / commented | Scenario: missing or nonobject settle reply is a per exchange refusal. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Settling.test_unreadable_record_is_retained_and_reported_without_delegation`](../tests/test_settle.py#L108) | Mid* / commented | Scenario: unreadable record is retained and reported without delegation. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Settling.test_stop_gets_a_selection_failure_as_an_outcome`](../tests/test_settle.py#L120) | Mid* / commented | Scenario: stop gets a selection failure as an outcome. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Settling.test_nonzero_child_status_is_not_reported_as_success`](../tests/test_settle.py#L128) | Mid* / commented | Scenario: nonzero child status is not reported as success. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Settling.test_success_without_a_state_or_with_a_different_exchange_is_unavailable`](../tests/test_settle.py#L137) | Mid* / commented | Scenario: root.settle-reply-identity. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## tests/test_sql_support.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`SqlSupport.test_each_missing_tool_is_named_before_a_server_can_start`](../tests/test_sql_support.py#L27) | Mid* / commented | Scenario: each missing tool is named before a server can start. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`SqlSupport.test_copied_build_identity_and_lineage_are_validated_before_sql`](../tests/test_sql_support.py#L42) | Mid* / commented | Scenario: copied build identity and lineage are validated before sql. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`SqlSupport.test_nonregular_sql_input_is_never_followed_or_read`](../tests/test_sql_support.py#L65) | Mid* / commented | Scenario: nonregular sql input is never followed or read. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`SqlSupport.test_private_server_ignores_caller_pg_variables_and_dumps_a_stable_schema`](../tests/test_sql_support.py#L84) | Mid* / commented | Scenario: private server ignores caller pg variables and dumps a stable schema. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`SqlSupport.test_private_server_is_removed_after_a_failed_check`](../tests/test_sql_support.py#L104) | Mid* / commented | Scenario: private server is removed after a failed check. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`SqlSupport.test_fictional_rows_cover_replacement_open_history_and_exact_text`](../tests/test_sql_support.py#L115) | Mid* / commented | Scenario: fictional rows cover replacement open history and exact text. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## tests/test_standin.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`StandIn.test_scripts_list_run_fragments_and_process_observation`](../tests/test_standin.py#L11) | Mid* / commented | Scenario: scripts list run fragments and process observation. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`StandIn.test_detached_reply_closes_pipes_before_the_stand_in_ends`](../tests/test_standin.py#L41) | Mid* / commented | Scenario: detached reply closes pipes before the stand in ends. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## tests/test_start.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`Starting.test_cli_chooses_exact_build_preserves_options_group_stdin_and_cwd`](../tests/test_start.py#L78) | Mid* / commented | Scenario: cli chooses exact build preserves options group stdin and cwd. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Starting.test_explicit_build_skips_list_and_does_not_read_a_fifo_request`](../tests/test_start.py#L96) | Mid* / commented | Scenario: root.start-no-request-read. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Starting.test_refusal_line_is_unchanged_and_also_removes_request`](../tests/test_start.py#L108) | Mid* / commented | Scenario: refusal line is unchanged and also removes request. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Starting.test_returns_on_a_fragmented_object_without_waiting_for_trunk_exit`](../tests/test_start.py#L118) | Top / active | Splits an acceptance JSON object across writes after diagnostic/non-object output, while the Trunk stays alive. Requires an immediate valid reply instead of waiting for process exit or rejecting a partial frame. |
| [`Starting.test_timeout_keeps_request_and_process_and_a_late_writer_can_still_finish`](../tests/test_start.py#L128) | Top / active | Holds the reply beyond the start timeout. Confirms the request bytes and child survive the uncertain outcome and the child can subsequently finish, preventing destructive timeout cleanup. |
| [`Starting.test_eof_without_object_preserves_request_and_final_unterminated_object_is_accepted`](../tests/test_start.py#L142) | Mid* / commented | Scenario: eof without object preserves request and final unterminated object is accepted. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Starting.test_preflight_refusal_or_no_fit_does_not_start_run_or_remove_request`](../tests/test_start.py#L155) | Mid* / commented | Scenario: preflight refusal or no fit does not start run or remove request. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Starting.test_cleanup_failure_is_diagnostic_after_a_reply_and_spawn_failure_keeps_request`](../tests/test_start.py#L173) | Mid* / commented | Scenario: cleanup failure is diagnostic after a reply and spawn failure keeps request. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## tests/test_start_selection.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`Selection.test_input_preserves_run_option_order_spelling_and_values`](../tests/test_start_selection.py#L22) | Mid* / commented | Scenario: input preserves run option order spelling and values. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Selection.test_invalid_start_input_is_refused_before_selection`](../tests/test_start_selection.py#L37) | Mid* / commented | Scenario: invalid start input is refused before selection. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Selection.test_no_fit_lists_only_fitting_runnable_build_numbers_without_starting`](../tests/test_start_selection.py#L49) | Mid* / commented | Scenario: no fit lists only fitting runnable build numbers without starting. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Selection.test_malformed_or_wrong_inventory_is_unavailable`](../tests/test_start_selection.py#L61) | Mid* / commented | Scenario: malformed or wrong inventory is unavailable. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## tests/test_stop.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`Stopping.test_missing_exchange_is_none_without_launching_or_creating_control`](../tests/test_stop.py#L28) | Mid* / commented | Scenario: missing exchange is none without launching or creating control. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Stopping.test_dead_process_is_settled_without_a_stop_line_and_reports_the_observed_state`](../tests/test_stop.py#L39) | Mid* / commented | Scenario: dead process is settled without a stop line and reports the observed state. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Stopping.test_settling_refusal_keeps_a_dead_stop_successful_with_its_known_end`](../tests/test_stop.py#L54) | Mid* / commented | Scenario: settling refusal keeps a dead stop successful with its known end. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Stopping.test_cooperative_stop_appends_once_and_preserves_an_existing_answer_line`](../tests/test_stop.py#L73) | Mid* / commented | Scenario: cooperative stop appends once and preserves an existing answer line. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Stopping.test_disappearing_folder_after_a_stop_is_saved`](../tests/test_stop.py#L89) | Mid* / commented | Scenario: disappearing folder after a stop is saved. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Stopping.test_already_ended_living_record_is_not_written_or_signalled`](../tests/test_stop.py#L99) | Mid* / commented | Scenario: already ended living record is not written or signalled. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Stopping.test_publication_wait_is_bounded_and_picks_up_a_newly_published_record`](../tests/test_stop.py#L113) | Mid* / commented | Scenario: publication wait is bounded and picks up a newly published record. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Stopping.test_nonregular_missing_or_symlink_control_refuses_without_force`](../tests/test_stop.py#L136) | Mid* / commented | Scenario: root.stop-control-refusal. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Stopping.test_short_control_write_is_not_retried`](../tests/test_stop.py#L156) | Mid* / commented | Scenario: short control write is not retried. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Stopping.test_reused_pid_is_treated_as_gone_and_never_signalled`](../tests/test_stop.py#L168) | Mid* / commented | Scenario: root.stop-process-identity. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Stopping.test_graceful_deadline_calls_escalation_after_twenty_awake_seconds`](../tests/test_stop.py#L184) | Mid* / commented | Scenario: graceful deadline calls escalation after twenty awake seconds. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## tests/test_stopping_drills.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`Freeze.test_a_private_process_is_thawed_after_success_body_failure_and_real_signals`](../tests/test_stopping_drills.py#L15) | Mid* / commented | Scenario: a private process is thawed after success body failure and real signals. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Freeze.test_reused_or_stale_identity_never_gets_a_thaw_signal`](../tests/test_stopping_drills.py#L44) | Mid* / commented | Scenario: sapling.freeze-reused-pid. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`Freeze.test_failure_during_stop_delivery_still_attempts_to_thaw_the_same_owned_process`](../tests/test_stopping_drills.py#L63) | Mid* / commented | Scenario: sapling.freeze-delivery-race. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`IgnoredChild.test_private_wrapper_child_records_term_and_survives_until_explicit_kill`](../tests/test_stopping_drills.py#L83) | Mid* / commented | Scenario: private wrapper child records term and survives until explicit kill. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`IgnoredChild.test_owned_manager_reply_and_kill_reap_only_the_started_private_command`](../tests/test_stopping_drills.py#L123) | Mid* / commented | Scenario: owned manager reply and kill reap only the started private command. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`StoppingJudgment.test_saved_graceful_reply_is_valid_but_force_and_settling_cannot_be_invented`](../tests/test_stopping_drills.py#L159) | Mid* / commented | Scenario: sapling.stop-reply-judgment. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`StoppingJudgment.test_reuse_requires_retained_passing_checks_source_status_and_chosen_build`](../tests/test_stopping_drills.py#L171) | Mid* / commented | Scenario: sapling.newer-build-receipt. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## tests/test_trunk_drills.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`PrivateDriver.test_copied_launcher_and_actual_standin_use_only_the_private_home`](../tests/test_trunk_drills.py#L28) | Mid* / commented | Scenario: sapling.standin-isolation. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`PrivateDriver.test_actual_script_output_and_request_are_recorded_without_owner_state`](../tests/test_trunk_drills.py#L46) | Mid* / commented | Scenario: actual script output and request are recorded without owner state. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`PrivateDriver.test_scenario_release_and_finish_are_owned_and_reset_between_uses`](../tests/test_trunk_drills.py#L61) | Mid* / commented | Scenario: scenario release and finish are owned and reset between uses. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`ProcessAndRows.test_persisted_identity_and_exactly_one_matching_end_are_required`](../tests/test_trunk_drills.py#L75) | Mid* / commented | Scenario: sapling.drill-end-identity. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`ProcessAndRows.test_real_recovery_keeps_every_whole_block_but_never_saves_fragments_as_messages`](../tests/test_trunk_drills.py#L90) | Mid* / commented | Scenario: sapling.drill-real-row-mapping. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`ProcessAndRows.test_live_private_process_identity_is_checked_before_a_signal`](../tests/test_trunk_drills.py#L107) | Mid* / commented | Scenario: sapling.drill-process-identity. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`ProcessAndRows.test_missing_nonleader_and_own_group_refuse_without_signalling`](../tests/test_trunk_drills.py#L125) | Mid* / commented | Scenario: sapling.drill-process-refusal. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`ProcessAndRows.test_new_rows_are_allowed_but_changing_or_dropping_old_rows_refuses`](../tests/test_trunk_drills.py#L137) | Mid* / commented | Scenario: sapling.drill-existing-rows. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`ProcessAndRows.test_failed_drill_still_closes_frame_and_saves_its_failure`](../tests/test_trunk_drills.py#L148) | Mid* / commented | Scenario: sapling.drill-failure-cleanup. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`ProcessAndRows.test_real_variant_is_refused_for_every_other_drill_before_frame_creation`](../tests/test_trunk_drills.py#L162) | Mid* / commented | Scenario: sapling.drill-real-boundary. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## tests/test_vigor_tables.py

| Test or check | Tier / state | Justification |
| --- | --- | --- |
| [`OperationalBoundary.test_default_preview_does_not_open_an_owner_folder_or_start_a_build`](../tests/test_vigor_tables.py#L26) | Mid* / commented | Scenario: default preview does not open an owner folder or start a build. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`OperationalBoundary.test_operational_guard_detects_old_row_schema_backend_and_vigor_damage`](../tests/test_vigor_tables.py#L44) | Mid* / commented | Scenario: operational guard detects old row schema backend and vigor damage. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`VigorTables.test_both_layouts_carry_the_same_vigor_tables_and_repeat_fully_commented`](../tests/test_vigor_tables.py#L114) | Mid* / commented | Scenario: both layouts carry the same vigor tables and repeat fully commented. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`VigorTables.test_fictional_rows_are_exact_and_survive_a_repeated_layout`](../tests/test_vigor_tables.py#L136) | Mid* / commented | Scenario: fictional rows are exact and survive a repeated layout. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`VigorTables.test_the_tables_refuse_a_repeated_report_and_an_inconsistent_result`](../tests/test_vigor_tables.py#L155) | Mid* / commented | Scenario: the tables refuse a repeated report and an inconsistent result. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |
| [`VigorTables.test_whole_migration_still_passes_and_copies_no_vigor_row`](../tests/test_vigor_tables.py#L192) | Mid* / commented | Scenario: whole migration still passes and copies no vigor row. Disabled because no independently reviewed top-tier rationale was established for this case. Mid is provisional, not a verdict that every assertion is useful. |

## Low tier removed in the prior pass

Source remains in Git at the reviewed revision; these cases are not reintroduced as comments. Supporting evidence is in the October pruning report.

| Former test | Tier / state | Justification |
| --- | --- | --- |
| `contract/conformance/tests/test_coverage.py::Coverage.test_every_trunk_requirement_naming_contract_has_a_scenario` | Low / removed | Compares declarative coverage labels, not scenario behavior or assertion quality. |
| `contract/conformance/tests/test_coverage.py::Coverage.test_every_scenario_of_the_complete_registry_has_a_run` | Low / removed | Copies the expected registry number sequence and checks callable fields already visible in its construction. |
| `contract/conformance/tests/test_cli.py::Cli.test_help` | Low / removed | Only checks the fixed help branch returns zero and includes a declared option; the actual parser/refusal/runner boundaries are exercised elsewhere. |
| `tests/test_groups.py::GroupIdentity.test_os_clock_is_uptime_raw_on_this_mac` | Low / removed | Mocks the clock and copies the wrapper exact clock-selection expression; it does not establish awake-time semantics. |
| `tests/test_management_input.py::ManagementInput.test_stop_and_settle_uuid_arguments_and_common_options` | Low / removed | Copies ordinary valid option records and an absent exchange default. |
| `tests/test_start_selection.py::Selection.test_explicit_build_does_not_query_the_launcher` | Low / removed | Mocks list_reply around a direct explicit-build return already exercised in the real start path. |
| `tests/test_start_selection.py::Selection.test_uses_the_chosen_build_from_exact_root_and_trunk_inventory` | Low / removed | Supplies one pre-marked chosen build and checks its name plus mocked call arguments. |
| `tests/test_start_selection.py::Selection.test_launcher_refusal_is_the_same_raw_reply` | Low / removed | Asserts object identity for the direct error-return branch after supplying the mock reply. |
| `tests/test_listing_form.py::ListingForm.test_two_root_listings_combine_by_their_exchange_entries` | Low / removed | The test itself concatenates two independent listings, then checks ordinary root labels; it exercises no product aggregation behavior. |
| `contract/conformance/tests/test_standin.py::StandIn.test_info_names_contract_1_and_the_build` | Low / removed | Tests static metadata of the test stand-in, echoing its selected fake build and launcher name. |
| `contract/conformance/tests/test_standin.py::StandIn.test_capabilities_offer_the_selected_subscription_without_a_run` | Low / removed | Copies two hard-coded family/subscription lists returned by the stand-in; no production capability behavior is exercised. |
