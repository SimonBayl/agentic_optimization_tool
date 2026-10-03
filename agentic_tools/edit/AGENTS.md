# edit

Edits the model spec once a model has been built. It never rebuilds the
spec: it asks the LLM (`models.editor`) for the smallest ModelPatch
implementing the user request, so unrelated elements stay unchanged.

## Behavior

- Messages sent to the LLM: EDIT_PROMPT as system message, then the
  problem summary, the current spec (JSON), the data schema, the last
  result (summarize_result), the previous reply and the last user
  message. The request is read together with the previous reply, so
  "apply the first relaxation" refers to it.
- The patch is validated without LLM. An invalid patch is sent back with
  its errors (PATCH_RETRY_PROMPT); only the last attempt is kept in the
  messages. After `model_editor.max_attempts`, a patch carrying the
  question FAILED_QUESTION with the errors is returned.
- A patch without operation nor question means the message is a retry or
  a question about the result: it is answered by the explain tool.

## Expected patch

- Operations refer to existing elements by their exact name.
- A new constraint takes the next free `RULE_xxx` name and a quantified
  expression.
- A value given by the user goes into the parameter description, without
  data binding; a penalty, weight or big-M is never invented.
- The model stays linear and its units consistent.
- An ambiguous request, a request already allowed by the model, or one
  designating no existing element gives no operation and one question.

## Validation (patch.py)

An operation is invalid when:

- it targets the objective without action `replace` and name `minimize`
  or `maximize`;
- it adds an element whose name (the symbol for a binding) exists;
- it replaces or removes a missing element; the error lists the
  existing names.

The patched spec is then checked; only errors absent before the patch
count:

- a parameter without data binding and without digit in its
  description has no value;
- a binding refers to no set or parameter.

## Application

- Operations are applied in order on copies; the input spec is never
  modified. The objective operation sets both direction and expression.
- sync_rules mirrors every constraint operation in the business rules,
  matched by name: a removal deletes the rule; an add or a replace
  writes a confirmed rule whose text is the patch summary and whose
  hardness is kept, or hard for a new rule.

## Files

- AgentEdit.py: AgentModelEditor, the context (edit_context), the LLM
  call (`ask`) and its correction loop (`propose`).
- patch.py: validation and application of a patch, and sync of the
  business rules; no LLM call.
