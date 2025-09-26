from __future__ import annotations

from typing import Optional
from docutils import nodes as _n

from .helpers import _escape, iframe_url
from .nodes import WokwiNode, WokwiTabsNode, TabListNode, TabPanelNode


def _render_iframe_attrs(node: WokwiNode) -> tuple[str, str, str]:
    iframe_page = node.get("iframe_page")
    iframe_page_params = node.get("iframe_page_params", {})
    diagram_path = node.get("diagram")
    firmware_path = node.get("firmware")
    width = node.get("width")
    height = node.get("height")
    loading = node.get("loading", "lazy")
    classes = " ".join(node.get("classes", []))
    viewer_url = iframe_url(iframe_page, diagram_path, firmware_path, iframe_page_params)

    attrs = {
        "src": viewer_url,
        "width": _escape(str(width), quote=True),
        "height": _escape(str(height), quote=True),
        "loading": _escape(str(loading), quote=True),
        "class": _escape(classes, quote=True),
        "frameborder": "0",
    }
    attr_str = " ".join(f'{k}="{v}"' for k, v in attrs.items() if v)
    allow = " allowfullscreen" if bool(node.get("allowfullscreen")) else ""
    return attr_str, allow, viewer_url


# --- Single Wokwi (keep header with info + fullscreen only) ---

def visit_wokwi_html(self, node: WokwiNode):
    attr_str, allow, _ = _render_iframe_attrs(node)
    iframe = f"<iframe {attr_str}{allow}></iframe>"

    if node.get("suppress_header"):
        self.body.append(iframe)
        raise _n.SkipNode

    about_wokwi_url = getattr(self.builder.app.config, "about_wokwi_url", None)
    attr_str, allow, _ = _render_iframe_attrs(node)

    self.body.append('<div class="wokwi-frame">')
    self.body.append('<div class="wokwi-tabsbar"><div class="wokwi-actions">')
    if about_wokwi_url:
        self.body.append(
            f'<a class="wokwi-info-btn" href="{_escape(about_wokwi_url, True)}" target="_blank" rel="noopener" title="About Wokwi">ⓘ</a>'
        )
    self.body.append('<a class="wokwi-fullscreen-btn" href="#" title="Fullscreen simulation">⛶</a>')
    self.body.append('</div></div>')
    self.body.append(f"<iframe {attr_str}{allow}></iframe>")
    self.body.append("</div>")
    raise _n.SkipNode


def depart_wokwi_html(self, node: WokwiNode):
    pass


# --- Tabs container ---

def visit_wokwi_tabs_html(self, node: WokwiTabsNode):
    classes = "wokwi-tabs" + (" " + " ".join(node.get("classes", [])) if node.get("classes") else "")
    data_variant = f' data-variant="{_escape(node.get("variant"), True)}"' if node.get("variant") else ""
    self.body.append(f'<div class="{classes}"{data_variant}>')


def depart_wokwi_tabs_html(self, node: WokwiTabsNode):
    self.body.append("</div>")


def visit_tablist_html(self, node: TabListNode):
    labels = node.get("labels", [])
    panel_ids = node.get("panel_ids", [])
    tabs_code = node.get("tabs_code", [])
    tabs_wokwi = node.get("tabs_wokwi", [])
    about_wokwi_url = getattr(self.builder.app.config, "about_wokwi_url", None)
    launchpad_href = node.get("launchpad_href")
    launchpad_icon = node.get("launchpad_icon")


    self.body.append('<div class="wokwi-tabsbar">')
    self.body.append('<div class="wokwi-chip-tabs-container wokwi-chip-tabs-single-frame">')
    self.body.append('<div class="wokwi-tab-groups-row">')
    # Render code tabs first
    if tabs_code:
        self.body.append('<div class="wokwi-tab-group">')
        self.body.append('<div class="wokwi-tab-group-label">Code</div>')
        self.body.append('<div class="wokwi-tablist wokwi-code-tablist" data-wokwi="tablist">')
        for i, label in enumerate(tabs_code):
            panel_index = labels.index(label)
            pid = panel_ids[panel_index]
            selected = "true" if i == 0 else "false"
            self.body.append(
                f'<button class="wokwi-tab wokwi-code-tab" type="button" role="tab" '
                f'aria-selected="{selected}" data-target="{pid}">{_escape(label, True)}</button>'
            )
        self.body.append("</div>")  # code tablist
        self.body.append("</div>")  # tab group
    # Render wokwi tabs
    if tabs_wokwi:
        self.body.append('<div class="wokwi-tab-group">')
        self.body.append('<div class="wokwi-tab-group-label">Wokwi</div>')
        self.body.append('<div class="wokwi-tablist wokwi-wokwi-tablist" data-wokwi="tablist">')
        for i, label in enumerate(tabs_wokwi):
            panel_index = labels.index(label)
            pid = panel_ids[panel_index]
            selected = "true" if i == 0 and not tabs_code else "false"
            self.body.append(
                f'<button class="wokwi-tab wokwi-wokwi-tab" type="button" role="tab" '
                f'aria-selected="{selected}" data-target="{pid}">{_escape(label, True)}</button>'
            )
        self.body.append("</div>")  # wokwi tablist
        self.body.append("</div>")  # tab group
    self.body.append('</div>')  # wokwi-tab-groups-row
    self.body.append("</div>")  # wokwi-chip-tabs-container

    # Actions (right)
    self.body.append('<div class="wokwi-actions" data-wokwi-only="true">')
    if about_wokwi_url:
        self.body.append(
            f'<a class="wokwi-info-btn" href="{_escape(about_wokwi_url, True)}" target="_blank" rel="noopener" title="About Wokwi">ⓘ</a>'
        )
    self.body.append('<a class="wokwi-fullscreen-btn" href="#" title="Fullscreen simulation">⛶</a>')

    # Launchpad button (always show if icon exists)
    if launchpad_icon:
        base_href = launchpad_href or "https://espressif.github.io/esp-launchpad/"
        self.body.append(
            f'<a class="wokwi-launchpad-btn" href="{_escape(base_href, True)}" '
            f'data-base-href="{_escape(base_href, True)}" '
            f'target="_blank" rel="noopener" title="Open in ESP Launchpad">'
            f'<img src="{_escape(launchpad_icon, True)}" alt="ESP Launchpad"/></a>'
        )

    self.body.append("</div>")  # actions
    self.body.append("</div>")  # tabsbar
    raise _n.SkipNode


