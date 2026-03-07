function qualificationPage() {
    return {
        ...slidePanelBase(),
        ...tabBase('details'),

        criteria: JSON.parse(
            document.getElementById("criteria-data").textContent
        ),

        init() {
            document.addEventListener("trainer-user-selected", e => {
                this.selectTrainerUser(e.detail);
            });
        },
        openCriterion(id) {
            let criterionData;

            if (id === null) {
                criterionData = {
                    id: null,
                    name: '',
                    description: '',
                };
            } else {
                const criterion = this.criteria.find(c => c.id === id);
                if (!criterion) return;

                criterionData = JSON.parse(JSON.stringify(criterion));
            }

            this.openPanel('criteria', criterionData);
        },

        selectTrainerUser(user) {

            trainerData = {
                user_id: user.id,
                name: user.name,
                role: "Trainer"
            };
            this.openPanel('trainer_edit', trainerData)
        }
    }
}