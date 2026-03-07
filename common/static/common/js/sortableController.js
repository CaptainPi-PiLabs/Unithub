function sortableController(config) {
    return {
        dragging: false,

        init() {
            const el = document.getElementById(config.listId);
            if (!el) return;

            const waitForSortable = () => {

                if (typeof Sortable === "undefined") {
                    setTimeout(waitForSortable, 50);
                    return;
                }

                Sortable.create(el, {
                    animation: 150,
                    handle: config.handle || ".drag-handle",

                    onStart: () => {
                        this.dragging = true;
                    },

                    onEnd: (evt) => {

                        this.dragging = false;

                        const pk = evt.item.dataset.id;
                        if (!pk) return;

                        const formData = new FormData();

                        formData.append("csrfmiddlewaretoken", this.csrfToken());
                        formData.append("action", config.actionName);
                        formData.append("pk", pk);
                        formData.append("position", evt.newIndex + 1);

                        fetch(config.postUrl || window.location.pathname, {
                            method: "POST",
                            body: formData
                        })
                        .then(res => {
                            if (!res.ok) {
                                console.error("Move failed");
                                location.reload();
                            }
                        })
                        .catch(() => {
                            location.reload();
                        });
                    }
                });
            };

            waitForSortable();
        },

        goToDetail(id) {
            if (this.dragging) return;

            window.location.href = config.detailUrl(id);
        },

        csrfToken() {
            return document.querySelector(
                "[name=csrfmiddlewaretoken]"
            )?.value;
        }
    };
}