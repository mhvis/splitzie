document.addEventListener('alpine:init', () => {

    // Store for the known groups in the browser
    const groupsKey = "groupStore";
    Alpine.store('groups', {
        init() {
            this.groups = JSON.parse(localStorage.getItem(groupsKey) || '{}');
        },
        groups: {},

        /**
         * Adds a group and stores it into LocalStorage.
         *
         * @param {string} code
         * @param {string} name
         */
        add: function(code, name) {
            this.groups[code] = {'name': name};
            localStorage.setItem(groupsKey, JSON.stringify(this.groups));
        },

        /**
         * Removes a group from the store and browser data.
         *
         * @param {string} code
         */
        remove: function(code) {
            delete this.groups[code];
            localStorage.setItem(groupsKey, JSON.stringify(this.groups));
        },
    });
});

