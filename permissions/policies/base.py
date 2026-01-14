class PermissionPolicy:
    module: str | None = None
    actions: set | None = None

    def applies(self, user, rule, scope):
        """
        Return:
        - True  -> explicitly allow
        - False -> explicitly deny
        - None  -> not applicable
        """

        if self.module is not None and rule.module != self.module:
            return None

        if self.actions is not None and rule.action not in self.actions:
            return None

        return self.check(user, scope)

    def check(self, user, scope):
        return None