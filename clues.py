"""Puzzle Clues class file."""


class Clue(dict):
    """Clue class."""

    # name - name of the clue
    # suffix - suffix of the clue name
    # label - label to enter in the grid
    # starred - starred clue
    # clue - clue text
    # answers - list of answers
    # entries - list of entries
    # solutions - list of solutions

    def __init__(self, clue, group):
        """Initialize clue."""
        if isinstance(clue, str):
            self.clue_group = group
            data = self._parse_clue_string(clue)
            super().__init__(data)
        else:
            super().__init__(clue)

    @classmethod
    def get_enumeration(cls, answer):
        """Return the enumeration for a clue answer."""
        num = 0
        output = ""
        for char in answer:
            # count alpha characters
            if char.isalpha():
                num += 1
            # replace spaces with commas
            elif char == " ":
                output += f"{num},"
                num = 0
            # keep other characters as they are
            else:
                output += f"{num}{char}"
                num = 0
        output += f"{num}"
        return output

    def _parse_clue_string(self, clue):
        """Parse the clue string."""
        # parse clue name, label and suffix
        name = clue.split(". ")[0]

        # parse the star
        starred = False
        if name.startswith("*"):
            name = name[1:]
            starred = True

        # parse the label
        label = None
        label_index = 0
        if ";" in name:
            name, label = name.split(";", 1)
        if label and ";" in label:
            label, label_index = label.split(";", 1)
            label_index = int(label_index) if label_index else 0

        # parse the suffix
        suffix = None
        if "|" in name:
            name, suffix = name.split("|", 1)

        # parse clue, answers and solutions
        clue_text = clue.split(". ", 1)[1]
        # parse clue, answers and solutions
        clue_text = clue.split(". ", 1)[1]
        parts = clue_text.split(" ~ ")
        clue = parts[0]
        ans = parts[1] if len(parts) > 1 else ""
        sol = parts[2] if len(parts) > 2 else ans

        # parse the answers
        answers = ans.split("|")[0].split(";")

        # parse the entries
        entries = []
        if "|" in ans:
            entries = ans.split("|")[1].split(";")

        # parse the solutions
        solutions = sol.split(";")

        # get the enumerations
        enumerations = []
        show_enumerations = self.clue_group["settings"].get("show_enumerations", "none")
        if show_enumerations == "entries" and entries:
            enumerations = [self.get_enumeration(entry) for entry in entries]
        elif show_enumerations != "none":
            enumerations = [self.get_enumeration(answer) for answer in answers]

        return {
            "name": name,
            "suffix": suffix,
            "label": label,
            "label_index": label_index,
            "starred": starred,
            "clue": clue.strip(),
            "answers": answers,
            "entries": entries,
            "solutions": solutions,
            "enumerations": enumerations,
        }

    def label(self):
        """Return the label for this clue."""
        return self.get("label") or self.get("name")


class Clues(list):
    """Clues class."""

    def __init__(self, clues, group):
        """Initialize clues."""
        super().__init__()
        for clue in clues:
            self.append(Clue(clue, group))


class ClueGroupSettings(dict):
    """Clue group settings class."""

    def __init__(self, settings):
        """Initialize clue group settings."""
        super().__init__(settings)


class ClueGroup(dict):
    """Clue group class."""

    def __init__(self, clue_group):
        """Initialize clue group."""
        super().__init__()
        self["settings"] = ClueGroupSettings(clue_group.get("settings", {}))
        self["name"] = clue_group.get("name")
        self["clues"] = Clues(clue_group.get("clues", []), self)


class ClueGroups(list):
    """Clue groups class."""

    def __init__(self, clue_groups):
        """Initialize clue groups."""
        super().__init__()
        for clue_group in clue_groups:
            self.append(ClueGroup(clue_group))

    def entries(self):
        """Return a dict of entries for this puzzle."""
        data = {}
        for clue_group in self:
            settings = clue_group.get("settings", {})
            # skip entries if the clue group disables them
            if not settings.get("show_grid_entries", True):
                continue
            # if not settings.get("show_grid_labels", True):
            #     continue
            for clue in clue_group.get("clues", []):
                clue_answers = clue.get("answers", [])
                clue_entries = clue.get("entries", [])
                for entry in clue_entries or clue_answers:
                    entry = entry.strip().replace(" ", "")
                    if entry not in data:
                        data[entry] = []
                    data[entry].append(clue)
        return data

    def to_firestore(self):
        """Convert clue groups to firestore data."""
        output = []
        for clue_group in self:
            clues = []
            for clue in clue_group["clues"]:
                # parse the name, suffix and lab
                text = clue["name"]
                if clue["suffix"]:
                    text += f"|{clue['suffix']}"
                if clue["label"]:
                    text += f";{clue['label']}"
                    if clue["label_index"]:
                        text += f";{clue['label_index']}"

                # parse the clue
                text += f". {clue['clue']}"

                # parse the answers
                ans = ";".join(clue["answers"])
                text += f" ~ {ans}"

                # parse the entries
                ent = ";".join(clue["entries"])
                if ent:
                    text += f"|{ent}"

                # parse the solutions
                sol = ";".join(clue["solutions"])
                text += f" ~ {sol}"

                clues.append(text)

            clue_group["clues"] = clues
            output.append(clue_group)
        return output
