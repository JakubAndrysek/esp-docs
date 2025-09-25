from __future__ import annotations

from docutils import nodes


class WokwiNode(nodes.General, nodes.Element):
    """Represents a single Wokwi iframe embed (and its frame UI)."""

    pass


class WokwiTabsNode(nodes.General, nodes.Element):
    """Root container for tabs (holds TabList + TabPanels)."""

    pass


class TabListNode(nodes.General, nodes.Element):
    """Clickable tab headers area."""

    pass


class TabPanelNode(nodes.General, nodes.Element):
    """Single tab panel wrapping arbitrary children."""

    pass
