"""One renderer for both platform exports and standalone reproduction scripts."""


def render_figure(frame, recipe, cancelled=None):
    import io
    import pandas as pd
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt, font_manager

    def check():
        if cancelled and cancelled.is_set():
            raise RuntimeError("绘图已取消")

    check()
    x, y, kind, color = (recipe[key] for key in ("x", "y", "kind", "color"))
    if x not in frame.columns or y not in frame.columns:
        raise ValueError("所选列不存在")
    if kind not in {"line", "bar", "scatter", "hist"}:
        raise ValueError("不支持的图表类型")
    if kind == "bar" and len(frame) > 200:
        raise ValueError("柱状图最多绘制 200 行，请先汇总或筛选数据")
    available = {font.name for font in font_manager.fontManager.ttflist}
    font = next(
        (
            name
            for name in (
                "Microsoft YaHei",
                "Noto Sans CJK SC",
                "WenQuanYi Zen Hei",
                "SimHei",
            )
            if name in available
        ),
        "DejaVu Sans",
    )
    style = {
        "font.family": font,
        "axes.unicode_minus": False,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.facecolor": "#faf8f3",
        "axes.facecolor": "#faf8f3",
        "axes.edgecolor": "#d8d5cd",
        "axes.labelcolor": "#373c3a",
        "text.color": "#373c3a",
    }
    with plt.rc_context(style):
        fig, ax = plt.subplots(figsize=(9, 5.5), layout="constrained")
        try:
            values = pd.to_numeric(frame[y], errors="coerce")
            keep = values.notna()
            if not keep.any():
                raise ValueError("Y 列没有可绘制的数值")
            a, b = frame.loc[keep, x], values[keep]
            if kind == "line":
                ax.plot(a, b, color=color, linewidth=2)
            elif kind == "bar":
                ax.bar(a.astype(str), b, color=color, width=0.65)
            elif kind == "scatter":
                ax.scatter(a, b, color=color, s=30, alpha=0.7, edgecolors="none")
            else:
                ax.hist(b, bins="auto", color=color, alpha=0.85)
            ax.set_title(recipe["title"][:100], loc="left", fontsize=18, pad=24)
            ax.set_xlabel(x if kind != "hist" else y)
            ax.set_ylabel(y if kind != "hist" else "Count")
            ax.grid(axis="y", color="#dedbd3", linewidth=0.6, alpha=0.65)
            ax.set_axisbelow(True)
            result = {"rows": int(keep.sum())}
            for ext in ("png", "pdf"):
                check()
                stream = io.BytesIO()
                fig.savefig(stream, format=ext, dpi=250)
                check()
                result[ext] = stream.getvalue()
            return result
        finally:
            plt.close(fig)
