function tabBase(defaultTab = 'details') {
    return {
        activeTab: defaultTab,

        setTab(tab) {
            this.activeTab = tab;

            const url = new URL(window.location);
            url.searchParams.set("tab", tab);
            window.history.replaceState({}, "", url);
        },

        tabClass(tab) {
            return this.activeTab === tab
                ? 'border-b-2 border-blue-500 font-bold'
                : 'text-gray-500';
        },

        isTab(tab) {
            return this.activeTab === tab;
        }
    }
}