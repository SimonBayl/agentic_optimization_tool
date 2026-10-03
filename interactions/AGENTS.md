# interactions

The interface between the user and the graph. It never calls an LLM and
never decides the dialogue: it only submits messages and keeps states.

## Files

- ConversationSession.py: holds the committed state and the undo history.
  - submit: strips the message (an empty one raises ValueError), runs
    the graph on a deep copy of the state with the HumanMessage
    appended, and commits the returned state only if the turn succeeds;
    a failed turn leaves the state and the history unchanged. Returns
    the reply of the turn.
  - undo: restores the state preceding the last committed turn; returns
    False when there is none.
  - verbose: prints the business spec, the clarification state, the
    model spec (marked draft while not ready), the result without its
    code and the deferred IDs after each turn.
  - The graph is typed by the ConversationGraph protocol (`ainvoke`), so
    the tests can pass a deterministic double.
- terminal.py: command line loop. A message spans several lines and is
  sent with /send; an empty message is refused. /undo reverts the last
  turn, /new starts over with the same graph and data schema, /quit
  exits. An error is printed and the same message can be sent again.
- data_schema.py: reads the headers of the `*.csv` files of the data
  folder, in name order and in `utf-8-sig`, into the data schema
  `{file: {column: meaning}}` given to the agents. The meanings come from
  `data_schema.meanings` in parameters.yaml; a column without meaning
  gets UNKNOWN_MEANING, to clarify with the user. The data values are
  never loaded into the LLM context here.
