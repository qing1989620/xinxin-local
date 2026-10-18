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

    def neighbours(self, name, rel_types=("compose_with", "depend_on")):
        """无向邻接：出边与入边都算，返回 (关系, 技能名)。

        与上游 Retriever 相同：只返回已经存在于库中的目标，避免关系图
        把演化中淘汰的技能重新带进候选池。
        """
        present = set(self.skills)
        out = []
        node = self.skills.get(name)
        if node:
            for rel, target in node.relations:
                if rel in rel_types and target in present:
                    out.append((rel, target))
        for other in self.skills.values():
            for rel, target in other.relations:
                if target == name and rel in rel_types:
                    out.append((rel, other.name))
        return out
