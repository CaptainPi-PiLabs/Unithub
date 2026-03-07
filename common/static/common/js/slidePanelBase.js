function slidePanelBase() {
    return {
        panelOpen: false,
        panelMode: null,
        formData: {},

        openPanel(mode, data = {}) {
            this.panelMode = mode;
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