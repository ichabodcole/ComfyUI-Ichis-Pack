import { api } from "../../../scripts/api.js";
import { app } from "../../../scripts/app.js";

const LiteGraphGlobal = globalThis?.LiteGraph;
const DEBUG_PREFIX = "[ICHIS_Tag_Category_Select]";
const EXTENSION_NAME = "ichis.tag_category_select";
const NODE_NAME = "ICHIS_Tag_Category_Select";
const INPUT_SLOT = 0; // tag_metadata
const LOADER_EVENT = "ichis-tag-loader";

function logDebug(...args) {
    console.log(DEBUG_PREFIX, ...args);
}

const loaderCategoryCache = new Map();
const selectorNodes = new Set();

function getUniqueIdFromNode(node) {
    if (!node) return null;
    if (node.widgets) {
        const widget = node.widgets.find((w) => w.name === "unique_id" || w.name === "unique id");
        if (widget?.value) {
            return widget.value;
        }
    }
    if (Array.isArray(node.widgets_values) && Array.isArray(node.widgets)) {
        const index = node.widgets.findIndex((w) => w.name === "unique_id" || w.name === "unique id");
        if (index >= 0) {
            return node.widgets_values[index];
        }
    }
    if (node.extra?.unique_id) {
        return node.extra.unique_id;
    }
    if (node.properties?.unique_id) {
        return node.properties.unique_id;
    }
    return node.unique_id || null;
}

function getFilePathFromLoader(node) {
    if (!node) return null;
    if (node.widgets) {
        const fileWidget = node.widgets.find((w) => w.name === "file_path" || w.name === "file path");
        if (fileWidget?.value) {
            return fileWidget.value;
        }
    }
    if (Array.isArray(node.widgets) && Array.isArray(node.widgets_values)) {
        const idx = node.widgets.findIndex((w) => w.name === "file_path" || w.name === "file path");
        if (idx >= 0) {
            return node.widgets_values[idx];
        }
    }
    return null;
}

function ensureCollections(node) {
    if (!node.ichisCategoryWidgets) {
        node.ichisCategoryWidgets = [];
    }
    if (!node.ichisAvailableCategories) {
        node.ichisAvailableCategories = [];
    }
}

function hideBaseCategoriesWidget(node) {
    const widget = node.widgets?.find((w) => w.name === "categories");
    if (!widget) return;
    widget.hidden = true;
    widget.computeSize = () => [0, 0];
    node.ichisHiddenCategoriesWidget = widget;
}

function syncHiddenWidget(node) {
    if (!node.ichisHiddenCategoriesWidget) return;
    const values = node.ichisCategoryWidgets
        .map((w) => (typeof w.value === "string" ? w.value.trim() : ""))
        .filter((v) => v.length > 0);
    node.ichisHiddenCategoriesWidget.value = values.join("\n");
    const idx = node.widgets?.indexOf?.(node.ichisHiddenCategoriesWidget) ?? -1;
    if (idx >= 0 && Array.isArray(node.widgets_values)) {
        node.widgets_values[idx] = node.ichisHiddenCategoriesWidget.value;
    }
    node.extras = node.extras || {};
    node.extras.ichisCategoryList = values;
    node.widgets_changed = true;

    logDebug("syncHiddenWidget", {
        node: node?.id,
        values,
        widgets_values: node.widgets_values,
    });

    if (node.ichisDebugLabel) {
        node.ichisDebugLabel.value = values.length
            ? `${values.length} categories selected`
            : "no categories selected";
    }
}

function addCategoryWidget(node, value = "") {
    ensureCollections(node);
    const widget = node.addWidget(
        "combo",
        "select category",
        value,
        () => syncHiddenWidget(node),
        {
            values: node.ichisAvailableCategories.length
                ? [""].concat(node.ichisAvailableCategories)
                : [""],
        },
    );
    widget.serializeValue = function serializeValue() {
        return this.value ?? "";
    };
    node.ichisCategoryWidgets.push(widget);
    const idx = node.widgets?.indexOf?.(widget) ?? -1;
    if (idx >= 0 && Array.isArray(node.widgets_values)) {
        node.widgets_values[idx] = widget.value ?? "";
    }
    syncHiddenWidget(node);
    return widget;
}

function updateWidgetOptions(node) {
    ensureCollections(node);
    for (const widget of node.ichisCategoryWidgets) {
        if (!widget?.options) continue;
        widget.options.values = node.ichisAvailableCategories.length
            ? [""].concat(node.ichisAvailableCategories)
            : [""];
        if (widget.value && !node.ichisAvailableCategories.includes(widget.value)) {
            widget.value = "";
        }
    }
    syncHiddenWidget(node);
}

function applyAvailableCategories(node, categories, source = "") {
    ensureCollections(node);
    if (Array.isArray(categories)) {
        node.ichisAvailableCategories = categories.slice();
    }
    updateWidgetOptions(node);
    if (node.ichisDebugLabel) {
        node.ichisDebugLabel.value = node.ichisAvailableCategories.length
            ? `${node.ichisAvailableCategories.length} categories ${source}`
            : `no categories ${source}`;
    }
    node.graph?.setDirtyCanvas(true);
}

