function qualificationPage(qualification_id) {
    return {
        search: "",
        members: JSON.parse(document.getElementById("active_members").textContent),
        selectedMembers: [],

        get filteredMembers() {
            if (this.search.length < 2) return [];

            return this.members.filter(m =>
                m.name.toLowerCase().includes(this.search.toLowerCase()) &&
                !this.selectedMembers.some(s => s.id === m.id)
            ).slice(0, 10);
        },

        addMember(member) {
            this.selectedMembers.push(member);
        },

        removeMember(memberId) {
            this.selectedMembers =
                this.selectedMembers.filter(m => m.id !== memberId);
        },

        certifyMembers() {
            if (!this.selectedMembers.length) {
                alert("No members selected");
                return;
            }

            document.getElementById("membersField").value =
                JSON.stringify(this.selectedMembers.map(m => m.id));
                document.getElementById("certifyForm").submit()
        },

        csrfToken() {
            return document.querySelector('meta[name="csrf-token"]')?.content
                || document.cookie.split('; ')
                    .find(row => row.startsWith('csrftoken='))
                    ?.split('=')[1];
        }
    }
}