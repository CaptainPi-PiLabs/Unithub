function userSearch(options = {}) {
    return {
        endpoint: options.endpoint || "/api/users/search/",
        multiple: options.multiple ?? true,
        minLength: options.minLength ?? 2,

        search: "",
        results: [],
        selected: [],

        init() {
            if (options.initialSelected) {
                this.selected = options.multiple
                    ? options.initialSelected
                    : [options.initialSelected];
            }
        },

        async performSearch() {
            if (this.search.length < this.minLength) {
                this.results = [];
                return;
            }

            const params = new URLSearchParams({
                q: this.search
            });

            const res = await fetch(`${this.endpoint}?${params}`);
            const data = await res.json();

            this.results = data.results;
        },

        selectUser(user) {
            if (this.multiple) {
                if (!this.selected.some(u => u.id === user.id)) {
                    this.selected.push(user);
                }
            } else {
                this.selected = [user];
                this.results = [];
                this.search = user.name;
            }
        },

        removeUser(id) {
            this.selected = this.selected.filter(u => u.id !== id);
        },

        get selectedIds() {
            return this.selected.map(u => u.id);
        }
    };
}