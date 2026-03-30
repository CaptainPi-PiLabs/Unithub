function slidePanelBase() {
    return {
        panelOpen: false,
        panelMode: null,
        formData: {},

        getDefaultSlideData() {
            return {};
        },

        openPanel(mode, data = {}) {
            this.panelMode = mode;
            if (!data) {
                data = this.getDefaultSlideData();
            }
            this.formData = JSON.parse(JSON.stringify(data));
            this.panelOpen = true;
        },

        closePanel() {
            this.panelOpen = false;
            this.panelMode = null;
            this.formData = {};
        },

        isPanel(mode) {
            return this.panelMode === mode;
        }
    }
}