function extractCategoriesFromMetadata(node) {
    const categories = new Set();
    const input = node.inputs?.[INPUT_SLOT];
    if (input?.link != null) {
        const link = node.graph?.links?.[input.link];
        if (link) {
            const originNode = node.graph?.getNodeById?.(link.origin_id);
            if (originNode) {
                const loaderId = getUniqueIdFromNode(originNode);
                if (loaderId && loaderCategoryCache.has(loaderId)) {
                    loaderCategoryCache.get(loaderId).categories.forEach((cat) => categories.add(cat));
                }
                const outputSlot = originNode.outputs?.[link.origin_slot];
                const payload = outputSlot?.last_data?.[0];
                if (payload?.categories && Array.isArray(payload.categories)) {
                    payload.categories.forEach((cat) => categories.add(cat));
                }
            }
        }
    }
    const categoriesList = Array.from(categories);
    logDebug("extract categories", node?.id, categoriesList);
    applyAvailableCategories(node, categoriesList, "(extract)");
}

function restoreCategoryWidgets(node, retryCount = 0) {
    ensureCollections(node);
    
    // Check if widgets_values is available yet
    if (!Array.isArray(node.widgets_values) && retryCount < 5) {
        logDebug("widgets_values not ready, retrying in 100ms", { retryCount, widgets_values: node.widgets_values });
        setTimeout(() => restoreCategoryWidgets(node, retryCount + 1), 100);
        return;
    }
    
    // Check if we're restoring from saved state by looking for category widgets
    // that match our naming pattern but aren't in our tracked collection
    const categoryWidgets = node.widgets?.filter(w => 
        w.name === "select category" && !node.ichisCategoryWidgets.includes(w)
    ) || [];
    
    logDebug("restoreCategoryWidgets: categoryWidgets", { widgets: node.widgets, ichiWidgets: node.ichisCategoryWidgets, categoryWidgets });

    // Count expected category widgets from widgets_values
    // Look for non-empty string values that could be category selections
    let expectedCategoryCount = 0;
    if (Array.isArray(node.widgets_values)) {
        // Skip the first few known widgets (categories, allow_empty, debug, status, button)
        // and count non-empty string values that look like category selections
        for (let i = 5; i < node.widgets_values.length; i++) {
            const value = node.widgets_values[i];
            if (typeof value === "string" && value.trim() !== "") {
                expectedCategoryCount++;
            }
        }
    }
    
    logDebug("restoration analysis", {
        existingCategoryWidgets: categoryWidgets.length,
        trackedCategoryWidgets: node.ichisCategoryWidgets.length,
        expectedCategoryCount,
        widgets_values: node.widgets_values,
        retryCount
    });

    // If we have category widgets that aren't tracked, this is a restoration
    if (categoryWidgets.length > 0) {
        logDebug("restoring category widgets", node.id, categoryWidgets.length);
        
        // Add existing widgets to our tracking collection and restore their values
        for (const widget of categoryWidgets) {
            // Find the widget's index to get its value from widgets_values
            const widgetIndex = node.widgets.indexOf(widget);
            if (widgetIndex >= 0 && Array.isArray(node.widgets_values) && widgetIndex < node.widgets_values.length) {
                const savedValue = node.widgets_values[widgetIndex];
                if (savedValue && savedValue !== "") {
                    widget.value = savedValue;
                    logDebug("restored widget value", widgetIndex, savedValue);
                }
            }
            
            // Ensure the widget has the proper callback
            widget.callback = () => syncHiddenWidget(node);
            widget.serializeValue = function serializeValue() {
                return this.value ?? "";
            };
            node.ichisCategoryWidgets.push(widget);
        }
    }
    
    // Check if we need to create missing category widgets
    const totalExistingWidgets = node.ichisCategoryWidgets.length;
    if (expectedCategoryCount > totalExistingWidgets) {
        logDebug("creating missing category widgets", {
            expected: expectedCategoryCount,
            existing: totalExistingWidgets,
            missing: expectedCategoryCount - totalExistingWidgets
        });
        
        // Create missing widgets and restore their values
        for (let i = totalExistingWidgets; i < expectedCategoryCount; i++) {
            const valueIndex = 5 + i; // Start from index 5 in widgets_values
            const savedValue = (Array.isArray(node.widgets_values) && valueIndex < node.widgets_values.length) 
                ? node.widgets_values[valueIndex] 
                : "";
            
            logDebug("creating missing widget", { index: i, valueIndex, savedValue });
            addCategoryWidget(node, savedValue || "");
        }
    } else if (totalExistingWidgets === 0) {
        // No widgets at all, create the first one
        addCategoryWidget(node, "");
    }
    
    // Sync the hidden widget with current values
    syncHiddenWidget(node);
}

