import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.state import (  # noqa: E402
    ResearchResult,
    Scene,
    Script,
    Statistic,
    Storyboard,
)


def make_scene(index, layout, **fields):

    values = dict(
        index=index,
        layout=layout,
        narration=f"Narration for scene {index} with a few spoken words.",
        headline=f"Headline for scene {index}",
        stat_value="",
        bullets=[],
        chart_labels=[],
        chart_values=[],
        chart_unit="",
        source="",
    )
    values.update(fields)

    return Scene(**values)


@pytest.fixture
def storyboard():

    return Storyboard(
        color_theme="navy",
        scenes=[
            make_scene(1, "title", headline="India's jobs paradox explained"),
            make_scene(2, "stat", stat_value="3.2%", headline="Unemployment rate in 2023-24"),
            make_scene(3, "bullets", bullets=["Gig work is growing", "Wages are flat", "Women joining workforce"]),
            make_scene(4, "bar_chart", chart_labels=["Agriculture", "Services", "Industry"], chart_values=[46.1, 29.7, 24.2], chart_unit="%", source="PLFS 2023-24"),
            make_scene(5, "quote", headline="Jobs are growing, but good jobs are not"),
            make_scene(6, "outro", headline="The future of work is being decided now"),
        ],
    )


@pytest.fixture
def research():

    return ResearchResult(
        summary="Summary",
        facts=["Fact one"],
        statistics=[Statistic(label="Unemployment", value="3.2%", source="PLFS 2023-24")],
        caveats=["Caveat"],
        sources=["PLFS"],
    )


@pytest.fixture
def script():

    return Script(
        title="Jobs",
        hook="India's unemployment rate has nearly halved.",
        body=["So why is finding a good job still so hard?"],
        ending="Follow for more.",
    )
