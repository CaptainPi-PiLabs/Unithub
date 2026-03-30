function onboardingPage() {
    return {
        ...slidePanelBase(),

        application: JSON.parse(document.getElementById("applicationData").textContent),

        getDefaultSlideData() {
            return this.application;
        }
    }
}