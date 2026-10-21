import pytest

from app.music import (
    atmosphere, cached_emotion, current_mood, emotion_for, emotion_strength,
    influence_level, record_play, remember_emotion, set_influence, set_influence_level,
)
from app.store import Store


def play(store, valence=0.4, energy=0.45, ident="synthetic"):
    track = {"id": ident, "source": "netease", "name": "合成测试音乐"}
    remember_emotion(store, track, {"valence": valence, "energy": energy, "label": "喜", "moods": ["温柔"]})
    record_play(store, track)
    return track


@pytest.mark.parametrize("valence,energy,expected", [(0, .45, 0), (.5, .45, .5), (-.8, .45, .8), (0, 1, 1), (1, 1, 1)])
def test_song_strength_depends_only_on_song_coordinates(valence, energy, expected):
    assert emotion_strength(valence, energy) == expected


def test_four_levels_change_xinxin_but_not_the_song(tmp_path):
    store = Store(tmp_path)
    track = play(store)
    feelings = []
    for level, multiplier in enumerate([0.4, 1.0, 1.5, 2.2], 1):
        set_influence_level(store, level)
        mood = current_mood(store)
        assert mood["music_intensity"] == .4
        assert cached_emotion(store, track)["intensity"] == .4
        assert mood["feeling"]["multiplier"] == multiplier
        assert mood["feeling"]["intensity"] == pytest.approx(.4 * multiplier, abs=.001)
        feelings.append(mood["feeling"]["intensity"])
    assert feelings == sorted(set(feelings))


def test_more_plays_do_not_artificially_strengthen_same_music(tmp_path):
    store = Store(tmp_path)
    play(store)
    before = current_mood(store)
    for _ in range(15):
        play(store)
    after = current_mood(store)
    assert after["music_intensity"] == before["music_intensity"]
    assert after["feeling"]["intensity"] == before["feeling"]["intensity"]


def test_time_decay_changes_feeling_without_rescoring_music(tmp_path):
    store = Store(tmp_path)
    play(store)
    store.execute("UPDATE music_plays SET created=created-90*60")
    mood = current_mood(store)
    assert mood["music_intensity"] == .4
    assert mood["freshness"] == pytest.approx(.5, abs=.001)
    assert mood["feeling"]["intensity"] == pytest.approx(.2, abs=.001)


def test_disabled_feeling_is_zero_and_keeps_song_and_preference(tmp_path):
    store = Store(tmp_path)
    play(store)
    set_influence_level(store, 4)
    set_influence(store, False)
    mood = current_mood(store)
    assert mood["music_intensity"] == .4
    assert mood["sensitivity_level"] == 4
    assert mood["feeling"]["intensity"] == 0
    assert atmosphere(store) == ("", None)
    set_influence(store, True)
    assert current_mood(store)["feeling"]["intensity"] == pytest.approx(.88, abs=.001)


def test_legacy_setting_migrates_on_first_save(tmp_path):
    store = Store(tmp_path)
    store.set_setting("music_influence_level", 3)
    assert influence_level(store) == 3
    set_influence_level(store, 4)
    assert store.setting("music_sensitivity_level") == store.setting("music_influence_level") == 4


def test_weak_music_does_not_produce_strong_reaction_even_at_high_sensitivity(tmp_path):
    store = Store(tmp_path)
    play(store, .02)
    set_influence_level(store, 4)
    assert current_mood(store)["feeling"]["intensity"] < .05
    assert atmosphere(store) == ("", None)


def test_prompt_uses_xinxins_actual_feeling_and_keeps_task_accuracy(tmp_path):
    store = Store(tmp_path)
    play(store, .35)
    set_influence_level(store, 1)
    note, data = atmosphere(store)
    assert "克制" in note and "你实际感受到「平静」" in note
    assert "歌曲/氛围自身情绪强度" in note and "解题准确性" in note
    assert data["xinxin_feeling"]["intensity"] == pytest.approx(.14, abs=.001)


def test_unknown_song_has_zero_strength(tmp_path):
    assert emotion_for("synthetic-unknown-title")["intensity"] == 0
    store = Store(tmp_path)
    record_play(store, {"id": "unknown", "name": "synthetic-unknown-title"})
    assert current_mood(store)["feeling"]["intensity"] == 0
