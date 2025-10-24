import os
import math

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

pio.kaleido.scope.mathjax = None

import networkx as nx
from pyvis.network import Network
import seaborn as sns
from d3blocks import D3Blocks

from tlparser.config import Configuration
from tlparser.utils import Utils


class Viz:
    title_map = {
        "stats.agg.aps": ["Atomic Propositions (APs)", "Count"],
        "stats.agg.cops": ["Comparison Operators (COPs)", "Count"],
        "stats.agg.lops": ["Logical Operators (LOPs)", "Count"],
        "stats.agg.tops": ["Temporal Operators (TOPs)", "Count"],
        "stats.asth": ["Abstract Syntrax Tree Height (ASTH)", "Height"],
        "stats.entropy.lops_tops": ["Entropy (LOPs & TOPs)", "Entropy (base 2)"],
        "stats.req_len": ["Requirement Text Length", "Character Count"],
        "stats.req_sentence_count": ["Requirement Sentences", "Sentence Count"],
        "stats.req_word_count": ["Requirement Words", "Word Count"],
    }
    translatability = ["yes", "no", "depends"]

    def __init__(self, config: Configuration, file, selfonly=False):
        self.config = config
        self.data = pd.read_excel(file)
        if selfonly:
            selftypes = self.data[self.data["translation"] == "self"]["type"].unique()
            self.data = self.data[self.data["type"].isin(selftypes)]

    def __get_file_name(self, prefix, suffix=".pdf"):
        os.makedirs(self.config.folder_data_out, exist_ok=True)
        return os.path.join(
            self.config.folder_data_out,
            f"{prefix}_{Utils.get_unique_filename()}{suffix}",
        )

    def __get_reduced_logic_order(self):
        return [
            item
            for item in self.config.logic_order
            if item in self.data["type"].unique()
        ]

    def plot_histogram(self):
        reduced_order = self.__get_reduced_logic_order()
        type_palette = self.config.color_palette
        df = self.data.copy()
        df["type"] = pd.Categorical(df["type"], categories=reduced_order, ordered=True)
        _, axes = plt.subplots(2, 2, figsize=(7, 4), sharex=True, sharey=True)
        axes = axes.flatten()
        titles = {
            "self": {"title": "(a) Natural Formalization", "var": "n"},
            "yes": {"title": "(b) Possible", "var": "t_1"},
            "no": {"title": "(c) Not Possible", "var": "t_2"},
            "depends": {"title": "(d) Conditional", "var": "t_3"},
        }
        max_count = df["type"].value_counts().max() + 5
        translations_ordered = sorted(
            df["translation"].unique(), key=lambda x: list(titles.keys()).index(x)
        )

        for ax, translation in zip(axes, translations_ordered):
            sns.histplot(
                data=df[df["translation"] == translation],
                x="type",
                ax=ax,
                shrink=0.8,
                discrete=True,
                hue="type",
                multiple="stack",
                palette=type_palette,
                legend=False,
            )
            n = df[df["translation"] == translation].shape[0]
            title_info = titles.get(
                translation, {"title": f"Translatable: {translation}", "var": ""}
            )
            ax.set_title(f"{title_info['title']} (${title_info['var']}={n}$)")
            ax.set_xlabel("")
            ax.set_ylabel("Count")
            ax.set_ylim(0, max_count)
            major_locs = ax.yaxis.get_majorticklocs()
            if len(major_locs) > 1:
                major_interval = major_locs[1] - major_locs[0]
                minor_tick_interval = major_interval / 5
                ax.yaxis.set_minor_locator(ticker.MultipleLocator(minor_tick_interval))

            for bar in ax.patches:
                height = bar.get_height()
                if height > 0:
                    y = height / 2 if height > 14 else height + 8
                    ax.annotate(
                        f"{int(height)}",
                        xy=(bar.get_x() + bar.get_width() / 2, y),
                        xytext=(0, 0),
                        textcoords="offset points",
                        ha="center",
                        va="center",
                        fontsize=8,
                        color="black",
                        bbox=dict(
                            boxstyle="round,pad=0.2",
                            facecolor="white",
                            edgecolor="black",
                        ),
                    )

        plt.tight_layout()
        out = self.__get_file_name("hist")
        plt.savefig(out)
        plt.close()
        return out

    def _plot_violin(
        self,
        df_long,
        stats_values,
        metrics,
        title_map,
        out_prefix,
        include_strip=False,
        palette_index=0,
    ):
        type_palette = self.config.color_palette
        # Build a palette for the present types, optionally rotated by palette_index.
        present_types = list(df_long["type"].unique())
        ordered_present_types = [
            t for t in self.__get_reduced_logic_order() if t in present_types
        ] or present_types

        plot_palette = Utils.rotate_palette_map(
            type_palette, ordered_present_types, index=palette_index
        )

        # Special case: if only one type is present, allow selecting a different
        # color by index across the full configured palette, so different
        # violin plots can visually alternate even for the same type.
        if (
            len(ordered_present_types) == 1
            and isinstance(type_palette, dict)
            and isinstance(palette_index, int)
        ):
            only_type = ordered_present_types[0]
            full_order = self.config.logic_order or list(type_palette.keys())
            if not full_order:
                full_colors = list(type_palette.values())
            else:
                full_colors = [type_palette.get(t, "#808080") for t in full_order]
            if len(full_colors) > 0:
                idx = palette_index % len(full_colors)
                plot_palette = {only_type: full_colors[idx]}

        number_of_types = df_long["type"].unique().size

        if len(metrics) == 3:
            # Create a layout with the third plot centered by spanning both columns
            fig = plt.figure(figsize=(8, 8))
            gs = fig.add_gridspec(nrows=2, ncols=2)
            axes_list = [
                fig.add_subplot(gs[0, 0]),
                fig.add_subplot(gs[0, 1]),
                fig.add_subplot(gs[1, :]),
            ]
            fig.subplots_adjust(hspace=0.05, wspace=0.05)
        else:
            fig, axes = plt.subplots(
                nrows=3 if len(metrics) > 3 else 2,
                ncols=2,
                figsize=(8, 11) if len(metrics) > 3 else (8, 7),
                sharex=False,
                sharey=False,
            )
            axes_list = axes.flatten().tolist()
            plt.subplots_adjust(hspace=0.05, wspace=0.05)
        i = 1

        for ax, agg in zip(axes_list, metrics):
            y_max = df_long[df_long["aggregation"] == agg]["value"].max() * 1.8
            violin = sns.violinplot(
                x="type",
                y="value",
                data=df_long[df_long["aggregation"] == agg],
                hue="type",
                palette=plot_palette,
                bw_method=0.5,
                edgecolor="black",
                linewidth=1,
                linecolor="k",
                ax=ax,
                inner=None,
                legend=False,
            )
            sns.boxplot(
                x="type",
                y="value",
                hue="type",
                palette=plot_palette,
                data=df_long[df_long["aggregation"] == agg],
                width=0.12,
                showcaps=True,
                showbox=True,
                whiskerprops={"linewidth": 1.2, "color": "black"},
                medianprops={"linewidth": 1.2, "color": "black"},
                ax=ax,
                fliersize=5,
            )

            for violin_part in violin.collections:
                violin_part.set_alpha(0.6)

            if include_strip:
                sns.stripplot(
                    x="type",
                    y="value",
                    hue="type",
                    data=df_long[df_long["aggregation"] == agg],
                    alpha=0.3,
                    palette=plot_palette,
                    size=3,
                    marker="d",
                    edgecolor="black",
                    linewidth=1,
                    ax=ax,
                    dodge=False,
                )

            ax.set_xlabel("")
            ax.yaxis.set_minor_locator(ticker.MultipleLocator(1))

            x_shift = 1 / number_of_types / 2
            for _, row in stats_values[stats_values["aggregation"] == agg].iterrows():
                annotation_text = (
                    f"$\mu={row['mean']:.1f}$\n"
                    f"$M={row['median']:.1f}$\n"
                    f"$\sigma={row['std']:.1f}$"
                )
                ax.text(
                    x_shift,
                    0.83,
                    annotation_text,
                    color="black",
                    ha="center",
                    va="bottom",
                    transform=ax.transAxes,
                )
                x_shift += 1 / number_of_types

            if i > 0:  # increase to print 'n=...' more sparsly
                for x_category in df_long["type"].unique():
                    filtered_values = stats_values.loc[
                        (stats_values["aggregation"] == agg)
                        & (stats_values["type"] == x_category),
                        "count",
                    ]
                    n_value = (
                        int(filtered_values.iloc[0]) if not filtered_values.empty else 0
                    )
                    x_position = list(df_long["type"].unique()).index(x_category)
                    ax.text(
                        x_position,
                        -0.18 * y_max,
                        f"$n={n_value}$",
                        color="black",
                        ha="center",
                        va="top",
                    )

            i += 1
            ax.set_title(title_map.get(agg, agg)[0])
            ax.set_ylabel(title_map.get(agg, agg)[1])
            ax.set_ylim(-0.09 * y_max, y_max)
            major_locs = ax.yaxis.get_majorticklocs()
            if len(major_locs) > 1:
                major_interval = major_locs[1] - major_locs[0]
                minor_tick_interval = major_interval / 5
                ax.yaxis.set_minor_locator(ticker.MultipleLocator(minor_tick_interval))

        for j in range(len(metrics), len(axes_list)):
            axes_list[j].set_visible(False)

        fig.tight_layout()
        # If exactly 3 metrics, keep the third axis centered without stretching.
        if len(metrics) == 3:
            ref = axes_list[0].get_position()
            bottom = axes_list[2].get_position()
            w = ref.width
            h = ref.height
            x = 0.5 - w / 2
            axes_list[2].set_position([x, bottom.y0, w, h])
        out = self.__get_file_name(out_prefix)
        plt.savefig(out)
        plt.close()
        return out

    def plot_violin_engcompl(self, include_strip=False, palette_index=0):
        df_filtered = self.data[self.data["translation"] == "self"]
        metrics = df_filtered.filter(like=".agg.").columns.tolist()
        metrics = metrics + ["stats.asth", "stats.entropy.lops_tops"]
        df_long = pd.melt(
            df_filtered,
            id_vars=["id", "type"],
            value_vars=metrics,
            var_name="aggregation",
            value_name="value",
        )

        stats_values = (
            df_long.groupby(["type", "aggregation"])["value"]
            .agg(["mean", "median", "count", "std"])
            .reset_index()
        )
        return self._plot_violin(
            df_long,
            stats_values,
            metrics,
            self.title_map,
            "viol_engcompl",
            include_strip,
            palette_index,
        )

    def plot_violin_reqtext(self, include_strip=False, palette_index=0):
        df_filtered = self.data[self.data["translation"] == "self"]
        # metrics = df_filtered.filter(like=".req_").columns.tolist()
        metrics = ["stats.req_word_count", "stats.req_sentence_count"]
        df_long = pd.melt(
            df_filtered,
            id_vars=["id", "type"],
            value_vars=metrics,
            var_name="aggregation",
            value_name="value",
        )

        stats_values = (
            df_long.groupby(["type", "aggregation"])["value"]
            .agg(["mean", "median", "count", "std"])
            .reset_index()
        )
        return self._plot_violin(
            df_long,
            stats_values,
            metrics,
            self.title_map,
            "viol_req",
            include_strip,
            palette_index,
        )

    def plot_pairplot(self, include_trend: bool = False):
        type_palette = self.config.color_palette
        df = self.data[self.data["translation"] == "self"]
        metrics = df.filter(like=".agg.").columns.tolist()
        df_pairplot = df[metrics + ["type", "stats.asth", "stats.entropy.lops_tops"]]
        req_metrics = df.filter(like=".req_").columns.tolist()
        if req_metrics:
            df_pairplot = pd.concat([df_pairplot, df[req_metrics]], axis=1)

        unique_types = df_pairplot["type"].nunique()
        markers = ["o", "s", "D", "^", "v", "P"][:unique_types]

        g = sns.pairplot(
            df_pairplot,
            hue="type",
            palette=type_palette,
            diag_kind="kde",
            markers=markers,
        )

        for i, ax in enumerate(g.axes.flat):
            row_var = g.x_vars[i % len(g.x_vars)]
            col_var = g.y_vars[i // len(g.x_vars)]
            ax.set_xlabel(self.title_map.get(row_var, row_var)[0])
            ax.set_ylabel(self.title_map.get(col_var, col_var)[0])
            for artist in ax.collections:
                artist.set_edgecolor("black")
                artist.set_alpha(0.6)

        if include_trend:
            # Overlay a single overall linear trend per subplot (off-diagonal only)
            for r, row in enumerate(g.axes):
                for c, ax in enumerate(row):
                    xvar = g.x_vars[c]
                    yvar = g.y_vars[r]
                    if xvar == yvar:
                        continue
                    if df_pairplot[xvar].nunique() <= 1:
                        continue
                    sns.regplot(
                        data=df_pairplot,
                        x=xvar,
                        y=yvar,
                        scatter=False,
                        ax=ax,
                        color="black",
                        line_kws={"linewidth": 1.2, "alpha": 0.8, "zorder": 5},
                    )
                    # Restore pretty labels (regplot resets them)
                    ax.set_xlabel(self.title_map.get(xvar, [xvar, ""])[0])
                    ax.set_ylabel(self.title_map.get(yvar, [yvar, ""])[0])

        g._legend.set_title("")
        out = self.__get_file_name("pairp")
        plt.savefig(out)
        plt.close()
        return out

    def plot_pairplot_reqwords(self, include_trend: bool = False):
        # Scatter grids with Requirement Words on the Y-axis for selected X metrics
        df = self.data[self.data["translation"] == "self"].copy()

        x_metrics = [
            "stats.agg.aps",
            "stats.agg.cops",
            "stats.agg.lops",
            "stats.agg.tops",
            "stats.asth",
            "stats.entropy.lops_tops",
            "stats.req_sentence_count",
            "stats.req_len",
        ]
        y_metric = "stats.req_word_count"

        available = [m for m in x_metrics if m in df.columns]
        if y_metric not in df.columns or not available:
            # Nothing to plot
            return ""

        # Build figure 3x3
        fig, axes = plt.subplots(
            nrows=3, ncols=3, figsize=(8, 7), sharey=True, sharex=False
        )
        axes = axes.flatten()
        base_color = "#ffaf2d"

        for ax, x in zip(axes, available):
            ax.scatter(
                df[x],
                df[y_metric],
                s=28,
                c=base_color,
                alpha=0.55,
                edgecolors="black",
                linewidths=0.5,
            )
            x_label = self.title_map.get(x, [x, ""])[0]
            y_label = "Requirement Words"
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)

            if include_trend and df[x].nunique() > 1:
                sns.regplot(
                    data=df,
                    x=x,
                    y=y_metric,
                    scatter=False,
                    ax=ax,
                    color="black",
                    line_kws={"linewidth": 1.2, "alpha": 0.8, "zorder": 5},
                )
                # Restore labels after regplot overlay
                ax.set_xlabel(x_label)
                ax.set_ylabel(y_label)

        # Hide any unused axes (if fewer than 9 x metrics are available)
        for j in range(len(available), len(axes)):
            axes[j].set_visible(False)

        fig.tight_layout()
        # Center items in the last row without stretching when not all columns are used
        n = len(available)
        if n > 0 and n % 3 != 0:
            r = n % 3  # 1 or 2 items in the last row
            last_row_start = (n // 3) * 3
            # Reference positions for the three columns in the last row
            left_pos = axes[last_row_start].get_position()
            mid_pos = axes[last_row_start + 1].get_position()
            right_pos = axes[last_row_start + 2].get_position()

            if r == 1:
                # Move the single plot to the middle column
                axes[last_row_start].set_position(
                    [mid_pos.x0, mid_pos.y0, mid_pos.width, mid_pos.height]
                )
            elif r == 2:
                # Place the two plots adjacent and centered as a group.
                W = left_pos.width
                # spacing between adjacent columns (gap between left and middle)
                S = mid_pos.x0 - (left_pos.x0 + left_pos.width)
                total = 2 * W + S
                left_x = 0.5 - total / 2
                axes[last_row_start].set_position(
                    [left_x, left_pos.y0, W, left_pos.height]
                )
                axes[last_row_start + 1].set_position(
                    [left_x + W + S, left_pos.y0, W, left_pos.height]
                )
        out = self.__get_file_name("pair_reqw")
        plt.savefig(out)
        plt.close()
        return out

    def plot_sankey(self):
        df = self.data.copy()
        flow_counts = {"yes": {}, "no": {}, "depends": {}}
        for id_value, group in df.groupby("id"):
            source_type = group[group["translation"] == "self"]["type"].values[0]
            for _, row in group.iterrows():
                target_type = row["type"]
                translation_type = row["translation"]
                if translation_type in self.translatability:
                    if (source_type, target_type) not in flow_counts[translation_type]:
                        flow_counts[translation_type][
                            (source_type, target_type)
                        ] = set()
                    flow_counts[translation_type][(source_type, target_type)].add(
                        id_value
                    )

        labels = df["type"].unique().tolist()
        source = []
        target = []
        value = []
        link_labels = []
        link_colors = []

        translation_colors = {
            "yes": "rgba(0, 128, 0, 0.7)",
            "no": "rgba(255, 0, 0, 0.7)",
            "depends": "rgba(128, 128, 128, 0.7)",
        }

        label_to_index = {label: idx for idx, label in enumerate(labels)}
        for translation_type, flows in flow_counts.items():
            for (src, tgt), ids_set in flows.items():
                source.append(label_to_index[src])
                target.append(label_to_index[tgt])
                value.append(len(ids_set))
                link_labels.append(f"{len(ids_set)} ids ({translation_type})")
                link_colors.append(translation_colors[translation_type])

        fig = go.Figure(
            data=[
                go.Sankey(
                    arrangement="freeform",
                    node=dict(
                        pad=15,
                        thickness=20,
                        line=dict(color="black", width=0.5),
                        label=labels,
                    ),
                    link=dict(
                        arrowlen=15,
                        source=source,
                        target=target,
                        value=value,
                        label=link_labels,
                        color=link_colors,
                    ),
                )
            ]
        )

        fig.update_layout(
            title_text="Sankey Diagram of Translations",
            font_size=10,
        )
        out = self.__get_file_name("sankey")
        pio.write_image(fig, out, format="pdf")
        return out

    def plot_chord(self):
        outs = []
        for target in self.translatability:
            df = self.data.copy()
            d3 = D3Blocks(chart="chord", frame=True, verbose=50)
            links = []

            for _, group in df.groupby("id"):
                source_type_row = group[group["translation"] == "self"]
                if not source_type_row.empty:
                    source_type = source_type_row["type"].values[0]
                    yes_targets = group[
                        (group["translation"] == target)
                        & (group["type"] != source_type)
                    ]
                    for _, row in yes_targets.iterrows():
                        target_type = row["type"]
                        links.append(
                            {
                                "source": source_type,
                                "target": target_type,
                                "weight": 1,
                                "color": self.config.color_palette.get(source_type),
                            }
                        )
            if len(links) > 0:
                links_df = pd.DataFrame(links)
                links_df = (
                    links_df.groupby(["source", "target"])
                    .size()
                    .reset_index(name="weight")
                )

                d3.chord(
                    links_df,
                    ordering=self.__get_reduced_logic_order(),
                    reset_properties=False,
                )

                for label, color in self.config.color_palette.items():
                    if label in d3.node_properties.index:
                        d3.node_properties.loc[label, "color"] = color

                out = self.__get_file_name(f"chord_{target}", ".html")
                d3.chord(
                    links_df,
                    title=f"Chord Diagram (self -> {target})",
                    save_button=True,
                    filepath=out,
                    ordering=self.__get_reduced_logic_order(),
                    figsize=(550, 550),
                    reset_properties=False,
                    arrowhead=38,
                    fontsize=13,
                )
                outs.append(out)

        return "\n".join(outs)

    def plot_dag_interactive(self):
        outs = []
        for target in self.translatability:
            df = self.data.copy()
            G = nx.DiGraph()

            # constructing the directed graph
            for _, group in df.groupby("id"):
                source_type_row = group[group["translation"] == "self"]
                if not source_type_row.empty:
                    source_type = source_type_row["type"].values[0]
                    yes_targets = group[
                        (group["translation"] == target)
                        & (group["type"] != source_type)
                    ]
                    for _, row in yes_targets.iterrows():
                        target_type = row["type"]
                        if G.has_edge(source_type, target_type):
                            G[source_type][target_type]["weight"] += 1
                        else:
                            G.add_edge(
                                source_type,
                                target_type,
                                weight=1,
                                color=Utils.lighten_color(
                                    hex_color=self.config.color_palette.get(
                                        source_type, "black"
                                    ),
                                    opacity=0.8,
                                ),
                            )

            if G.number_of_edges() > 0:
                # using PyVis for interactive plotting
                net = Network(
                    notebook=True,
                    directed=True,
                    height="600px",
                    width="100%",
                    cdn_resources="in_line",
                )
                net.from_nx(G)
                net.show_buttons(filter_=["physics"])

                for node in net.nodes:
                    node["color"] = Utils.lighten_color(
                        hex_color=self.config.color_palette.get(node["label"], "black"),
                        opacity=0.8,
                    )
                    # node['opacity'] = 0.6
                    node["font"] = {"color": "black", "size": 28}
                    node["borderWidth"] = 2
                    node["shape"] = "box"

                for edge in net.edges:
                    weight = G[edge["from"]][edge["to"]].get("width", 1)
                    color = G[edge["from"]][edge["to"]].get("color", "black")
                    edge["value"] = math.log10(weight)
                    edge["title"] = f"Weight: {weight}"
                    edge["arrowStrikethrough"] = True
                    edge["color"] = color
                    edge["label"] = str(weight)
                    edge["font"] = {
                        "color": "black",
                        "size": 10,
                        "background": "rgba(255, 255, 255, 0)",
                        "strokeWidth": 0,
                    }
                    edge["arrows"] = {"to": {"enabled": True, "scaleFactor": 1.5}}

                net.set_edge_smooth("dynamic")
                net.repulsion(
                    node_distance=100,
                    central_gravity=0.05,
                    spring_length=80,
                    spring_strength=0.005,
                )

                # save as HTML
                out = self.__get_file_name(f"dag_{target}", ".html")
                net.show(out)
                outs.append(out)

        return outs

    def plot_operator_bars(self):
        # Summarize operator counts across self translations and plot three bar charts side-by-side
        df = self.data[self.data["translation"] == "self"].copy()

        groups = [
            (
                "(a) Temporal",
                {
                    "F": "stats.tops.F",
                    "G": "stats.tops.G",
                    "U": "stats.tops.U",
                    "X": "stats.tops.X",
                },
            ),
            (
                "(b) Logical",
                {
                    "and": "stats.lops.and",
                    "implies": "stats.lops.impl",
                    "not": "stats.lops.not",
                    "or": "stats.lops.or",
                },
            ),
            (
                "(c) Comparison",
                {
                    "eq": "stats.cops.eq",
                    "geq": "stats.cops.geq",
                    "gt": "stats.cops.gt",
                    "leq": "stats.cops.leq",
                    "lt": "stats.cops.lt",
                    "neq": "stats.cops.neq",
                },
            ),
        ]

        # Compute data and width ratios first so we can size columns proportionally
        bar_groups = []  # list of (title, labels, values)
        width_ratios = []
        for title, mapping in groups:
            labels = []
            values = []
            cols = [col for col in mapping.values() if col in df.columns]
            if cols:
                sums = df[cols].sum()
                for label, col in mapping.items():
                    if col in sums.index:
                        labels.append(label)
                        values.append(int(sums[col]))
            if not labels:
                labels, values = ["n/a"], [0]
            bar_groups.append((title, labels, values))
            width_ratios.append(max(len(labels), 1))

        fig, axes = plt.subplots(
            1,
            3,
            figsize=(9, 3.5),
            sharey=False,
            gridspec_kw={"width_ratios": width_ratios},
        )
        axes = axes.flatten()

        palette = sns.color_palette("tab10")
        alpha = 0.85  # add a bit of transparency to bar faces

        for ax, (title, labels, values) in zip(axes, bar_groups):
            base_colors = palette[: len(labels)]
            bar_colors = [(r, g, b, alpha) for (r, g, b) in base_colors]
            bars = ax.bar(labels, values, color=bar_colors, edgecolor="black")
            ax.set_title(title)
            ax.set_ylabel("Count")
            ax.set_ylim(0, max(values) * 1.15 + 1)

            for rect, val in zip(bars, values):
                ax.annotate(
                    str(val),
                    xy=(rect.get_x() + rect.get_width() / 2, rect.get_height()),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                )

        fig.tight_layout()
        out = self.__get_file_name("ops_bars")
        plt.savefig(out)
        plt.close()
        return out
