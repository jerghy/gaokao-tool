/**
 * Simple state store with subscription support
 * @class Store
 */
class Store {
    /**
     * Create a new store
     * @param {Object} initialState - Initial state object
     */
    constructor(initialState) {
        /** @type {Object} Current state */
        this.state = initialState;
        /** @type {Array<Function>} State change listeners */
        this.listeners = [];
    }

    /**
     * Get current state
     * @returns {Object} Current state
     */
    getState() {
        return this.state;
    }

    /**
     * Update state and notify listeners
     * @param {Object} newState - Partial state to merge
     */
    setState(newState) {
        this.state = { ...this.state, ...newState };
        this.notify();
    }

    /**
     * Subscribe to state changes
     * @param {Function} listener - Callback function receiving new state
     * @returns {Function} Unsubscribe function
     */
    subscribe(listener) {
        this.listeners.push(listener);
        return () => {
            this.listeners = this.listeners.filter(l => l !== listener);
        };
    }

    /**
     * Notify all listeners of state change
     */
    notify() {
        this.listeners.forEach(listener => listener(this.state));
    }

    /**
     * Reset store to initial state
     * @param {Object} [initialState] - New initial state
     */
    reset(initialState) {
        this.state = initialState || {};
        this.notify();
    }
}

/**
 * State management utilities
 * @namespace StateManager
 */
const StateManager = {
    /** @type {Object<string, Store>} Registered stores */
    stores: {},

    /**
     * Create or get a named store
     * @param {string} name - Store name
     * @param {Object} initialState - Initial state object
     * @returns {Store} Store instance
     */
    createStore(name, initialState) {
        if (this.stores[name]) {
            return this.stores[name];
        }
        const store = new Store(initialState);
        this.stores[name] = store;
        return store;
    },

    /**
     * Get a named store
     * @param {string} name - Store name
     * @returns {Store|undefined} Store instance or undefined
     */
    getStore(name) {
        return this.stores[name];
    }
};
