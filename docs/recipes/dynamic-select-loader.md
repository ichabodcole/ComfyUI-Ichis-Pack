# Recipe: Dynamic Select Inputs Backed by File Metadata

## Goal

Expose a file-backed list (e.g., tag categories) through a selectable UI that refreshes automatically whenever the source data changes.

## Ingredients

- **Loader node** that reads the file and emits structured metadata (list of categories, tags per category).
- **PromptServer broadcast** from the loader so the browser receives fresh metadata without reloading the graph.
- **Selector node + JS extension** that turns metadata into one or more combo widgets and echoes the chosen categories back to Python.
- **Consumer node** (sampler, processor, etc.) that accepts both the metadata payload and the finalized category list.

## Steps

1. **Implement Loader Node (Python)**

   - Add a hidden `unique_id` input so each node instance has a stable identifier.
   - Parse the file into a payload (categories, tags, resolved path) and cache it for reuse.
   - After each load, call `PromptServer.instance.send_sync("ichis-tag-loader", payload)` to broadcast the metadata; include `unique_id`, `resolved_path`, and `source_path` so selectors can match the event.

2. **Add Front-End Extension (JavaScript)**

   - Register an extension via `app.registerExtension` whose `beforeRegisterNodeDef` hooks `onNodeCreated`, `onConnectionsChange`, `onExecuted`, and `onConfigure`.
   - On node creation, hide the raw `STRING` input and inject one or more combo widgets (`node.addWidget("combo", ...)`). Keep a `Set` of selector nodes for quick refresh.
   - **Implement robust widget restoration:** Handle dynamic widget restoration with retry mechanisms and multiple lifecycle hooks to address timing issues where `widgets_values` may be undefined initially.
   - Listen for the loader event with `api.addEventListener("ichis-tag-loader", handler)`. When it fires, find connected selectors (matching by `unique_id`, node id, or file path) and update their widget options.
   - When the user changes a combo value, call a helper that writes both `widget.value` _and_ the corresponding entry in `node.widgets_values`, then synchronize the hidden string input (newline-joined categories).

3. **Normalize Selections in Python**

   - Parse the newline-separated string with a helper (no comma splitting) and map it against known metadata categories (`normalize_categories_selection`).
   - Provide sensible fallbacks (e.g., first category when empty) so downstream nodes never receive an empty list unless explicitly allowed.

4. **Consume the Selection**

   - Consumer nodes take `tag_metadata`, `tag_selection`, and/or a direct `category_list`. When metadata is missing they can still read from `file_path` for legacy compatibility.

5. **Implement Dynamic Widget Restoration**
   - **Detection:** Scan for widgets that match your naming pattern but aren't in your tracking collection during `onNodeCreated`.
   - **Timing Handling:** Check if `widgets_values` is available; if not, implement retry logic with `setTimeout` (up to 5 retries with 100ms delays).
   - **Additional Hooks:** Hook into `onConfigure` to catch restoration when `widgets_values` is properly populated.
   - **Missing Widget Recreation:** Analyze `widgets_values` array to count expected widgets and create any that ComfyUI failed to restore.
   - **Value Restoration:** Extract saved values from `widgets_values` at correct indices and assign to both existing and newly created widgets.
   - **Callback Restoration:** Ensure all widgets (existing and recreated) have proper callback functions and serialization methods.

## Testing Tips

- Add unit tests that cover loader caching, selector normalization, and the consumer node's handling of both metadata-driven and manual inputs.
- When debugging, keep a temporary text widget or console logging enabled in the JS extension to observe loader events and widget synchronization.
- **Test widget restoration thoroughly:** Save workflows with multiple dynamic widgets, refresh the page, and verify all widgets are restored with correct values and functionality.
- **Monitor timing issues:** Watch for `widgets_values` being undefined during initial restoration attempts and ensure retry mechanisms work properly.

## Variations

- Swap the loader for a database query or HTTP response—the pattern holds as long as the payload includes a unique id for matching.
- Replace combo widgets with text autocompletes or multi-select toggles; the key is still syncing `widgets_values` and broadcasting updates.

Keep this recipe handy whenever a future node needs to mirror back-end data in the ComfyUI front-end without forcing users to reload the graph.