function addControls(node) {
    hideBaseCategoriesWidget(node);
    ensureCollections(node);

    if (!node.ichisDebugLabel) {
        const noop = () => node.ichisDebugLabel?.value;
        node.ichisDebugLabel = node.addWidget("text", "ichis status", "init", noop, {
            multiline: false,
        });
        node.ichisDebugLabel.serializeValue = () => undefined;
    }
    if (!node.ichisAddButton) {
        node.ichisAddButton = node.addWidget("button", "+ category", null, () => {
            logDebug("+ category button clicked", node.id);
            addCategoryWidget(node, "");
            node.setSize?.(node.size);
        });
        node.ichisAddButton.serializeValue = () => null;
        node.ichisAddButton.removed = true;
    }
    // Restore category widgets from saved state
    restoreCategoryWidgets(node);

    extractCategoriesFromMetadata(node);
}

function refreshSelectorsForLoader(uniqueId) {
    if (!uniqueId) return;
    const payload = loaderCategoryCache.get(uniqueId);
    if (!payload) return;
    for (const node of selectorNodes) {
        if (!node || node.type !== NODE_NAME) continue;
        const input = node.inputs?.[INPUT_SLOT];
        if (!input?.link) continue;
        const link = node.graph?.links?.[input.link];
        if (!link) continue;
        const originNode = node.graph?.getNodeById?.(link.origin_id);
        if (!originNode) continue;
        const loaderId = getUniqueIdFromNode(originNode);
        const loaderFile = getFilePathFromLoader(originNode);
        const slotName = originNode.outputs?.[link.origin_slot]?.name;
        const matchesSocket = slotName === "metadata";

        logDebug("refresh candidates", {
            selector: node?.id,
            loaderNode: originNode?.id,
            loaderUnique: loaderId,
            eventUnique: uniqueId,
            matchesSocket,
            loaderFile,
            eventSource: payload.source_path,
            eventResolved: payload.resolved_path,
        });
        const uniqueMatch = loaderId && String(loaderId) === String(uniqueId);
        const nodeIdMatch = String(originNode.id) === String(uniqueId);
        const pathMatch = loaderFile && (loaderFile === payload.source_path || loaderFile === payload.resolved_path);
        if (matchesSocket && (uniqueMatch || nodeIdMatch || pathMatch)) {
            logDebug("refresh selector from event", node.id, payload.categories);
            applyAvailableCategories(node, payload.categories, "(event)");
            // Note: Removed auto-population of empty widgets with first category
            // This allows users to intentionally set empty values without them being overridden
            syncHiddenWidget(node);
        }
    }
}

function handleLoaderEvent(event) {
    const detail = event?.detail || event;
    if (!detail) return;
    const uniqueId = detail.unique_id || detail.id;
    if (!uniqueId) return;
    loaderCategoryCache.set(uniqueId, detail);
    logDebug("loader event", uniqueId, detail);
    refreshSelectorsForLoader(uniqueId);
}

logDebug("extension evaluating");

api?.addEventListener?.(LOADER_EVENT, handleLoaderEvent);

app.registerExtension({
    name: EXTENSION_NAME,
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData?.name !== NODE_NAME) return;
        logDebug("registering extension for node", NODE_NAME);
        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function onNodeCreatedWrapper() {
            const result = onNodeCreated?.apply(this, arguments);
            logDebug("node created", this?.id);
            addControls(this);
            selectorNodes.add(this);
            return result;
        };

        const onRemoved = nodeType.prototype.onRemoved;
        nodeType.prototype.onRemoved = function onRemovedWrapper() {
            selectorNodes.delete(this);
            return onRemoved?.apply(this, arguments);
        };

        const onConnectionsChange = nodeType.prototype.onConnectionsChange;
        nodeType.prototype.onConnectionsChange = function connectionsWrapper(
            slotType,
            slotIndex,
            isConnected,
            _linkInfo,
            _nodeSlot,
        ) {
            const result = onConnectionsChange?.apply(this, arguments);
            const isInput = LiteGraphGlobal?.INPUT ?? 1;
            if (slotType === isInput && slotIndex === INPUT_SLOT) {
                logDebug("connections changed", {
                    node: this?.id,
                    slotType,
                    slotIndex,
                    isConnected,
                });
                extractCategoriesFromMetadata(this);
            }
            return result;
        };

        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function executedWrapper(output) {
            const result = onExecuted?.apply(this, arguments);
            logDebug("node executed", this?.id, output);
            extractCategoriesFromMetadata(this);
            return result;
        };

        // Hook into onConfigure to catch node restoration
        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function configureWrapper(info) {
            const result = onConfigure?.apply(this, arguments);
            logDebug("node configured", this?.id, { info, widgets_values: this.widgets_values });
            
            // Try restoration again after configuration
            if (Array.isArray(this.widgets_values) && this.widgets_values.length > 5) {
                logDebug("attempting restoration after configure");
                restoreCategoryWidgets(this);
            }
            
            return result;
        };
    },
});
