Contains the folder related to every tools that the agent can use to guide the user throught the optimization process.


A file utils contains comune function, and I want it to define a decorator function that is comune to every llm calls that holds the try/error policy for the agent (exponential backoff if needed, catch the errors 500, 429 ...)

## utils.py

- `llm_retry(understanding=False)`: the decorator, put it on the method of the tool that calls the LLM (not on `parse`). It retries with exponential backoff (`base_delay * 2**attempt`) on:
  - HTTP errors 408, 429, 500, 502, 503, 504 (MistralError.status_code),
  - network errors (httpx2.TransportError),
  - pydantic ValidationError, when the model returns a malformed structured output (happens with small models).
  Any other error is raised right away. There are 2 policies in parameters.yaml: `retry.default` and `retry.understanding` (longer, used with `understanding=True`).
- `MistralAgent`: base class of every tool calling Mistral. It holds the client, the settings and the model name, and gives:
  - `parse(messages, output)`: calls `chat.parse_async` and returns the parsed pydantic object, raises ValueError when there is nothing to parse,
  - `format_messages(messages)`: the conversation as plain text ("User: ..." / "Agent: ...") to put in the prompts.

## Tools

- understand/: extracts the business spec and asks the business questions (Q_xxx).
- completeness/: drafts the mathematical structure, links it to the data and asks the questions still needed (C_xxx).

A tool never modifies the state itself, it returns its structured output and the node in orchestrator/graph_orchestrator.py decides what goes into the AgentState.
