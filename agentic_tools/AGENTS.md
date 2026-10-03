Contains the folder related to every tools that the agent can use to guide the user throught the optimization process.


A file utils contains comune function, and I want it to define a decorator function that is comune to every llm calls that holds the try/error policy for the agent (exponential backoff if needed, catch the errors 500, 429 ...)

