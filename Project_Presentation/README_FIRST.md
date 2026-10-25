# About these presentation files

These slides and documents were written for the **first version** of the project
(20x20 grid, one agent type, manual "self-organization" button). They do not
describe the current application, and some statements in them were not true
even for the first version, for example:

- "11/11 test suites pass" - the old repository had no runnable pytest suite.
- "Recovery in 12-18 ms" - the old backend added a fixed 12 ms to the measured time.
- "Five agent roles" - the roles were labels picked from the agent number.

Please regenerate the slides from the current README before presenting.
Accurate figures for the current version: 44 automated tests, network
recomputation in a few milliseconds (measured, shown on the Network page),
failure detected after 3 simulated seconds by peer heartbeat.
