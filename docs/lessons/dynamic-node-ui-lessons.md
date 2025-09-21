# Lessons Learned — Dynamic ComfyUI Node UIs

## Context

Building the tag sampler workflow exposed several gaps in our understanding of how ComfyUI nodes interact with the front-end. This guide captures hard‑earned lessons so future dynamic nodes (e.g., loaders that populate selects, widgets that react to upstream data) start from the working patterns instead of dead ends.

## What _Doesn't_ Work

- **Trying to mutate `INPUT_TYPES` at runtime.** The Python side is evaluated once. Returning a different list of values for the same widget _after_ the graph is loaded will not refresh existing node instances.
- **Expecting ComfyUI to auto-refresh widgets when upstream data changes.** Outputs such as lists or dicts do not magically populate combo boxes; without a JS extension the UI stays static.
- **Relying on `last_data` for dynamic updates.** Nodes may cache outputs, but other nodes won't see changes in the front-end unless the widget values are explicitly updated in JavaScript.
- **Assuming the hidden `widgets_values` array updates itself.** Editing widget objects (`widget.value`) is not enough; you must also sync the corresponding entry in `node.widgets_values` or the back-end continues to see the old string.
- **Broadcasting data without a stable identifier.** Loader and selector nodes need a shared key (unique id, resolved path) to recognize each other. If you only send anonymous payloads, the UI cannot tell which selector should update.
- **Expecting ComfyUI to restore dynamically added widgets.** ComfyUI's serialization/deserialization only handles the initial widget set. Dynamically added widgets may be partially restored or missing entirely after page refresh.
- **Assuming `widgets_values` is available during `onNodeCreated`.** Widget values may be undefined initially and populated later in the lifecycle, causing restoration logic to fail if not properly timed.

## What _Does_ Work

- **Pair each dynamic node with a front-end extension.** Register an extension via `app.registerExtension` and hook into lifecycle events (`onNodeCreated`, `onConnectionsChange`, `onExecuted`) to inject widgets, update state, and trigger redraws.
- **Use PromptServer (or API routes) for backend→frontend messaging.** When the Python node finishes work, broadcast via `PromptServer.instance.send_sync("custom-event", payload)` so the JS listener can refresh options immediately.
- **Cache node references when you create them.** Keep a `Set` of active selector nodes on the JS side. When a loader event fires, iterate only those instances and apply the new data.
- **Always normalize selections on the Python side.** Even with JS keeping widgets in sync, run selections through utility helpers (`parse_categories_string`, `normalize_categories_selection`) so whitespace, case handling, and fallback behavior stay consistent.
- **Adopt one clear input format.** Expect newline-separated category names (or another unambiguous delimiter) to avoid double-parsing strings that contain commas or other punctuation.
- **Provide resilient defaults.** When no category is chosen, default to the first available _single_ category (not “all”) so downstream nodes don't explode.
- **Keep debug hooks until the workflow stabilizes.** Temporary status widgets and console logs save time when verifying the link between loader events and selector updates; remove them _after_ the flow is battle-tested.
- **Implement robust widget restoration for dynamic widgets.** Use multiple lifecycle hooks (`onNodeCreated`, `onConfigure`) with retry mechanisms to handle timing issues. Analyze `widgets_values` array to detect and recreate missing dynamically added widgets.
- **Handle restoration timing carefully.** Widget values may not be available immediately. Implement retry logic with `setTimeout` and hook into `onConfigure` to catch restoration at the proper time when `widgets_values` is populated.

## Recommended Implementation Pattern

1. **Python node emits metadata** with a unique identifier (hidden `UNIQUE_ID` input is fine) and broadcasts the payload via PromptServer.
2. **JavaScript extension listens** for that event, caches the payload, and updates connected selector nodes (adding/removing combo widgets, refreshing options, syncing `widgets_values`).
3. **Selectors publish normalized selections** back to Python, ideally as simple newline-separated strings plus a payload dict for downstream nodes.
4. **Consumers (samplers, processors)** accept either the structured payload or the simple list, keeping legacy fallbacks only where absolutely necessary.

## Checklist For Future Dynamic Nodes

- [ ] Hidden `unique_id` added to any node that needs to broadcast updates.
- [ ] PromptServer route/broadcast implemented with a descriptive event name.
- [ ] Front-end extension registered, syncing widget values _and_ `widgets_values`.
- [ ] Parsing helpers accept newline-separated strings; avoid commas as structural delimiters.
- [ ] Debug mode prints include input/output signatures to ease troubleshooting.
- [ ] Unit tests cover both manual selections and default fallback behavior.
- [ ] Widget restoration logic implemented with retry mechanism for timing issues.
- [ ] Multiple lifecycle hooks (`onNodeCreated`, `onConfigure`) to catch restoration properly.
- [ ] Dynamic widget detection and recreation based on `widgets_values` array analysis.
- [ ] Proper callback and serialization function restoration for recreated widgets.

Refer back to this sheet before building the next dynamic loader/selector pair to avoid playing whack-a-mole with ComfyUI’s UI lifecycle again.
