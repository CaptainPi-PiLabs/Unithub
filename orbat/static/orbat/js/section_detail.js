function sectionPage(sectionId) {
    return {
        ...slidePanelBase(),

        sectionId: sectionId,
        activeTab: 'details',

        slotData: JSON.parse(document.getElementById("slots_json").textContent),

        openSlot(slotId = null) {
            if (slotId && this.slotData[slotId]) {
                slot_data = {...this.slotData[slotId]};
            } else {
                slot_data = {name: '', colour: '', is_officer: false};
            }
            this.openPanel("edit_slot", slot_data)
        },

        submitSlot() {

        }
    }
}