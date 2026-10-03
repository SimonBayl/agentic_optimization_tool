Everything between the user and the graph. For now it's a terminal chat, mainly used to test and debug the agent step by step.

## Files

- Conversation.py: ConversationSession keeps the AgentState between the turns. `submit` adds the user message, streams the graph and keeps:
  - the new state,
  - history: the previous states, for /undo,
  - steps: what each node returned during the last turn, for /steps (printed live when verbose).
- terminal.py: multiline input (the message is sent with /send) and the chat commands.
- debug.py: prints the state and the node updates as indented JSON (pydantic models, messages and sets are converted).
- data_files.py: builds the data schema from the CSV files of a folder (--data option).

## Chat commands

- /send: send the message typed so far.
- /state [field ...]: print the AgentState, or only some fields (e.g. /state business_spec model_spec). An unknown field prints the list of the available ones.
- /steps: replay the intermediate states of the last turn, node by node.
- /debug: show or hide the node updates during each turn (same as -v).
- /undo: go back to the state before the last turn. /new: start over, the data schema is kept.
- /help, /quit.

At the end of each turn the whole AgentState is printed (all fields, with the turn number), then the reply of the agent, so the question stays next to the prompt.

Errors of a turn are caught and printed, the state is not changed and the user can send the message again.
