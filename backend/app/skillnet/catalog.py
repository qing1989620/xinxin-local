"""Minimal in-memory contract consumed by the upstream shared LinUCB algorithm."""


class SkillLibrary:
    def __init__(self, skills):
        self.skills = {skill.name: skill for skill in skills}

    def all(self):
        return list(self.skills.values())

    def get(self, name):
        return self.skills.get(name)

    def __iter__(self):
        return iter(self.all())

    def __len__(self):
        return len(self.skills)