def depart_tablist_html(self, node: TabListNode):
    pass


def visit_tabpanel_html(self, node: TabPanelNode):
    pid = node.get("panel_id")
    active = "true" if node.get("active") else "false"

    viewer_url: Optional[str] = None
    for ch in node.children:
        if isinstance(ch, WokwiNode):
            _attr, _allow, url = _render_iframe_attrs(ch)
            viewer_url = url
            break

    data_attr = f' data-viewer-url="{_escape(viewer_url, True)}"' if viewer_url else ""
    self.body.append(f'<div class="wokwi-panel" id="{pid}" role="tabpanel" data-active="{active}"{data_attr}>')


def depart_tabpanel_html(self, node: TabPanelNode):
    self.body.append("</div>")


# --- Text / LaTeX fallbacks (unchanged) ---

def _fallback_text(viewer_url: str) -> str:
    return f"Wokwi simulation: {viewer_url}"


def visit_wokwi_text(self, node: WokwiNode):
    viewer_url = iframe_url(node.get("iframe_page"), node.get("diagram"), node.get("firmware"))
    self.add_text(_fallback_text(viewer_url))
    raise _n.SkipNode


def depart_wokwi_text(self, node: WokwiNode):
    pass


def visit_wokwi_tabs_text(self, node: WokwiTabsNode):
    self.add_text("Tabs:\n")


def depart_wokwi_tabs_text(self, node: WokwiTabsNode):
    pass


def visit_tablist_text(self, node: TabListNode):
    labels = node.get("labels", [])
    for i, lbl in enumerate(labels, 1):
        self.add_text(f"  {i}. {lbl}\n")
    raise _n.SkipNode


def depart_tablist_text(self, node: TabListNode):
    pass


def visit_tabpanel_text(self, node: TabPanelNode):
    label = node.get("label") or "Tab"
    self.add_text(f"\n[{label}]\n")


def depart_tabpanel_text(self, node: TabPanelNode):
    self.add_text("\n")


def visit_wokwi_latex(self, node: WokwiNode):
    viewer_url = iframe_url(node.get("iframe_page"), node.get("diagram"), node.get("firmware"))
    self.body.append(r"\url{" + viewer_url + "}")
    raise _n.SkipNode


def depart_wokwi_latex(self, node: WokwiNode):
    pass


def visit_wokwi_tabs_latex(self, node: WokwiTabsNode):
    self.body.append("\\par\\medskip{}\n")


def depart_wokwi_tabs_latex(self, node: WokwiTabsNode):
    self.body.append("\\par\\medskip{}\n")


def visit_tablist_latex(self, node: TabListNode):
    labels = node.get("labels", [])
    if labels:
        self.body.append("\\textbf{Tabs:} " + ", ".join(labels) + "\\\\\n")
    raise _n.SkipNode


def depart_tablist_latex(self, node: TabListNode):
    pass


def visit_tabpanel_latex(self, node: TabPanelNode):
    label = node.get("label") or "Tab"
    self.body.append("\\textbf{" + label + "}: ")


def depart_tabpanel_latex(self, node: TabPanelNode):
    self.body.append("\\par\n")
